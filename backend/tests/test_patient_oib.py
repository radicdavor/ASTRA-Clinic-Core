from datetime import datetime, timedelta, timezone

from app.models.domain import AuditLog, Clinic, Patient, PatientClinicAssociation
from tests.conftest import login_token


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def associate_with_test_clinic(db, auth_setup, patient):
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=auth_setup["clinic"].id, created_by_user_id=auth_setup["admin"].id))
    db.commit()


def test_create_patient_without_oib_succeeds(client, auth_setup):
    response = client.post(
        "/api/patients",
        headers=auth_headers(client),
        json={"first_name": "Bez", "last_name": "Oiba"},
    )

    assert response.status_code == 200
    assert response.json()["oib"] is None


def test_create_patient_with_valid_oib_succeeds_and_is_returned(client, auth_setup):
    response = client.post(
        "/api/patients",
        headers=auth_headers(client),
        json={"first_name": "Oib", "last_name": "Valjan", "oib": "12345678901"},
    )

    assert response.status_code == 200
    assert response.json()["oib"] == "12345678901"


def test_invalid_oib_is_rejected(client, auth_setup):
    response = client.post(
        "/api/patients",
        headers=auth_headers(client),
        json={"first_name": "Oib", "last_name": "Los", "oib": "ABC"},
    )

    assert response.status_code == 422


def test_duplicate_oib_is_rejected(client, auth_setup):
    headers = auth_headers(client)
    first = client.post("/api/patients", headers=headers, json={"first_name": "Prvi", "last_name": "Pacijent", "oib": "22222222222"})
    second = client.post("/api/patients", headers=headers, json={"first_name": "Drugi", "last_name": "Pacijent", "oib": "22222222222"})

    assert first.status_code == 200
    assert second.status_code == 409


def test_patient_search_includes_oib(client, auth_setup, sql_query_counter):
    headers = auth_headers(client)
    client.post("/api/patients", headers=headers, json={"first_name": "Search", "last_name": "Oib", "oib": "33333333333"})

    with sql_query_counter.track() as query_count:
        response = client.get("/api/patients?q=33333333333", headers=headers)

    assert response.status_code == 200
    assert [patient["oib"] for patient in response.json()] == ["33333333333"]
    assert query_count.count <= 8


def test_patient_directory_is_bounded_and_stably_ordered(client, db, auth_setup):
    db.add_all(
        Patient(first_name=f"Ime {index:03d}", last_name="Ograniceni", phone=str(index))
        for index in range(75)
    )
    db.commit()

    response = client.get("/api/patients?q=Ograniceni", headers=auth_headers(client))

    assert response.status_code == 200
    assert len(response.json()) == 50
    assert [item["first_name"] for item in response.json()[:3]] == ["Ime 000", "Ime 001", "Ime 002"]
    assert client.get("/api/patients?limit=51", headers=auth_headers(client)).status_code == 422


def test_global_patient_identity_reads_never_expose_cross_clinic_free_text_notes(client, db, auth_setup):
    foreign_clinic = Clinic(name="Foreign identity clinic")
    foreign_patient = Patient(
        first_name="Foreign",
        last_name="Identity",
        phone="099000111",
        notes="CROSS_CLINIC_FREE_TEXT_SENTINEL",
    )
    db.add_all([foreign_clinic, foreign_patient])
    db.flush()
    db.add(PatientClinicAssociation(patient_id=foreign_patient.id, clinic_id=foreign_clinic.id, active=True))
    db.commit()
    headers = auth_headers(client)

    directory = client.get("/api/patients?q=Foreign", headers=headers)
    detail = client.get(f"/api/patients/{foreign_patient.id}", headers=headers)
    duplicates = client.get(
        "/api/patients/possible-duplicates?first_name=Foreign&last_name=Identity",
        headers=headers,
    )

    assert directory.status_code == detail.status_code == duplicates.status_code == 200
    assert "notes" not in directory.json()[0]
    assert "notes" not in detail.json()
    assert "notes" not in duplicates.json()[0]
    assert "CROSS_CLINIC_FREE_TEXT_SENTINEL" not in directory.text + detail.text + duplicates.text


def test_possible_duplicates_returns_identity_candidates(client, auth_setup):
    headers = auth_headers(client)
    client.post(
        "/api/patients",
        headers=headers,
        json={"first_name": "Ana", "last_name": "Horvat", "date_of_birth": "1990-01-01", "phone": "+385 91 111 222"},
    )

    response = client.get(
        "/api/patients/possible-duplicates?first_name=Ana&last_name=Horvat&date_of_birth=1990-01-01",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()[0]["first_name"] == "Ana"


def test_patch_patient_keeps_legacy_demo_email_readable_and_invalidates_changed_email(client, db, auth_setup):
    patient = Patient(
        first_name="Legacy",
        last_name="Email",
        email="synthetic.legacy@example.invalid",
        phone="001",
        email_verified_at=datetime.now(timezone.utc),
    )
    db.add(patient)
    db.flush()
    associate_with_test_clinic(db, auth_setup, patient)
    headers = auth_headers(client)

    phone_only = client.patch(f"/api/patients/{patient.id}", headers=headers, json={"phone": "002"})
    changed_email = client.patch(f"/api/patients/{patient.id}", headers=headers, json={"email": "synthetic.legacy@example.com"})

    assert phone_only.status_code == 200
    assert phone_only.json()["email"] == "synthetic.legacy@example.invalid"
    assert changed_email.status_code == 200
    assert changed_email.json()["email"] == "synthetic.legacy@example.com"
    db.refresh(patient)
    assert patient.email_verified_at is None


def test_patch_patient_uses_expected_updated_at_and_rejects_stale_payload(client, db, auth_setup):
    patient = Patient(first_name="Stale", last_name="Pacijent", phone="001")
    db.add(patient)
    db.flush()
    associate_with_test_clinic(db, auth_setup, patient)
    headers = auth_headers(client)
    original_updated_at = patient.updated_at.isoformat()

    ok = client.patch(f"/api/patients/{patient.id}", headers=headers, json={"expected_updated_at": original_updated_at, "phone": "002"})
    assert ok.status_code == 200
    assert ok.json()["phone"] == "002"
    db.refresh(patient)
    patient.updated_at = datetime.now(timezone.utc) + timedelta(seconds=5)
    db.commit()

    stale = client.patch(f"/api/patients/{patient.id}", headers=headers, json={"expected_updated_at": original_updated_at, "phone": "003"})
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "stale_patient"
    db.refresh(patient)
    assert patient.phone == "002"
    assert db.query(AuditLog).filter_by(entity_type="Patient", entity_id=patient.id, action="update").count() == 1


def test_stale_email_update_does_not_clear_current_verification(client, db, auth_setup):
    patient = Patient(
        first_name="Email",
        last_name="Conflict",
        email="old@example.com",
        phone="001",
        email_verified_at=datetime.now(timezone.utc),
    )
    db.add(patient)
    db.flush()
    associate_with_test_clinic(db, auth_setup, patient)
    headers = auth_headers(client)
    stale_updated_at = patient.updated_at.isoformat()
    client.patch(f"/api/patients/{patient.id}", headers=headers, json={"expected_updated_at": stale_updated_at, "phone": "002"})
    db.refresh(patient)
    patient.updated_at = datetime.now(timezone.utc) + timedelta(seconds=5)
    db.commit()

    response = client.patch(f"/api/patients/{patient.id}", headers=headers, json={"expected_updated_at": stale_updated_at, "email": "new@example.com"})

    assert response.status_code == 409
    db.refresh(patient)
    assert patient.email == "old@example.com"
    assert patient.email_verified_at is not None


def test_duplicate_oib_remains_blocked_with_expected_updated_at(client, db, auth_setup):
    existing = Patient(first_name="Vec", last_name="Postoji", oib="44444444444")
    patient = Patient(first_name="Drugi", last_name="Pacijent")
    db.add_all([existing, patient])
    db.flush()
    associate_with_test_clinic(db, auth_setup, existing)
    associate_with_test_clinic(db, auth_setup, patient)
    headers = auth_headers(client)

    response = client.patch(f"/api/patients/{patient.id}", headers=headers, json={"expected_updated_at": patient.updated_at.isoformat(), "oib": "44444444444"})

    assert response.status_code == 409
