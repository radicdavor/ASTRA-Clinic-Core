from datetime import date, time

import pytest
from fastapi import HTTPException

from app.models.domain import Appointment
from app.services.appointments import validate_appointment_payload
from tests.conftest import login_token
from tests.factories import appointment, patient, provider, room, service


def test_reject_end_time_before_start_time(db):
    p = provider(db)
    r = room(db)

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(db, date(2026, 7, 5), time(10, 0), time(9, 0), p.id, r.id, "scheduled", "manual")

    assert exc.value.status_code == 422


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


def test_create_appointment_succeeds(db):
    p = patient(db)
    pr = provider(db)
    rm = room(db)
    sv = service(db)
    duration = validate_appointment_payload(db, date(2026, 7, 5), time(11, 0), time(11, 30), pr.id, rm.id, "scheduled", "manual")
    obj = Appointment(patient_id=p.id, provider_id=pr.id, room_id=rm.id, service_id=sv.id, date=date(2026, 7, 5), start_time=time(11, 0), end_time=time(11, 30), duration_minutes=duration)
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
