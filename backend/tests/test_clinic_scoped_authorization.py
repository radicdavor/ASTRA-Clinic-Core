from datetime import date, datetime, time
from decimal import Decimal

from app.auth.dependencies import hash_api_key
from app.models.domain import (
    ApiKey,
    Appointment,
    Clinic,
    ClinicMembership,
    Institution,
    JourneyActivity,
    Patient,
    PatientClinicAssociation,
    PatientJourney,
    Provider,
    Role,
    Room,
    Service,
    User,
)
from app.services.seed import seed_demo_memberships
from tests.conftest import login_token


def auth_headers(client, extra: dict[str, str] | None = None) -> dict[str, str]:
    token = login_token(client, "admin@test.local")
    headers = {"Authorization": f"Bearer {token}"}
    if extra:
        headers.update(extra)
    return headers


def seed_two_clinic_patients(db, auth_setup):
    clinic_a = auth_setup["clinic"]
    clinic_b = Clinic(name="Other Clinic")
    patient_a = Patient(first_name="Clinic", last_name="Alpha", oib="10000000001")
    patient_b = Patient(first_name="Clinic", last_name="Beta", oib="20000000002")
    db.add_all([clinic_b, patient_a, patient_b])
    db.flush()
    db.add_all(
        [
            PatientClinicAssociation(patient_id=patient_a.id, clinic_id=clinic_a.id, created_by_user_id=auth_setup["admin"].id),
            PatientClinicAssociation(patient_id=patient_b.id, clinic_id=clinic_b.id, created_by_user_id=auth_setup["admin"].id),
        ]
    )
    db.commit()
    return clinic_a, clinic_b, patient_a, patient_b


def test_patient_directory_returns_only_active_clinic_patients(client, db, auth_setup):
    _, _, patient_a, patient_b = seed_two_clinic_patients(db, auth_setup)

    response = client.get("/api/patients", headers=auth_headers(client))

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert patient_a.id in ids
    assert patient_b.id not in ids


def test_direct_patient_identity_from_other_clinic_is_not_enumerable(client, db, auth_setup):
    _, _, _, patient_b = seed_two_clinic_patients(db, auth_setup)

    response = client.get(f"/api/patients/{patient_b.id}", headers=auth_headers(client))

    missing = client.get("/api/patients/2147483647", headers=auth_headers(client))
    assert response.status_code == missing.status_code == 404
    assert response.json() == missing.json()


def test_inactive_patient_clinic_association_does_not_grant_operational_access(client, db, auth_setup):
    patient_obj = Patient(first_name="Inactive", last_name="Association")
    db.add(patient_obj)
    db.flush()
    db.add(
        PatientClinicAssociation(
            patient_id=patient_obj.id,
            clinic_id=auth_setup["clinic"].id,
            active=False,
            created_by_user_id=auth_setup["admin"].id,
        )
    )
    db.commit()

    directory = client.get("/api/patients?q=Inactive", headers=auth_headers(client))
    detail = client.get(f"/api/patients/{patient_obj.id}", headers=auth_headers(client))

    assert directory.status_code == 200
    assert directory.json() == []
    assert detail.status_code == 404


def test_cross_clinic_patient_appointments_require_scoped_patient_first(client, db, auth_setup):
    _, clinic_b, _, patient_b = seed_two_clinic_patients(db, auth_setup)
    provider = Provider(full_name="Dr. Other", active=True)
    service = Service(name="Other Service", duration_minutes=30, price=Decimal("80.00"), active=True)
    room_b = Room(name="Other Clinic Room", clinic_id=clinic_b.id, active=True)
    db.add_all([provider, service, room_b])
    db.flush()
    appointment_b = Appointment(
        patient_id=patient_b.id,
        service_id=service.id,
        provider_id=provider.id,
        room_id=room_b.id,
        clinic_id=clinic_b.id,
        date=date(2026, 7, 21),
        start_time=time(11, 0),
        end_time=time(11, 30),
        duration_minutes=30,
    )
    db.add(appointment_b)
    db.commit()

    response = client.get(f"/api/patients/{patient_b.id}/appointments", headers=auth_headers(client))

    assert response.status_code == 404


def test_cross_clinic_patient_billing_context_remains_scoped(client, db, auth_setup):
    _, _, _, patient_b = seed_two_clinic_patients(db, auth_setup)

    response = client.get(f"/api/patients/{patient_b.id}/invoices", headers=auth_headers(client))

    assert response.status_code == 404


def test_patient_search_uses_active_clinic_identity_directory(client, db, auth_setup):
    _, _, patient_a, patient_b = seed_two_clinic_patients(db, auth_setup)

    response = client.get("/api/search?q=Clinic", headers=auth_headers(client))

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["patients"]}
    assert patient_a.id in ids
    assert patient_b.id not in ids


def test_operational_patient_identity_hides_sibling_and_foreign_institution(client, db, auth_setup):
    clinic_a = auth_setup["clinic"]
    sibling = Clinic(name="Sibling Clinic", institution_id=clinic_a.institution_id)
    foreign_institution = Institution(code="SYNTH-B", name="Synthetic Institution B")
    db.add_all([sibling, foreign_institution])
    db.flush()
    foreign = Clinic(name="Foreign Institution Clinic", institution_id=foreign_institution.id)
    sibling_patient = Patient(first_name="SiblingSecret", last_name="Patient", oib="30000000003")
    foreign_patient = Patient(first_name="ForeignSecret", last_name="Patient", oib="40000000004")
    db.add_all([foreign, sibling_patient, foreign_patient])
    db.flush()
    db.add_all(
        [
            PatientClinicAssociation(patient_id=sibling_patient.id, clinic_id=sibling.id, active=True),
            PatientClinicAssociation(patient_id=foreign_patient.id, clinic_id=foreign.id, active=True),
        ]
    )
    db.commit()
    headers = auth_headers(client)

    directory = client.get("/api/patients?q=Secret", headers=headers)
    search = client.get("/api/search?q=Secret", headers=headers)
    sibling_detail = client.get(f"/api/patients/{sibling_patient.id}", headers=headers)
    foreign_detail = client.get(f"/api/patients/{foreign_patient.id}", headers=headers)
    missing_detail = client.get("/api/patients/2147483647", headers=headers)
    sibling_duplicates = client.get(
        "/api/patients/possible-duplicates?oib=30000000003", headers=headers
    )
    foreign_duplicates = client.get(
        "/api/patients/possible-duplicates?oib=40000000004", headers=headers
    )

    assert directory.status_code == search.status_code == 200
    assert directory.json() == []
    assert search.json()["patients"] == []
    assert sibling_duplicates.json() == foreign_duplicates.json() == []
    assert sibling_detail.status_code == foreign_detail.status_code == missing_detail.status_code == 404
    assert sibling_detail.json() == foreign_detail.json() == missing_detail.json()
    combined = directory.text + search.text + sibling_detail.text + foreign_detail.text
    assert "SiblingSecret" not in combined
    assert "ForeignSecret" not in combined


def test_cross_clinic_patient_mutations_fail_before_database_change(client, db, auth_setup):
    _, _, _, patient_b = seed_two_clinic_patients(db, auth_setup)
    before = (patient_b.first_name, patient_b.last_name, patient_b.phone)

    response = client.patch(
        f"/api/patients/{patient_b.id}",
        headers=auth_headers(client),
        json={"first_name": "UnauthorizedMutation", "phone": "999"},
    )

    assert response.status_code == 404
    db.refresh(patient_b)
    assert (patient_b.first_name, patient_b.last_name, patient_b.phone) == before


def test_scheduling_routes_reject_cross_clinic_patient_before_insert(client, db, auth_setup):
    _, _, _, patient_b = seed_two_clinic_patients(db, auth_setup)
    clinic_a = auth_setup["clinic"]
    provider = Provider(full_name="Dr. Active Clinic", clinic_id=clinic_a.id, active=True)
    service = Service(name="Active Clinic Service", duration_minutes=30, price=Decimal("80.00"), active=True)
    room = Room(name="Active Clinic Scheduling Room", clinic_id=clinic_a.id, active=True)
    db.add_all([provider, service, room])
    db.commit()
    payload = {
        "patient_id": patient_b.id,
        "provider_id": provider.id,
        "service_id": service.id,
        "room_id": room.id,
        "date": "2026-07-22",
        "start_time": "09:00",
        "end_time": "09:30",
        "duration_minutes": 30,
        "status": "scheduled",
        "source": "manual",
    }
    before = db.query(Appointment).count()

    for route in ("/api/appointments", "/api/intake/web/appointments", "/api/ai/appointments/create"):
        response = client.post(route, headers=auth_headers(client), json=payload)
        assert response.status_code == 404

    assert db.query(Appointment).count() == before


def test_clinic_api_key_cannot_schedule_patient_from_another_clinic(client, db, auth_setup):
    _, _, _, patient_b = seed_two_clinic_patients(db, auth_setup)
    clinic_a = auth_setup["clinic"]
    provider = Provider(full_name="Dr. API Scope", clinic_id=clinic_a.id, active=True)
    service = Service(name="API Scope Service", duration_minutes=30, price=Decimal("80.00"), active=True)
    room = Room(name="API Scope Room", clinic_id=clinic_a.id, active=True)
    raw_key = "synthetic_patient_scope_key"
    db.add_all(
        [
            provider,
            service,
            room,
            ApiKey(
                name="Synthetic patient-scope scheduler",
                key_hash=hash_api_key(raw_key),
                scopes=["ai.appointments.create"],
                clinic_id=clinic_a.id,
                institution_id=clinic_a.institution_id,
                active=True,
            ),
        ]
    )
    db.commit()
    before = db.query(Appointment).count()

    response = client.post(
        "/api/ai/appointments/create",
        headers={"X-ASTRA-API-Key": raw_key},
        json={
            "patient_id": patient_b.id,
            "provider_id": provider.id,
            "service_id": service.id,
            "room_id": room.id,
            "date": "2026-07-22",
            "start_time": "10:00",
            "end_time": "10:30",
            "duration_minutes": 30,
            "status": "scheduled",
            "source": "ai_agent",
        },
    )

    assert response.status_code == 404
    assert db.query(Appointment).count() == before


def test_user_with_multiple_memberships_must_select_active_clinic(client, db, auth_setup):
    clinic_b = Clinic(name="Second Membership Clinic")
    db.add(clinic_b)
    db.flush()
    db.add(ClinicMembership(user_id=auth_setup["admin"].id, clinic_id=clinic_b.id, created_by_user_id=auth_setup["admin"].id))
    db.commit()

    response = client.get("/api/patients", headers=auth_headers(client))

    assert response.status_code == 409
    assert "aktivne klinike" in response.json()["detail"]


def test_current_user_clinics_reports_default_and_selection_requirement(client, db, auth_setup):
    single = client.get("/auth/me/clinics", headers=auth_headers(client))
    assert single.status_code == 200
    assert single.json()["default_clinic_id"] == auth_setup["clinic"].id
    assert single.json()["requires_selection"] is False

    clinic_b = Clinic(name="Selectable Clinic")
    db.add(clinic_b)
    db.flush()
    db.add(ClinicMembership(user_id=auth_setup["admin"].id, clinic_id=clinic_b.id, created_by_user_id=auth_setup["admin"].id))
    db.commit()

    multiple = client.get("/auth/me/clinics", headers=auth_headers(client))
    assert multiple.status_code == 200
    assert multiple.json()["default_clinic_id"] is None
    assert multiple.json()["requires_selection"] is True


def test_seed_demo_memberships_assigns_demo_roles_to_clinics(db):
    clinic_a = Clinic(name="Demo Seed Clinic A")
    clinic_b = Clinic(name="Demo Seed Clinic B")
    role = Role(name="demo_admin", description="Demo Admin")
    user = User(email="demo.seed@astra.local", full_name="Demo Seed", password_hash="demo", role=role)
    db.add_all([clinic_a, clinic_b, role, user])
    db.commit()

    seed_demo_memberships(db)
    db.commit()

    memberships = db.query(ClinicMembership).filter(ClinicMembership.user_id == user.id).all()
    assert {membership.clinic_id for membership in memberships} == {clinic_a.id, clinic_b.id}
    assert all(membership.active for membership in memberships)


def test_invalid_active_clinic_header_is_rejected(client, db, auth_setup):
    clinic_b = Clinic(name="Forbidden Header Clinic")
    db.add(clinic_b)
    db.commit()

    response = client.get("/api/patients", headers=auth_headers(client, {"X-Clinic-Id": str(clinic_b.id)}))

    assert response.status_code == 403


def test_dashboard_returns_only_active_clinic_journeys(client, db, auth_setup):
    clinic_a = auth_setup["clinic"]
    clinic_b = Clinic(name="Dashboard Other Clinic")
    provider = Provider(full_name="Dr. Scope", active=True)
    service = Service(name="Scope Gastroscopy", duration_minutes=30, price=Decimal("120.00"), active=True)
    room_a = Room(name="Scope Room A", clinic_id=clinic_a.id, active=True)
    room_b = Room(name="Scope Room B", clinic_id=clinic_b.id, active=True)
    patient_a = Patient(first_name="Dashboard", last_name="Visible")
    patient_b = Patient(first_name="Dashboard", last_name="Hidden")
    db.add_all([clinic_b, provider, service, room_a, room_b, patient_a, patient_b])
    db.flush()
    db.add_all(
        [
            PatientClinicAssociation(patient_id=patient_a.id, clinic_id=clinic_a.id),
            PatientClinicAssociation(patient_id=patient_b.id, clinic_id=clinic_b.id),
        ]
    )
    appointment_a = Appointment(
        patient_id=patient_a.id,
        service_id=service.id,
        provider_id=provider.id,
        room_id=room_a.id,
        clinic_id=clinic_a.id,
        date=date(2026, 7, 20),
        start_time=time(9, 0),
        end_time=time(9, 30),
        duration_minutes=30,
    )
    appointment_b = Appointment(
        patient_id=patient_b.id,
        service_id=service.id,
        provider_id=provider.id,
        room_id=room_b.id,
        clinic_id=clinic_b.id,
        date=date(2026, 7, 20),
        start_time=time(10, 0),
        end_time=time(10, 30),
        duration_minutes=30,
    )
    db.add_all([appointment_a, appointment_b])
    db.flush()
    journey_a = PatientJourney(patient_id=patient_a.id, appointment_id=appointment_a.id, clinic_id=clinic_a.id, intake_channel="manual", current_stage="booked")
    journey_b = PatientJourney(patient_id=patient_b.id, appointment_id=appointment_b.id, clinic_id=clinic_b.id, intake_channel="manual", current_stage="booked")
    db.add_all([journey_a, journey_b])
    db.flush()
    db.add_all(
        [
            JourneyActivity(
                journey_id=journey_a.id,
                appointment_id=appointment_a.id,
                service_id=service.id,
                activity_key="primary",
                activity_kind="specialist_consultation",
                specialty_key="gastro",
                clinic_id=clinic_a.id,
                primary_provider_id=provider.id,
                room_id=room_a.id,
                sequence=1,
                planned_start=datetime(2026, 7, 20, 9, 0),
                planned_end=datetime(2026, 7, 20, 9, 30),
            ),
            JourneyActivity(
                journey_id=journey_b.id,
                appointment_id=appointment_b.id,
                service_id=service.id,
                activity_key="primary",
                activity_kind="specialist_consultation",
                specialty_key="gastro",
                clinic_id=clinic_b.id,
                primary_provider_id=provider.id,
                room_id=room_b.id,
                sequence=1,
                planned_start=datetime(2026, 7, 20, 10, 0),
                planned_end=datetime(2026, 7, 20, 10, 30),
            ),
        ]
    )
    db.commit()

    response = client.get("/api/dashboard/day?selected_date=2026-07-20", headers=auth_headers(client))

    assert response.status_code == 200
    names = {row["patient_name"] for row in response.json()["rows"]}
    assert "Dashboard Visible" in names
    assert "Dashboard Hidden" not in names


def test_direct_patient_journey_detail_is_scoped_to_active_clinic(client, db, auth_setup):
    clinic_a = auth_setup["clinic"]
    clinic_b = Clinic(name="Journey Detail Other Clinic")
    provider = Provider(full_name="Dr. Journey Scope", active=True)
    service = Service(name="Journey Scope Service", duration_minutes=30, price=Decimal("120.00"), active=True)
    room_b = Room(name="Journey Scope Room B", clinic_id=clinic_b.id, active=True)
    patient_b = Patient(first_name="Journey", last_name="Hidden")
    db.add_all([clinic_b, provider, service, room_b, patient_b])
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient_b.id, clinic_id=clinic_b.id))
    appointment_b = Appointment(
        patient_id=patient_b.id,
        service_id=service.id,
        provider_id=provider.id,
        room_id=room_b.id,
        clinic_id=clinic_b.id,
        date=date(2026, 7, 20),
        start_time=time(11, 0),
        end_time=time(11, 30),
        duration_minutes=30,
    )
    db.add(appointment_b)
    db.flush()
    journey_b = PatientJourney(patient_id=patient_b.id, appointment_id=appointment_b.id, clinic_id=clinic_b.id, intake_channel="manual", current_stage="booked")
    db.add(journey_b)
    db.commit()

    response = client.get(f"/api/patient-journeys/{journey_b.id}", headers=auth_headers(client, {"X-Clinic-Id": str(clinic_a.id)}))

    assert response.status_code == 404
    assert response.json()["detail"] == "Tijek pacijenta nije pronađen"
