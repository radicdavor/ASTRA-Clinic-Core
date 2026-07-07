from datetime import datetime

from app.models.domain import AuditLog, ClinicalEpisode, ClinicalPlan, PatientClinicalSummaryRecord
from tests.conftest import login_token
from tests.factories import appointment, clinical_document, episode, patient


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def preview(client, appointment_id, headers):
    return client.get(f"/api/appointments/{appointment_id}/clinical-readiness-preview", headers=headers)


def test_preview_is_read_only_and_does_not_change_appointment_status(client, db, auth_setup):
    appt = appointment(db, status="scheduled")
    original_status = appt.status
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    body = response.json()
    assert body["is_preview"] is True
    assert body["appointment_id"] == appt.id
    db.expire(appt)
    assert appt.status == original_status
    assert db.query(AuditLog).count() == 0


def test_preview_does_not_create_tasks_episodes_or_clinical_plans(client, db, auth_setup):
    appt = appointment(db)
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count


def test_appointment_without_episode_still_returns_preview(client, db, auth_setup):
    appt = appointment(db)
    assert appt.episode_id is None
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    assert response.json()["is_preview"] is True


def test_preview_is_separate_from_operational_readiness(client, db, auth_setup):
    appt = appointment(db)
    headers = auth_headers(client)

    clinical = preview(client, appt.id, headers)
    operational = client.get("/api/readiness", headers=headers)

    assert clinical.status_code == 200
    assert operational.status_code == 200
    assert "items" in clinical.json()
    assert "checks" in operational.json()
    assert all(check["key"] != "clinical_readiness" for check in operational.json()["checks"])


def test_unreviewed_ai_extraction_is_not_used_as_preview_source(client, db, auth_setup):
    appt = appointment(db)
    doc = clinical_document(db, appt.patient, physician_reviewed=False)
    doc.recommendations = ["Postoji otvoreno pitanje koje ceka pregled"]
    db.commit()
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    body = response.json()
    assert all(item.get("source_ref") != f"ClinicalDocument:{doc.id}" for item in body["items"])
    assert not any(item["category"] == "open_question" for item in body["items"])


def test_reviewed_open_questions_appear_as_warnings_not_blockers_or_tasks(client, db, auth_setup):
    appt = appointment(db)
    doc = clinical_document(db, appt.patient, physician_reviewed=True)
    doc.recommendations = ["Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled"]
    db.commit()
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    open_items = [item for item in response.json()["items"] if item["category"] == "open_question"]
    assert len(open_items) == 1
    assert open_items[0]["status"] == "needs_physician_review"
    assert open_items[0]["severity"] == "warning"
    assert open_items[0]["blocking"] is False
    assert "zadatak" in open_items[0]["suggested_action"].lower()


def test_patient_clinical_summary_alone_is_not_used_as_source_of_truth(client, db, auth_setup):
    appt = appointment(db)
    db.add(
        PatientClinicalSummaryRecord(
            patient_id=appt.patient_id,
            summary_text="Pregledani sazetak bez izvora.",
            open_items=["Sazetak ne smije postati readiness izvor"],
            status="reviewed",
            generated_by="physician",
            reviewed_by=1,
            reviewed_at=datetime(2026, 7, 7),
        )
    )
    db.commit()
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    labels = [item["label"] for item in response.json()["items"]]
    assert "Sazetak ne smije postati readiness izvor" not in labels


def test_missing_service_returns_blocking_item_but_does_not_update_appointment(client, db, auth_setup):
    appt = appointment(db)
    appt.service_id = None
    db.commit()
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert any(item["key"] == "missing_service" and item["blocking"] for item in body["items"])
    db.expire(appt)
    assert appt.service_id is None


def test_missing_template_returns_limitation_not_server_error(client, db, auth_setup):
    appt = appointment(db)
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    assert "Nema definiranog clinical readiness templatea za ovu uslugu." in response.json()["limitations"]
