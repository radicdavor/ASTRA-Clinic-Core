from datetime import date, time

import pytest
from fastapi import HTTPException

from app.models.domain import AuditLog, Clinic, Provider, Room, Service
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
    assert provider.json()["weekly_working_hours"]["0"] == {"enabled": True, "start": "08:00", "end": "16:00"}
    assert provider.json()["weekly_working_hours"]["6"]["enabled"] is False


def test_reject_appointment_outside_provider_working_hours(db):
    provider = Provider(full_name="dr. Morning", specialty="test", email="morning@example.hr", work_start=time(8, 0), work_end=time(12, 0))
    db.add(provider)
    db.flush()
    provider_room = room(db)

    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(db, date(2026, 7, 6), time(12, 0), time(12, 30), provider.id, provider_room.id, "scheduled", "manual")

    assert exc.value.status_code == 409
    assert "izvan radnog vremena liječnika" in exc.value.detail


def test_weekly_working_hours_allow_variable_days_and_reject_day_off(db):
    weekly = {str(day): {"enabled": day in {1, 3}, "start": "10:00", "end": "18:00"} for day in range(7)}
    provider = Provider(full_name="dr. Part Time", specialty="test", weekly_working_hours=weekly, work_start=time(7), work_end=time(20))
    db.add(provider); db.flush(); provider_room = room(db)
    assert validate_appointment_payload(db, date(2026, 7, 7), time(10), time(10, 30), provider.id, provider_room.id, "scheduled", "manual") == 30
    with pytest.raises(HTTPException, match="ne radi odabranog dana"):
        validate_appointment_payload(db, date(2026, 7, 6), time(10), time(10, 30), provider.id, provider_room.id, "scheduled", "manual")


@pytest.mark.parametrize(("staff_role", "email"), [("nurse", "sestra@example.hr"), ("secretary", "tajnica@example.hr")])
def test_create_non_physician_staff_and_reject_as_appointment_provider(client, db, auth_setup, staff_role, email):
    headers = {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}
    clinic = client.post("/api/clinics", headers=headers, json={"name": f"Klinika {staff_role}"})
    response = client.post("/api/providers", headers=headers, json={
        "full_name": "Test osoblje",
        "specialty": None,
        "email": email,
        "staff_role": staff_role,
        "clinic_id": clinic.json()["id"],
        "work_start": "08:00",
        "work_end": "16:00",
    })
    assert response.status_code == 200
    assert response.json()["staff_role"] == staff_role

    provider = db.get(Provider, response.json()["id"])
    provider_room = room(db)
    with pytest.raises(HTTPException) as exc:
        validate_appointment_payload(db, date(2026, 7, 6), time(10, 0), time(10, 30), provider.id, provider_room.id, "scheduled", "manual")
    assert exc.value.status_code == 422
    assert "samo liječniku" in exc.value.detail


def test_filter_services_by_clinic_and_deactivate_with_audit(client, db, auth_setup):
    clinic_a = Clinic(name="Klinika A"); clinic_b = Clinic(name="Klinika B")
    service_a = Service(name="Usluga A", duration_minutes=40, price=75); service_b = Service(name="Usluga B", duration_minutes=20, price=35)
    room_a = Room(name="Soba A", clinic=clinic_a, allowed_services=[service_a]); room_b = Room(name="Soba B", clinic=clinic_b, allowed_services=[service_b])
    db.add_all([clinic_a, clinic_b, service_a, service_b, room_a, room_b]); db.commit()
    headers = {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}

    filtered = client.get(f"/api/services?clinic_id={clinic_a.id}", headers=headers)
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()] == [service_a.id]
    assert filtered.json()[0]["clinic_ids"] == [clinic_a.id]

    updated = client.patch(f"/api/services/{service_a.id}", headers=headers, json={"duration_minutes": 60, "price": "95.50", "room_ids": [room_a.id]})
    assert updated.status_code == 200
    assert updated.json()["duration_minutes"] == 60
    assert updated.json()["price"] == "95.50"
    assert updated.json()["room_ids"] == [room_a.id]
    assert updated.json()["clinic_ids"] == [clinic_a.id]
    invalid_duration = client.patch(f"/api/services/{service_a.id}", headers=headers, json={"duration_minutes": 55})
    assert invalid_duration.status_code == 422
    assert client.patch(f"/api/services/{service_a.id}", headers=headers, json={"room_ids": [999999]}).status_code == 422

    hidden = client.post(f"/api/services/{service_a.id}/visibility", headers=headers)
    assert hidden.status_code == 200
    assert hidden.json()["visible_in_catalog"] is False
    assert client.get(f"/api/services?clinic_id={clinic_a.id}", headers=headers).json() == []
    assert client.get(f"/api/services?clinic_id={clinic_a.id}&include_hidden=true", headers=headers).json()[0]["id"] == service_a.id

    removed = client.delete(f"/api/services/{service_a.id}", headers=headers)
    assert removed.status_code == 200
    assert removed.json()["active"] is False
    assert client.get("/api/services", headers=headers).json()[0]["id"] == service_b.id
    assert db.query(AuditLog).filter(AuditLog.entity_type == "Service", AuditLog.entity_id == service_a.id, AuditLog.action == "deactivate").one()
    assert db.query(AuditLog).filter(AuditLog.entity_type == "Service", AuditLog.entity_id == service_a.id, AuditLog.action == "update").one()


def test_hide_and_deactivate_clinic_and_room(client, db, auth_setup):
    clinic = Clinic(name="Resursna klinika"); room_item = Room(name="Resursna soba", clinic=clinic)
    db.add_all([clinic, room_item]); db.commit()
    headers = {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}
    assert client.post(f"/api/rooms/{room_item.id}/visibility", headers=headers).json()["visible_in_catalog"] is False
    assert all(item["id"] != room_item.id for item in client.get("/api/rooms", headers=headers).json())
    assert any(item["id"] == room_item.id for item in client.get("/api/rooms?include_hidden=true", headers=headers).json())
    assert client.post(f"/api/clinics/{clinic.id}/visibility", headers=headers).json()["visible_in_catalog"] is False
    assert all(item["id"] != clinic.id for item in client.get("/api/clinics", headers=headers).json())
    assert client.delete(f"/api/clinics/{clinic.id}", headers=headers).status_code == 200
    db.refresh(room_item)
    assert room_item.active is False
    actions = {(item.entity_type, item.action) for item in db.query(AuditLog).all()}
    assert {("Room", "hide"), ("Clinic", "hide"), ("Clinic", "deactivate")}.issubset(actions)


def test_provider_can_be_marked_unavailable_and_deactivated(client, db, auth_setup):
    provider = Provider(full_name="Osoba za status", staff_role="physician")
    db.add(provider); db.commit(); headers = {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}
    schedule = {str(day): {"enabled": day in {0, 2, 4}, "start": "09:00", "end": "17:00"} for day in range(7)}
    schedule_response = client.patch(f"/api/providers/{provider.id}/schedule", headers=headers, json={"weekly_working_hours": schedule})
    assert schedule_response.status_code == 200
    assert schedule_response.json()["weekly_working_hours"]["2"]["start"] == "09:00"
    assert schedule_response.json()["work_start"] == "09:00:00"
    clinic_day = {**schedule, "0": {"enabled": True, "start": "07:00", "end": "20:00"}}
    assert client.patch(f"/api/providers/{provider.id}/schedule", headers=headers, json={"weekly_working_hours": clinic_day}).status_code == 200
    outside_clinic_hours = {**schedule, "0": {"enabled": True, "start": "06:59", "end": "20:00"}}
    assert client.patch(f"/api/providers/{provider.id}/schedule", headers=headers, json={"weekly_working_hours": outside_clinic_hours}).status_code == 422
    invalid = {**schedule, "0": {"enabled": True, "start": "20:00", "end": "07:00"}}
    assert client.patch(f"/api/providers/{provider.id}/schedule", headers=headers, json={"weekly_working_hours": invalid}).status_code == 422
    hidden = client.post(f"/api/providers/{provider.id}/availability", headers=headers)
    assert hidden.status_code == 200 and hidden.json()["available_for_work"] is False
    assert all(item["id"] != provider.id for item in client.get("/api/providers", headers=headers).json())
    assert any(item["id"] == provider.id for item in client.get("/api/providers?include_hidden=true", headers=headers).json())
    removed = client.delete(f"/api/providers/{provider.id}", headers=headers)
    assert removed.status_code == 200 and removed.json()["active"] is False
    actions = {item.action for item in db.query(AuditLog).filter(AuditLog.entity_type == "Provider", AuditLog.entity_id == provider.id)}
    assert {"schedule_update", "unavailable", "deactivate"}.issubset(actions)
