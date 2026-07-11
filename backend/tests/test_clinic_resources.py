from datetime import date, time

import pytest
from fastapi import HTTPException

from app.models.domain import Provider
from app.services.appointments import validate_appointment_payload
from tests.conftest import login_token
from tests.factories import room


def test_create_clinic_room_and_provider(client, auth_setup):
    headers = {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}

    clinic = client.post("/api/clinics", headers=headers, json={"name": "Kardiologija"})
    assert clinic.status_code == 200
    clinic_id = clinic.json()["id"]

    created_room = client.post("/api/rooms", headers=headers, json={"name": "Kardio 1", "type": "ordinacija", "clinic_id": clinic_id})
    assert created_room.status_code == 200
    assert created_room.json()["clinic_id"] == clinic_id

    provider = client.post("/api/providers", headers=headers, json={
        "full_name": "dr. Test Kardiolog",
        "specialty": "kardiologija",
        "email": "kardiolog@example.hr",
        "clinic_id": clinic_id,
        "work_start": "08:00",
        "work_end": "16:00",
    })
    assert provider.status_code == 200
    assert provider.json()["email"] == "kardiolog@example.hr"
    assert provider.json()["work_start"] == "08:00:00"
    assert provider.json()["work_end"] == "16:00:00"


def test_reject_appointment_outside_provider_working_hours(db):
    provider = Provider(full_name="dr. Morning", specialty="test", email="morning@example.hr", work_start=time(8, 0), work_end=time(12, 0))
    db.add(provider)
    db.flush()
    provider_room = room(db)

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(db, date(2026, 7, 6), time(12, 0), time(12, 30), provider.id, provider_room.id, "scheduled", "manual")

    assert exc.value.status_code == 409
    assert "izvan radnog vremena liječnika" in exc.value.detail
