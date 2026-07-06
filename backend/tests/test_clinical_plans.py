from app.models.domain import AuditLog, ClinicalEpisode
from tests.conftest import login_token
from tests.factories import appointment, clinical_plan, episode, patient, provider, room, service


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def test_generate_plan_does_not_update_episode_until_confirmed(client, db, auth_setup):
    p = patient(db)
    pr = provider(db)
    ep = episode(db, patient_obj=p, provider_obj=pr)
    original_status = ep.status
    headers = auth_headers(client)

    response = client.post(
        f"/api/episodes/{ep.id}/clinical-plans/generate",
        headers=headers,
        json={
            "procedure_type": "Gastroskopija",
            "findings": "Ucinjena biopsija",
            "pathology_ordered": True,
            "physician_conclusion": "Cekati PH nalaz.",
            "episode_goal": "Razjasniti tegobe",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "ai_suggestion"
    assert payload["status"] == "draft"
    assert payload["physician_confirmed"] is False
    assert payload["next_action"] == "wait_for_pathology"
    assert payload["physician_conclusion"] == "Cekati PH nalaz."
    db.expire(ep)
    assert db.get(ClinicalEpisode, ep.id).status == original_status


def test_confirm_plan_updates_episode_and_writes_audit(client, db, auth_setup):
    p = patient(db)
    pr = provider(db)
    ep = episode(db, patient_obj=p, provider_obj=pr)
    plan = clinical_plan(db, episode_obj=ep)
    headers = auth_headers(client)

    response = client.post(f"/api/clinical-plans/{plan.id}/confirm", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "active"
    assert response.json()["physician_confirmed"] is True
    db.expire(ep)
    updated_episode = db.get(ClinicalEpisode, ep.id)
    assert updated_episode.status == "waiting"
    assert updated_episode.priority == "important"
    actions = [log.action for log in db.query(AuditLog).all()]
    assert "ai_plan_confirmed" in actions
    assert "update" in actions

    repeated = client.post(f"/api/clinical-plans/{plan.id}/confirm", headers=headers)
    assert repeated.status_code == 200
    assert repeated.json()["id"] == plan.id


def test_edit_and_reject_plan_keep_episode_unchanged(client, db, auth_setup):
    p = patient(db)
    pr = provider(db)
    ep = episode(db, patient_obj=p, provider_obj=pr)
    plan = clinical_plan(db, episode_obj=ep)
    headers = auth_headers(client)

    edited = client.patch(f"/api/clinical-plans/{plan.id}", headers=headers, json={"next_action": "follow_up_visit", "rationale": "Rucno uredeno"})
    rejected = client.post(f"/api/clinical-plans/{plan.id}/reject", headers=headers)

    assert edited.status_code == 200
    assert edited.json()["source"] == "physician"
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "cancelled"
    db.expire(ep)
    assert db.get(ClinicalEpisode, ep.id).status == "active"


def test_reject_plan_cannot_be_confirmed(client, db, auth_setup):
    ep = episode(db)
    plan = clinical_plan(db, episode_obj=ep, status="cancelled")
    headers = auth_headers(client)

    response = client.post(f"/api/clinical-plans/{plan.id}/confirm", headers=headers)

    assert response.status_code == 422


def test_invalid_plan_values_are_rejected(client, db, auth_setup):
    ep = episode(db)
    plan = clinical_plan(db, episode_obj=ep)
    headers = auth_headers(client)

    bad_status = client.patch(f"/api/clinical-plans/{plan.id}", headers=headers, json={"proposed_episode_status": "diagnosed"})
    bad_action = client.patch(f"/api/clinical-plans/{plan.id}", headers=headers, json={"next_action": "invent_diagnosis"})
    bad_priority = client.patch(f"/api/clinical-plans/{plan.id}", headers=headers, json={"priority": "whatever"})

    assert bad_status.status_code == 422
    assert bad_action.status_code == 422
    assert bad_priority.status_code == 422


def test_new_ai_suggestion_supersedes_previous_pending_plan(client, db, auth_setup):
    ep = episode(db)
    first = clinical_plan(db, episode_obj=ep)
    headers = auth_headers(client)

    generated = client.post(f"/api/episodes/{ep.id}/clinical-plans/generate", headers=headers, json={"physician_conclusion": "Cekati patologiju.", "pathology_ordered": True})
    plans = client.get(f"/api/episodes/{ep.id}/clinical-plans", headers=headers)

    assert generated.status_code == 200
    db.expire(first)
    assert first.status == "cancelled"
    pending = [plan for plan in plans.json() if not plan["physician_confirmed"] and plan["status"] in {"draft", "waiting"}]
    assert len(pending) == 1
    assert pending[0]["id"] == generated.json()["id"]


def test_completed_plan_sets_episode_end_date(client, db, auth_setup):
    ep = episode(db)
    plan = clinical_plan(db, episode_obj=ep)
    headers = auth_headers(client)

    edited = client.patch(f"/api/clinical-plans/{plan.id}", headers=headers, json={"proposed_episode_status": "completed", "next_action": "episode_completed"})
    confirmed = client.post(f"/api/clinical-plans/{plan.id}/confirm", headers=headers)

    assert edited.status_code == 200
    assert confirmed.status_code == 200
    db.expire(ep)
    updated = db.get(ClinicalEpisode, ep.id)
    assert updated.status == "completed"
    assert updated.end_date is not None


def test_episode_plan_lists_active_and_timeline(client, db, auth_setup):
    p = patient(db)
    pr = provider(db)
    rm = room(db)
    sv = service(db)
    ep = episode(db, patient_obj=p, provider_obj=pr)
    appt = appointment(db, patient_obj=p, provider_obj=pr, room_obj=rm, service_obj=sv)
    appt.episode_id = ep.id
    db.commit()
    headers = auth_headers(client)

    generated = client.post(
        f"/api/episodes/{ep.id}/clinical-plans/generate",
        headers=headers,
        json={"appointment_id": appt.id, "procedure_type": "Kolonoskopija", "pathology_ordered": True, "physician_conclusion": "Cekati patologiju."},
    )
    confirmed = client.post(f"/api/clinical-plans/{generated.json()['id']}/confirm", headers=headers)
    plans = client.get(f"/api/episodes/{ep.id}/clinical-plans", headers=headers)
    active = client.get(f"/api/episodes/{ep.id}/clinical-plans/active", headers=headers)
    timeline = client.get(f"/api/episodes/{ep.id}/clinical-timeline", headers=headers)

    assert generated.status_code == 200
    assert confirmed.status_code == 200
    assert plans.status_code == 200
    assert active.status_code == 200
    assert active.json()["id"] == generated.json()["id"]
    assert timeline.status_code == 200
    assert any(item["action"] == "ai_plan_generated" for item in timeline.json())
    assert any(item["action"] == "ai_plan_confirmed" for item in timeline.json())
    assert any(item["source"] == "AI Suggested" for item in timeline.json())
    assert any(item["source"] == "Human Confirmed" for item in timeline.json())


def test_generate_rejects_appointment_from_another_episode(client, db, auth_setup):
    p = patient(db)
    other = patient(db, first_name="Other")
    pr = provider(db)
    rm = room(db)
    sv = service(db)
    ep = episode(db, patient_obj=p, provider_obj=pr)
    other_ep = episode(db, patient_obj=other, provider_obj=pr, title="Other")
    appt = appointment(db, patient_obj=other, provider_obj=pr, room_obj=rm, service_obj=sv)
    appt.episode_id = other_ep.id
    db.commit()
    headers = auth_headers(client)

    response = client.post(f"/api/episodes/{ep.id}/clinical-plans/generate", headers=headers, json={"appointment_id": appt.id})

    assert response.status_code == 422
