from datetime import date, time

from app.models.domain import JourneyActivity, PatientJourney, ProcedureIntervention
from tests.conftest import login_token
from tests.factories import appointment, provider, room, service


def headers(client):
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def canonical_journey(client, db):
    anchor = appointment(db)
    response = client.post(
        "/api/patient-journeys",
        headers=headers(client),
        json={"appointment_id": anchor.id, "intake_channel": "manual", "initial_stage": "booked"},
    )
    assert response.status_code == 200
    return response.json(), anchor


def activity_payload(db, *, activity_key="second", day=date(2026, 7, 6), start=time(9, 30), end=time(10, 0)):
    suffix = f"{activity_key}-{day.isoformat()}-{start.isoformat()}"
    return {
        "service_id": service(db, name=f"Service {suffix}").id,
        "provider_id": provider(db, name=f"dr. {suffix}").id,
        "room_id": room(db, name=f"Room {suffix}").id,
        "date": day.isoformat(),
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "activity_key": activity_key,
        "activity_kind": "diagnostic_procedure",
        "specialty_key": "gastroenterology",
        "required": True,
    }


def test_journey_starts_with_one_primary_activity(client, db, auth_setup):
    journey, anchor = canonical_journey(client, db)
    assert len(journey["activities"]) == 1
    assert journey["activities"][0]["activity_key"] == "primary"
    assert journey["activities"][0]["appointment_id"] == anchor.id


def test_adds_multiple_sequential_services_to_one_physical_arrival(client, db, auth_setup):
    journey, _ = canonical_journey(client, db)
    second = client.post(
        f"/api/patient-journeys/{journey['id']}/activities",
        headers=headers(client),
        json=activity_payload(db),
    )
    assert second.status_code == 201
    third = client.post(
        f"/api/patient-journeys/{journey['id']}/activities",
        headers=headers(client),
        json=activity_payload(db, activity_key="third", start=time(10), end=time(10, 30)),
    )
    assert third.status_code == 201
    listed = client.get(f"/api/patient-journeys/{journey['id']}/activities", headers=headers(client))
    assert listed.status_code == 200
    assert [item["activity_key"] for item in listed.json()] == ["primary", "second", "third"]
    assert {item["journey_id"] for item in listed.json()} == {journey["id"]}


def test_rejects_second_date_duplicate_key_and_patient_overlap(client, db, auth_setup):
    journey, _ = canonical_journey(client, db)
    wrong_day = client.post(
        f"/api/patient-journeys/{journey['id']}/activities",
        headers=headers(client),
        json=activity_payload(db, day=date(2026, 7, 7)),
    )
    assert wrong_day.status_code == 409

    created = client.post(
        f"/api/patient-journeys/{journey['id']}/activities",
        headers=headers(client),
        json=activity_payload(db),
    )
    assert created.status_code == 201
    duplicate = client.post(
        f"/api/patient-journeys/{journey['id']}/activities",
        headers=headers(client),
        json=activity_payload(db, start=time(10), end=time(10, 30)),
    )
    assert duplicate.status_code == 409
    overlap = client.post(
        f"/api/patient-journeys/{journey['id']}/activities",
        headers=headers(client),
        json=activity_payload(db, activity_key="overlap", start=time(9, 45), end=time(10, 15)),
    )
    assert overlap.status_code == 409
    assert "pacijent" in overlap.json()["detail"]


def test_activity_transition_is_explicit_and_audited(client, db, auth_setup):
    journey, _ = canonical_journey(client, db)
    created = client.post(
        f"/api/patient-journeys/{journey['id']}/activities",
        headers=headers(client),
        json=activity_payload(db),
    ).json()
    blocked = client.post(
        f"/api/patient-journeys/{journey['id']}/activities/{created['id']}/transition",
        headers=headers(client),
        json={"target_status": "ready"},
    )
    assert blocked.status_code == 409
    activity = db.get(JourneyActivity, created["id"])
    activity.form_resolution_status = "not_required"
    db.flush()
    ready = client.post(
        f"/api/patient-journeys/{journey['id']}/activities/{created['id']}/transition",
        headers=headers(client),
        json={"target_status": "ready"},
    )
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_biopsy_activity_requires_resolved_complication_and_labeled_specimen(client, db, auth_setup):
    journey, _ = canonical_journey(client, db)
    activity = db.get(JourneyActivity, journey["activities"][0]["id"])
    activity.form_resolution_status = "not_required"
    visit = db.get(PatientJourney, journey["id"])
    visit.check_in_status = "ready"; visit.current_stage = "ready_for_clinician"
    db.commit()
    url = f"/api/patient-journeys/{journey['id']}/activities/{activity.id}"
    assert client.post(f"{url}/transition", headers=headers(client), json={"target_status": "ready"}).status_code == 200
    assert client.post(f"{url}/transition", headers=headers(client), json={"target_status": "in_progress"}).status_code == 200
    intervention = client.post(f"{url}/interventions", headers=headers(client), json={"intervention_type": "biopsy", "anatomical_site": "Sintetičko mjesto", "count": 1, "retrieval_status": "collected"}).json()
    unresolved = client.post(f"{url}/transition", headers=headers(client), json={"target_status": "completed"})
    assert unresolved.status_code == 409 and "komplikacije" in unresolved.json()["detail"]
    db.get(ProcedureIntervention, intervention["id"]).complication = "Nema"
    db.commit()
    missing = client.post(f"{url}/transition", headers=headers(client), json={"target_status": "completed"})
    assert missing.status_code == 409 and "uzorak" in missing.json()["detail"]
    case = client.post(f"{url}/pathology-case", headers=headers(client), json={"specimens": [{"specimen_label": "A1", "anatomical_site": "Sintetičko mjesto", "specimen_type": "biopsy", "source_intervention_id": intervention["id"], "collection_time": "2026-07-06T09:20:00Z"}]})
    assert case.status_code == 201
    completed = client.post(f"{url}/transition", headers=headers(client), json={"target_status": "completed"})
    assert completed.status_code == 200 and completed.json()["status"] == "completed"
