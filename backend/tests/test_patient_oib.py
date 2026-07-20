from datetime import datetime, timezone

from app.models.domain import Patient
from tests.conftest import login_token


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


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


def test_patient_search_includes_oib(client, auth_setup):
    headers = auth_headers(client)
    client.post("/api/patients", headers=headers, json={"first_name": "Search", "last_name": "Oib", "oib": "33333333333"})

    response = client.get("/api/patients?q=33333333333", headers=headers)

    assert response.status_code == 200
    assert [patient["oib"] for patient in response.json()] == ["33333333333"]


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
    db.commit()
    headers = auth_headers(client)

    phone_only = client.patch(f"/api/patients/{patient.id}", headers=headers, json={"phone": "002"})
    changed_email = client.patch(f"/api/patients/{patient.id}", headers=headers, json={"email": "synthetic.legacy@example.com"})

    assert phone_only.status_code == 200
    assert phone_only.json()["email"] == "synthetic.legacy@example.invalid"
    assert changed_email.status_code == 200
    assert changed_email.json()["email"] == "synthetic.legacy@example.com"
    db.refresh(patient)
    assert patient.email_verified_at is None
