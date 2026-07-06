from datetime import date

from app.models.domain import AuditLog
from tests.conftest import login_token
from tests.factories import appointment, episode, patient, provider, room, service


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def test_create_update_close_episode(client, db, auth_setup):
    p = patient(db)
    pr = provider(db)
    headers = auth_headers(client)

    created = client.post(
        "/api/episodes",
        headers=headers,
        json={
            "patient_id": p.id,
            "title": "GERB pracenje",
            "episode_type": "gastroenterology",
            "status": "active",
            "priority": "routine",
            "start_date": "2026-07-05",
            "owner_provider_id": pr.id,
            "summary": "Demo summary",
        },
    )

    assert created.status_code == 200
    episode_id = created.json()["id"]
    assert created.json()["patient"]["id"] == p.id

    updated = client.patch(f"/api/episodes/{episode_id}", headers=headers, json={"priority": "urgent", "summary": "Updated"})
    assert updated.status_code == 200
    assert updated.json()["priority"] == "urgent"

    closed = client.post(f"/api/episodes/{episode_id}/close", headers=headers)
    assert closed.status_code == 200
    assert closed.json()["status"] == "completed"
    assert closed.json()["end_date"] == str(date.today())

    actions = [log.action for log in db.query(AuditLog).filter(AuditLog.entity_type == "ClinicalEpisode").all()]
    assert "create" in actions
    assert "update" in actions
    assert "close" in actions


def test_list_patient_episodes_and_episode_appointments(client, db, auth_setup):
    p = patient(db)
    pr = provider(db)
    rm = room(db)
    sv = service(db)
    ep = episode(db, patient_obj=p, provider_obj=pr)
    appt = appointment(db, patient_obj=p, provider_obj=pr, room_obj=rm, service_obj=sv)
    appt.episode_id = ep.id
    db.commit()
    headers = auth_headers(client)

    patient_episodes = client.get(f"/api/patients/{p.id}/episodes", headers=headers)
    episode_appointments = client.get(f"/api/episodes/{ep.id}/appointments", headers=headers)

    assert patient_episodes.status_code == 200
    assert patient_episodes.json()[0]["id"] == ep.id
    assert episode_appointments.status_code == 200
    assert episode_appointments.json()[0]["id"] == appt.id


def test_create_appointment_with_episode_and_reject_cross_patient(client, db, auth_setup):
    p = patient(db)
    other = patient(db, first_name="Other")
    pr = provider(db)
    rm = room(db)
    sv = service(db)
    ep = episode(db, patient_obj=p, provider_obj=pr)
    other_ep = episode(db, patient_obj=other, provider_obj=pr, title="Other episode")
    headers = auth_headers(client)

    ok_response = client.post(
        "/api/appointments",
        headers=headers,
        json={
            "patient_id": p.id,
            "service_id": sv.id,
            "provider_id": pr.id,
            "room_id": rm.id,
            "episode_id": ep.id,
            "date": "2026-07-05",
            "start_time": "11:00",
            "end_time": "11:30",
            "duration_minutes": 30,
            "status": "scheduled",
            "source": "manual",
        },
    )

    rejected = client.post(
        "/api/appointments",
        headers=headers,
        json={
            "patient_id": p.id,
            "service_id": sv.id,
            "provider_id": pr.id,
            "room_id": rm.id,
            "episode_id": other_ep.id,
            "date": "2026-07-05",
            "start_time": "12:00",
            "end_time": "12:30",
            "duration_minutes": 30,
            "status": "scheduled",
            "source": "manual",
        },
    )

    assert ok_response.status_code == 200
    assert ok_response.json()["episode"]["id"] == ep.id
    assert rejected.status_code == 422


def test_readiness_includes_clinical_episodes(client, auth_setup):
    headers = auth_headers(client)

    response = client.get("/api/readiness", headers=headers)

    assert response.status_code == 200
    assert any(check["key"] == "clinical_episodes" and check["target_path"] == "/episodes" for check in response.json()["checks"])
