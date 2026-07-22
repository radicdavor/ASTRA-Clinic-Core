from datetime import date, time

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.domain import Appointment, Clinic, ClinicMembership, PatientJourney, Permission, Role, User
from app.core.security import hash_password
from app.services.appointments import APPOINTMENT_STATUSES_BLOCKING_PATIENT_TIME, calculate_duration_minutes, validate_appointment_payload
from tests.conftest import login_token
from tests.factories import appointment, episode, patient, provider, room, service


def appointment_payload(patient_obj, provider_obj, room_obj, service_obj, start="09:15", end="09:45", status="scheduled"):
    return {
        "patient_id": patient_obj.id,
        "provider_id": provider_obj.id,
        "room_id": room_obj.id,
        "service_id": service_obj.id,
        "date": "2026-07-06",
        "start_time": start,
        "end_time": end,
        "duration_minutes": 30,
        "status": status,
        "source": "manual",
    }


def test_reject_end_time_before_start_time(db):
    p = provider(db)
    r = room(db)

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(db, date(2026, 7, 6), time(10, 0), time(9, 0), p.id, r.id, "scheduled", "manual")

    assert exc.value.status_code == 422


def test_appointment_duration_rejects_ambiguous_clinic_local_time():
    with pytest.raises(HTTPException) as exc:
        calculate_duration_minutes(date(2026, 10, 25), time(2, 30), time(3, 30), "Europe/Zagreb")

    assert exc.value.status_code == 422
    assert "dvosmisleno" in exc.value.detail


def test_appointment_duration_rejects_nonexistent_clinic_local_time():
    with pytest.raises(HTTPException) as exc:
        calculate_duration_minutes(date(2026, 3, 29), time(2, 30), time(3, 30), "Europe/Zagreb")

    assert exc.value.status_code == 422
    assert "ne postoji" in exc.value.detail


def test_reject_provider_overlap(db):
    existing = appointment(db)

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(db, existing.date, time(9, 15), time(9, 45), existing.provider_id, existing.room_id + 100, "scheduled", "manual")

    assert exc.value.status_code == 409


def test_reject_room_overlap(db):
    existing = appointment(db)
    other_provider = provider(db, "dr. Other")

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(db, existing.date, time(9, 15), time(9, 45), other_provider.id, existing.room_id, "scheduled", "manual")

    assert exc.value.status_code == 409


def test_cancelled_appointment_does_not_block_time(db):
    existing = appointment(db, status="cancelled")

    duration = validate_appointment_payload(db, existing.date, time(9, 15), time(9, 45), existing.provider_id, existing.room_id, "scheduled", "manual")

    assert duration == 30


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (time(9, 0), time(9, 30)),
        (time(8, 45), time(9, 15)),
        (time(9, 15), time(9, 45)),
        (time(9, 5), time(9, 25)),
        (time(8, 45), time(9, 45)),
    ],
)
def test_same_patient_overlapping_intervals_block_even_across_resources(db, start, end):
    existing = appointment(db)
    other_provider = provider(db, "dr. Other resource")
    other_room = room(db, "Other resource room")

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(
            db,
            existing.date,
            start,
            end,
            other_provider.id,
            other_room.id,
            "scheduled",
            "manual",
            patient_id=existing.patient_id,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "patient_appointment_overlap"
    assert "conflicts" in exc.value.detail


def test_touching_patient_appointments_do_not_conflict(db):
    existing = appointment(db)
    other_provider = provider(db, "dr. Touching")
    other_room = room(db, "Touching room")

    duration = validate_appointment_payload(
        db,
        existing.date,
        time(9, 30),
        time(10, 0),
        other_provider.id,
        other_room.id,
        "scheduled",
        "manual",
        patient_id=existing.patient_id,
    )

    assert duration == 30


def test_patient_appointment_on_different_day_does_not_conflict(db):
    existing = appointment(db)
    other_provider = provider(db, "dr. Different day")
    other_room = room(db, "Different day room")

    duration = validate_appointment_payload(
        db,
        date(2026, 7, 7),
        time(9, 0),
        time(9, 30),
        other_provider.id,
        other_room.id,
        "scheduled",
        "manual",
        patient_id=existing.patient_id,
    )

    assert duration == 30


def test_other_patient_same_time_does_not_trigger_patient_overlap(db):
    existing = appointment(db)
    other_patient = patient(db, first_name="Other")
    other_provider = provider(db, "dr. Other patient")
    other_room = room(db, "Other patient room")

    duration = validate_appointment_payload(
        db,
        existing.date,
        existing.start_time,
        existing.end_time,
        other_provider.id,
        other_room.id,
        "scheduled",
        "manual",
        patient_id=other_patient.id,
    )

    assert duration == 30


def test_nonblocking_status_does_not_block_patient_time(db):
    existing = appointment(db, status="cancelled")
    other_provider = provider(db, "dr. Cancelled patient")
    other_room = room(db, "Cancelled patient room")

    duration = validate_appointment_payload(
        db,
        existing.date,
        existing.start_time,
        existing.end_time,
        other_provider.id,
        other_room.id,
        "scheduled",
        "manual",
        patient_id=existing.patient_id,
    )

    assert duration == 30


def test_formal_patient_time_blocking_statuses_are_known():
    assert "confirmed" in APPOINTMENT_STATUSES_BLOCKING_PATIENT_TIME
    assert "rescheduled" in APPOINTMENT_STATUSES_BLOCKING_PATIENT_TIME
    assert "cancelled" not in APPOINTMENT_STATUSES_BLOCKING_PATIENT_TIME
    assert "no_show" not in APPOINTMENT_STATUSES_BLOCKING_PATIENT_TIME


def test_create_appointment_succeeds(db):
    p = patient(db)
    pr = provider(db)
    rm = room(db)
    sv = service(db)
    duration = validate_appointment_payload(db, date(2026, 7, 6), time(11, 0), time(11, 30), pr.id, rm.id, "scheduled", "manual")
    obj = Appointment(patient_id=p.id, provider_id=pr.id, room_id=rm.id, service_id=sv.id, date=date(2026, 7, 6), start_time=time(11, 0), end_time=time(11, 30), duration_minutes=duration)
    db.add(obj)
    db.flush()

    assert obj.id is not None


def test_appointment_detail_includes_patient_provider_and_room(client, db, auth_setup):
    obj = appointment(db)
    token = login_token(client, "admin@test.local")

    response = client.get(f"/api/appointments/{obj.id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient"]["first_name"]
    assert payload["provider"]["full_name"]
    assert payload["room"]["name"]


def test_update_appointment_revalidates_conflicts(db):
    existing = appointment(db)
    other_patient = patient(db, first_name="Other")
    other_service = service(db, name="Other service")
    candidate = appointment(
        db,
        patient_obj=other_patient,
        provider_obj=provider(db, "dr. Candidate"),
        room_obj=room(db, "Candidate room"),
        service_obj=other_service,
    )

    candidate.provider_id = existing.provider_id

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(
            db,
            candidate.date,
            candidate.start_time,
            candidate.end_time,
            candidate.provider_id,
            candidate.room_id,
            candidate.status,
            candidate.source,
            appointment_id=candidate.id,
        )

    assert exc.value.status_code == 409


def test_update_appointment_excludes_itself_from_patient_overlap(db):
    existing = appointment(db)

    duration = validate_appointment_payload(
        db,
        existing.date,
        existing.start_time,
        existing.end_time,
        existing.provider_id,
        existing.room_id,
        existing.status,
        existing.source,
        patient_id=existing.patient_id,
        appointment_id=existing.id,
    )

    assert duration == 30


def test_update_appointment_to_patient_conflict_blocks(db):
    existing = appointment(db)
    candidate = appointment(
        db,
        patient_obj=patient(db, first_name="Candidate"),
        provider_obj=provider(db, "dr. Candidate patient conflict"),
        room_obj=room(db, "Candidate patient conflict room"),
        service_obj=service(db, name="Candidate service"),
    )

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(
            db,
            existing.date,
            existing.start_time,
            existing.end_time,
            candidate.provider_id,
            candidate.room_id,
            candidate.status,
            candidate.source,
            patient_id=existing.patient_id,
            appointment_id=candidate.id,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "patient_appointment_overlap"


def test_reject_service_in_incompatible_room(db):
    pr = provider(db)
    rm = room(db)
    allowed_service = service(db, name="Allowed")
    blocked_service = service(db, name="Blocked")
    rm.allowed_services = [allowed_service]
    db.flush()

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(db, date(2026, 7, 6), time(11, 0), time(11, 30), pr.id, rm.id, "scheduled", "manual", service_id=blocked_service.id)

    assert exc.value.status_code == 409


def test_reject_appointment_on_sunday(db):
    pr = provider(db)
    rm = room(db)

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(db, date(2026, 7, 5), time(11, 0), time(11, 30), pr.id, rm.id, "scheduled", "manual")

    assert exc.value.status_code == 422
    assert "Nedjelja je neradni dan" in exc.value.detail


def test_create_appointment_api_blocks_cross_clinic_same_patient_overlap(client, db, auth_setup):
    clinic_b = Clinic(name="Other scheduling clinic")
    p = patient(db)
    service_obj = service(db, name="Cross clinic service")
    existing = appointment(db, patient_obj=p, service_obj=service_obj)
    provider_b = provider(db, "dr. Cross clinic")
    room_b = room(db, "Cross clinic room")
    db.add(clinic_b)
    db.flush()
    room_b.clinic_id = clinic_b.id
    db.add(ClinicMembership(user_id=auth_setup["admin"].id, clinic_id=clinic_b.id, created_by_user_id=auth_setup["admin"].id))
    db.commit()
    token = login_token(client, "admin@test.local")

    response = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {token}", "X-Clinic-Id": str(clinic_b.id)},
        json=appointment_payload(p, provider_b, room_b, service_obj, start="09:15", end="09:45"),
    )

    assert existing.id
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "patient_appointment_overlap"
    assert detail["conflicts"][0]["patient_id"] == p.id
    forbidden_keys = {"notes", "price", "total_amount", "diagnosis", "anamnesis", "reception_note"}
    assert forbidden_keys.isdisjoint(detail["conflicts"][0].keys())


def test_create_appointment_api_allows_touching_patient_appointment(client, db, auth_setup):
    p = patient(db)
    existing = appointment(db, patient_obj=p)
    provider_obj = provider(db, "dr. Touch api")
    room_obj = room(db, "Touch api room")
    room_obj.clinic_id = auth_setup["clinic"].id
    service_obj = service(db, name="Touch api service")
    db.commit()
    token = login_token(client, "admin@test.local")

    response = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json=appointment_payload(p, provider_obj, room_obj, service_obj, start="09:30", end="10:00"),
    )

    assert existing.id
    assert response.status_code == 200


def test_update_appointment_api_blocks_patient_overlap(client, db, auth_setup):
    existing = appointment(db)
    candidate = appointment(
        db,
        patient_obj=patient(db, first_name="Patch"),
        provider_obj=provider(db, "dr. Patch conflict"),
        room_obj=room(db, "Patch conflict room"),
        service_obj=service(db, name="Patch service"),
    )
    token = login_token(client, "admin@test.local")

    response = client.patch(
        f"/api/appointments/{candidate.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"patient_id": existing.patient_id},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "patient_appointment_overlap"


def test_update_appointment_cannot_change_patient_of_linked_episode_or_journey(client, db, auth_setup):
    original_patient = patient(db, first_name="Original")
    replacement_patient = patient(db, first_name="Replacement")
    clinical_episode = episode(db, patient_obj=original_patient)
    linked_appointment = appointment(db, patient_obj=original_patient)
    linked_appointment.episode_id = clinical_episode.id
    db.flush()
    token = login_token(client, "admin@test.local")
    headers = {"Authorization": f"Bearer {token}"}
    journey_response = client.post(
        "/api/patient-journeys",
        headers=headers,
        json={"appointment_id": linked_appointment.id, "intake_channel": "manual", "initial_stage": "booked"},
    )
    assert journey_response.status_code == 200
    journey_id = journey_response.json()["id"]

    response = client.patch(
        f"/api/appointments/{linked_appointment.id}",
        headers=headers,
        json={"patient_id": replacement_patient.id},
    )

    assert response.status_code == 409
    db.refresh(linked_appointment)
    assert linked_appointment.patient_id == original_patient.id
    assert linked_appointment.episode_id == clinical_episode.id
    assert db.get(PatientJourney, journey_id).patient_id == original_patient.id


def test_appointments_list_is_scoped_to_active_clinic(client, db, auth_setup):
    clinic_b = Clinic(name="Hidden schedule clinic")
    service_obj = service(db, name="Scoped list service")
    provider_b = provider(db, "dr. Hidden")
    room_b = room(db, "Hidden room")
    db.add(clinic_b)
    db.flush()
    room_b.clinic_id = clinic_b.id
    visible = appointment(db, service_obj=service_obj)
    hidden = appointment(db, provider_obj=provider_b, room_obj=room_b, service_obj=service_obj)
    db.commit()
    token = login_token(client, "admin@test.local")

    response = client.get("/api/appointments", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert visible.id in ids
    assert hidden.id not in ids


def test_patient_availability_requires_specific_permission(client, db, auth_setup):
    p = patient(db)
    permission = db.scalar(select(Permission).where(Permission.name == "patients.read"))
    role = Role(name="patient-reader-only", description="Patient Reader", permissions=[permission])
    user = User(email="patient-reader@test.local", full_name="Patient Reader", password_hash=hash_password("secret"), role=role)
    db.add_all([permission, role, user])
    db.flush()
    db.add(ClinicMembership(user_id=user.id, clinic_id=auth_setup["clinic"].id, created_by_user_id=auth_setup["admin"].id))
    db.commit()
    token = login_token(client, "patient-reader@test.local")

    response = client.get(f"/api/patients/{p.id}/appointments", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_patient_availability_returns_minimal_cross_clinic_dto(client, db, auth_setup):
    clinic_b = Clinic(name="Visible conflict clinic")
    service_obj = service(db, name="Minimal DTO service")
    provider_b = provider(db, "dr. Minimal DTO")
    room_b = room(db, "Minimal DTO room")
    db.add(clinic_b)
    db.flush()
    room_b.clinic_id = clinic_b.id
    p = patient(db)
    obj = appointment(db, patient_obj=p, provider_obj=provider_b, room_obj=room_b, service_obj=service_obj)
    db.commit()
    token = login_token(client, "admin@test.local")

    response = client.get(f"/api/patients/{p.id}/appointments", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload == [
        {
            "appointment_id": obj.id,
            "patient_id": p.id,
            "date": "2026-07-06",
            "start_time": "09:00:00",
            "end_time": "09:30:00",
            "status": "scheduled",
            "clinic": {"id": clinic_b.id, "name": clinic_b.name},
            "service_name": service_obj.name,
            "provider_name": provider_b.full_name,
        }
    ]


def test_reception_list_and_arrival_action(client, db, auth_setup):
    obj = appointment(db)
    token = login_token(client, "admin@test.local")
    headers = {"Authorization": f"Bearer {token}"}

    slots = client.get(f"/api/reception/day?date={obj.date}", headers=headers)
    assert slots.status_code == 200
    assert any(slot["appointment"] and slot["appointment"]["id"] == obj.id for slot in slots.json())
    assert any(slot["empty"] for slot in slots.json())

    arrived = client.post(f"/api/appointments/{obj.id}/mark-arrived", headers=headers, json={"identity_verified": True})
    assert arrived.status_code == 200
    assert arrived.json()["status"] == "arrived"
    assert arrived.json()["arrived_at"]
    assert arrived.json()["identity_verified_at"]

    audit = client.get(f"/api/audit-log?entity_type=Appointment&entity_id={obj.id}", headers=headers)
    assert audit.status_code == 200
    assert any(item["action"] == "mark_arrived" for item in audit.json())


def test_reception_rejects_arrival_without_identity_verification(client, db, auth_setup):
    obj = appointment(db)
    token = login_token(client, "admin@test.local")

    response = client.post(
        f"/api/appointments/{obj.id}/mark-arrived",
        headers={"Authorization": f"Bearer {token}"},
        json={"identity_verified": False},
    )

    assert response.status_code == 422
    assert obj.status == "scheduled"


def test_reception_rejects_arrival_from_terminal_status(client, db, auth_setup):
    obj = appointment(db, status="cancelled")
    token = login_token(client, "admin@test.local")

    response = client.post(
        f"/api/appointments/{obj.id}/mark-arrived",
        headers={"Authorization": f"Bearer {token}"},
        json={"identity_verified": True},
    )

    assert response.status_code == 409


def test_reception_start_service_requires_arrival_and_verified_identity(client, db, auth_setup):
    obj = appointment(db)
    token = login_token(client, "admin@test.local")
    headers = {"Authorization": f"Bearer {token}"}

    blocked = client.post(f"/api/appointments/{obj.id}/start-service", headers=headers)
    assert blocked.status_code == 409

    arrived = client.post(
        f"/api/appointments/{obj.id}/mark-arrived",
        headers=headers,
        json={"identity_verified": True},
    )
    assert arrived.status_code == 200

    started = client.post(f"/api/appointments/{obj.id}/start-service", headers=headers)
    assert started.status_code == 200
    assert started.json()["status"] == "in_progress"

    audit_response = client.get(f"/api/audit-log?entity_type=Appointment&entity_id={obj.id}", headers=headers)
    assert audit_response.status_code == 200
    assert any(item["action"] == "start_service" for item in audit_response.json())
