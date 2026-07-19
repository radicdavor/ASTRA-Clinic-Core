from app.core.security import hash_password
from app.models.domain import AuditLog, JourneyBlocker, Permission, Role, User
from tests.conftest import login_token
from tests.factories import appointment


def admin_headers(client):
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def ready_journey(client, db):
    appt = appointment(db)
    headers = admin_headers(client)
    journey = client.post("/api/patient-journeys", headers=headers, json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"}).json()
    response = client.post(f"/api/patient-journeys/{journey['id']}/transition", headers=headers, json={"target_stage": "ready_for_arrival"})
    assert response.status_code == 200
    return journey, headers


def reception_headers(client, db):
    permissions = db.query(Permission).filter(Permission.name.in_(["journey.read", "checkin.update"])).all()
    role = Role(name="synthetic_reception", description="Synthetic", permissions=permissions)
    user = User(email="reception@test.local", full_name="Synthetic Reception", password_hash=hash_password("secret"), role=role)
    db.add(user)
    db.flush()
    return {"Authorization": f"Bearer {login_token(client, 'reception@test.local')}"}


def test_start_check_in_records_arrival_and_structured_items(client, db, auth_setup):
    journey, headers = ready_journey(client, db)
    dashboard = client.get("/api/dashboard/day?selected_date=2026-07-06", headers=headers).json()
    row = next(item for item in dashboard["rows"] if item["journey_id"] == journey["id"])
    assert row["allowed_actions"] == ["open_check_in"]
    response = client.post(f"/api/patient-journeys/{journey['id']}/check-in", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_review" and body["arrived_at"]
    assert {item["category"] for item in body["items"]} == {"identity", "documents", "preparation", "preconditions"}
    assert "patient_data_confirmed" in {item["item_key"] for item in body["items"]}
    assert "fasting_6h" in {item["item_key"] for item in body["items"]}
    assert "pacemaker" in {item["item_key"] for item in body["items"]}
    detail = client.get(f"/api/patient-journeys/{journey['id']}", headers=headers).json()
    assert detail["current_stage"] == "check_in_review" and detail["check_in_status"] == "in_review"


def test_start_check_in_from_booked_patient_opens_reception(client, db, auth_setup):
    appt = appointment(db)
    headers = admin_headers(client)
    journey = client.post("/api/patient-journeys", headers=headers, json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"}).json()
    dashboard = client.get("/api/dashboard/day?selected_date=2026-07-06", headers=headers).json()
    row = next(item for item in dashboard["rows"] if item["journey_id"] == journey["id"])
    assert "open_check_in" in row["allowed_actions"]

    response = client.post(f"/api/patient-journeys/{journey['id']}/check-in", headers=headers)

    assert response.status_code == 200
    detail = client.get(f"/api/patient-journeys/{journey['id']}", headers=headers).json()
    assert detail["current_stage"] == "check_in_review"


def test_reception_complete_records_red_notes_but_sends_patient_to_clinician(client, db, auth_setup):
    journey, admin = ready_journey(client, db)
    client.post(f"/api/patient-journeys/{journey['id']}/check-in", headers=admin)
    reception = reception_headers(client, db)
    response = client.post(
        f"/api/patient-journeys/{journey['id']}/check-in/complete-reception",
        headers=reception,
        json={
            "items": [
                {"item_key": "fasting_6h", "note": "Post od 6 sati nije potvrđen."},
                {"item_key": "pacemaker", "note": "Pacijent navodi elektrostimulator."},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    detail = client.get(f"/api/patient-journeys/{journey['id']}", headers=admin).json()
    assert detail["current_stage"] == "ready_for_clinician"
    assert db.query(JourneyBlocker).filter_by(journey_id=journey["id"], status="open").count() == 0
    dashboard = client.get("/api/dashboard/day?selected_date=2026-07-06", headers=admin).json()
    row = next(item for item in dashboard["rows"] if item["journey_id"] == journey["id"])
    assert row["reception_warning"] is True
    assert "Pacijent navodi elektrostimulator." in row["reception_warning_details"]


def test_reception_confirms_administrative_items_with_one_audited_action(client, db, auth_setup):
    journey, admin = ready_journey(client, db)
    client.post(f"/api/patient-journeys/{journey['id']}/check-in", headers=admin)
    reception = reception_headers(client, db)
    response = client.post(f"/api/patient-journeys/{journey['id']}/check-in/confirm-administrative", headers=reception)
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["state"] == "confirmed" for item in items if item["item_key"] == "patient_data_confirmed")
    assert all(item["state"] == "not_confirmed" for item in items if item["item_key"] != "patient_data_confirmed")
    assert db.query(AuditLog).filter_by(entity_type="PatientJourney", entity_id=journey["id"], action="checkin_administrative_confirmed").count() == 1


def test_check_in_becomes_ready_only_after_every_item_is_human_resolved(client, db, auth_setup):
    journey, headers = ready_journey(client, db)
    checkin = client.post(f"/api/patient-journeys/{journey['id']}/check-in", headers=headers).json()
    latest = None
    for item in checkin["items"]:
        latest = client.patch(f"/api/patient-journeys/{journey['id']}/check-in/items/{item['id']}", headers=headers, json={"state": "not_applicable"})
        assert latest.status_code == 200
    assert latest.json()["status"] == "ready"
    detail = client.get(f"/api/patient-journeys/{journey['id']}", headers=headers).json()
    assert detail["current_stage"] == "ready_for_clinician" and detail["check_in_status"] == "ready"
