from app.models.domain import AuditLog
from tests.conftest import login_token
from tests.factories import episode, patient, provider


def headers(client, email="admin@test.local"):
    return {"Authorization": f"Bearer {login_token(client, email)}"}


def test_workflow_task_template_checklist_and_completion(client, db, auth_setup):
    p = patient(db)
    pr = provider(db)
    ep = episode(db, patient_obj=p, provider_obj=pr)
    auth = headers(client)
    template = client.post("/api/workflow-templates", headers=auth, json={"key": "result-review", "name": "Pregled nalaza", "default_priority": "important", "checklist_items": ["Otvori izvor", "Evidentiraj pregled"]})
    assert template.status_code == 200

    created = client.post("/api/workflow-tasks", headers=auth, json={"title": "Pregledaj patologiju", "patient_id": p.id, "episode_id": ep.id, "assignee_provider_id": pr.id, "template_id": template.json()["id"]})
    assert created.status_code == 200
    body = created.json()
    assert body["priority"] == "important"
    assert len(body["checklist"]) == 2
    task_id = body["id"]

    blocked = client.patch(f"/api/workflow-tasks/{task_id}", headers=auth, json={"status": "completed"})
    assert blocked.status_code == 422
    for item in body["checklist"]:
        response = client.post(f"/api/workflow-tasks/{task_id}/checklist/{item['id']}/toggle", headers=auth)
        assert response.status_code == 200
    completed = client.patch(f"/api/workflow-tasks/{task_id}", headers=auth, json={"status": "completed"})
    assert completed.status_code == 200
    assert completed.json()["completed_at"] is not None
    actions = [entry.action for entry in db.query(AuditLog).filter(AuditLog.entity_type == "WorkflowTask").all()]
    assert {"create", "checklist_completed", "complete"}.issubset(actions)


def test_workflow_rejects_cross_patient_episode_and_enforces_permissions(client, db, auth_setup):
    p = patient(db)
    other = patient(db, first_name="Drugi")
    pr = provider(db)
    foreign_episode = episode(db, patient_obj=other, provider_obj=pr)
    rejected = client.post("/api/workflow-tasks", headers=headers(client), json={"title": "Pogresna veza", "patient_id": p.id, "episode_id": foreign_episode.id})
    assert rejected.status_code == 422
    forbidden = client.get("/api/workflow-tasks", headers=headers(client, "limited@test.local"))
    assert forbidden.status_code == 403


def test_patient_and_episode_task_views(client, db, auth_setup):
    p = patient(db)
    pr = provider(db)
    ep = episode(db, patient_obj=p, provider_obj=pr)
    auth = headers(client)
    created = client.post("/api/workflow-tasks", headers=auth, json={"title": "Organiziraj kontrolu", "patient_id": p.id, "episode_id": ep.id, "responsible_role": "receptionist"})
    assert created.status_code == 200
    assert client.get(f"/api/patients/{p.id}/workflow-tasks", headers=auth).json()[0]["id"] == created.json()["id"]
    assert client.get(f"/api/episodes/{ep.id}/workflow-tasks", headers=auth).json()[0]["id"] == created.json()["id"]
