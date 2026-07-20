from datetime import timedelta

from app.core.security import hash_password
from app.models.domain import AuditLog, JourneyActivity, JourneyBlocker, JourneyEvent, Permission, Role, User
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


def add_second_activity(db, journey_detail):
    first = db.get(JourneyActivity, journey_detail["activities"][0]["id"])
    second = JourneyActivity(
        journey_id=first.journey_id,
        appointment_id=None,
        service_id=first.service_id,
        activity_key="colonoscopy",
        activity_kind="procedure",
        specialty_key=first.specialty_key,
        clinic_id=first.clinic_id,
        primary_provider_id=first.primary_provider_id,
        room_id=first.room_id,
        sequence=2,
        required=True,
        planned_start=first.planned_end,
        planned_end=first.planned_end + timedelta(minutes=30),
        status="ready",
        form_resolution_status="not_required",
    )
    db.add(second)
    db.flush()
    return first, second


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
    detail_before = client.get(f"/api/patient-journeys/{journey['id']}", headers=admin).json()
    activity_id = detail_before["activities"][0]["id"]
    reception = reception_headers(client, db)
    response = client.post(
        f"/api/patient-journeys/{journey['id']}/check-in/complete-reception",
        headers=reception,
        json={
            "items": [
                {"item_key": "fasting_6h", "note": "Post od 6 sati nije potvrđen.", "details": {"last_intake_timing": "2–4 sata", "intake_type": "kava s mlijekom"}, "activity_ids": [activity_id]},
                {"item_key": "pacemaker", "note": "Pacijent navodi elektrostimulator."},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    response_items = {item["item_key"]: item for item in response.json()["items"]}
    assert response_items["patient_data_confirmed"]["state"] == "confirmed"
    assert response_items["consent_status"]["state"] == "not_applicable"
    assert response_items["fasting_6h"]["state"] == "requires_clinician_review"
    assert response_items["fasting_6h"]["details_json"]["intake_type"] == "kava s mlijekom"
    assert response_items["fasting_6h"]["activity_ids_json"] == [activity_id]
    assert response_items["pacemaker"]["state"] == "requires_clinician_review"
    detail = client.get(f"/api/patient-journeys/{journey['id']}", headers=admin).json()
    assert detail["current_stage"] == "ready_for_clinician"
    assert detail["check_in_status"] == "ready"
    assert db.query(JourneyBlocker).filter_by(journey_id=journey["id"], status="open").count() == 0
    dashboard = client.get("/api/dashboard/day?selected_date=2026-07-06", headers=admin).json()
    row = next(item for item in dashboard["rows"] if item["journey_id"] == journey["id"])
    assert row["reception_warning"] is True
    assert "Pacijent navodi elektrostimulator." in row["reception_warning_details"]


def test_medical_disposition_is_separate_from_reception_completion_and_requires_permission(client, db, auth_setup):
    journey, admin = ready_journey(client, db)
    client.post(f"/api/patient-journeys/{journey['id']}/check-in", headers=admin)
    reception = reception_headers(client, db)
    completed = client.post(
        f"/api/patient-journeys/{journey['id']}/check-in/complete-reception",
        headers=reception,
        json={"items": [{"item_key": "fasting_6h", "note": "Post od 6 sati nije potvrđen."}]},
    ).json()
    item = next(item for item in completed["items"] if item["item_key"] == "fasting_6h")

    forbidden = client.post(
        f"/api/patient-journeys/{journey['id']}/check-in/items/{item['id']}/medical-disposition",
        headers=reception,
        json={"disposition": "proceed", "note": "Medicinska odluka."},
    )
    assert forbidden.status_code == 403

    response = client.post(
        f"/api/patient-journeys/{journey['id']}/check-in/items/{item['id']}/medical-disposition",
        headers=admin,
        json={"disposition": "proceed", "note": "Pregledano prije zahvata."},
    )
    assert response.status_code == 200
    updated = next(item for item in response.json()["items"] if item["item_key"] == "fasting_6h")
    assert updated["state"] == "confirmed"
    assert updated["medical_disposition"] == "proceed"
    assert updated["medical_disposition_note"] == "Pregledano prije zahvata."
    detail = client.get(f"/api/patient-journeys/{journey['id']}", headers=admin).json()
    assert detail["check_in_status"] == "ready"


def test_reception_completion_is_idempotent_and_conflicts_on_changed_payload(client, db, auth_setup):
    journey, admin = ready_journey(client, db)
    client.post(f"/api/patient-journeys/{journey['id']}/check-in", headers=admin)
    reception = reception_headers(client, db)
    payload = {"idempotency_key": "reception-demo-key", "items": [{"item_key": "fasting_6h", "note": "Post nije potvrđen."}]}

    first = client.post(f"/api/patient-journeys/{journey['id']}/check-in/complete-reception", headers=reception, json=payload)
    second = client.post(f"/api/patient-journeys/{journey['id']}/check-in/complete-reception", headers=reception, json=payload)
    conflict = client.post(
        f"/api/patient-journeys/{journey['id']}/check-in/complete-reception",
        headers=reception,
        json={"idempotency_key": "reception-demo-key", "items": [{"item_key": "fasting_6h", "note": "Drugi sadržaj."}]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "idempotency_conflict"
    assert db.query(JourneyEvent).filter_by(journey_id=journey["id"], event_type="check_in_reception_completed").count() == 1
    assert db.query(AuditLog).filter_by(entity_type="PatientJourney", entity_id=journey["id"], action="checkin_reception_completed").count() == 1


def test_shared_red_flag_can_reference_multiple_activities_without_global_block(client, db, auth_setup):
    journey, admin = ready_journey(client, db)
    detail_before = client.get(f"/api/patient-journeys/{journey['id']}", headers=admin).json()
    first, second = add_second_activity(db, detail_before)
    db.commit()
    client.post(f"/api/patient-journeys/{journey['id']}/check-in", headers=admin)
    reception = reception_headers(client, db)

    response = client.post(
        f"/api/patient-journeys/{journey['id']}/check-in/complete-reception",
        headers=reception,
        json={"idempotency_key": "shared-red-flag-key", "items": [{"item_key": "sedation_escort", "note": "Pratnja nije potvrđena.", "activity_ids": [first.id, second.id]}]},
    )

    assert response.status_code == 200
    item = next(item for item in response.json()["items"] if item["item_key"] == "sedation_escort")
    assert item["state"] == "requires_clinician_review"
    assert item["activity_ids_json"] == [first.id, second.id]
    detail = client.get(f"/api/patient-journeys/{journey['id']}", headers=admin).json()
    assert detail["current_stage"] == "ready_for_clinician"
    assert detail["check_in_status"] == "ready"
    assert db.query(JourneyBlocker).filter_by(journey_id=journey["id"], status="open").count() == 0


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
