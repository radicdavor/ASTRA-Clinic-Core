from datetime import datetime

from app.models.domain import Appointment, AuditLog, ClinicalEpisode, ClinicalPlan, PatientClinicalSummaryRecord
from app.services.clinical_readiness_preview import build_clinical_readiness_preview
from tests.conftest import login_token
from tests.factories import appointment, clinical_document, episode, patient, service


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
    task_table_count = 1 if "tasks" in db.get_bind().dialect.get_table_names(db.connection()) else 0
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    assert task_table_count == 0
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


def test_missing_service_returns_blocking_item_without_db_write(db):
    p = patient(db)
    appt = Appointment(id=999, patient_id=p.id, service_id=None)

    response = build_clinical_readiness_preview(db, appt)

    assert response.status == "blocked"
    assert any(item.key == "missing_service" and item.blocking for item in response.items)
    assert appt.service_id is None
    assert db.query(AuditLog).count() == 0


def test_colonoscopy_service_selects_colonoscopy_template(client, db, auth_setup):
    colonoscopy = service(db, name="Kolonoskopija s mogucnosti polipektomije")
    appt = appointment(db, service_obj=colonoscopy)
    original_status = appt.status
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    body = response.json()
    assert "Koristi se demo/pilot template: Kolonoskopija." in body["limitations"]
    assert any(item["key"] == "template_colonoscopy_bowel_prep" for item in body["items"])
    assert any(item["key"] == "template_colonoscopy_polypectomy_materials" for item in body["items"])
    assert body["status"] != "blocked"
    assert all(item["blocking"] is False for item in body["items"] if item["key"].startswith("template_"))
    db.expire(appt)
    assert appt.status == original_status


def test_gastroscopy_service_selects_gastroscopy_template(client, db, auth_setup):
    gastroscopy = service(db, name="Gastroskopija uz sedaciju")
    appt = appointment(db, service_obj=gastroscopy)
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    body = response.json()
    assert "Koristi se demo/pilot template: Gastroskopija." in body["limitations"]
    assert any(item["key"] == "template_gastroscopy_fasting_check" for item in body["items"])
    assert any(item["key"] == "template_gastroscopy_sedation_escort" for item in body["items"])
    assert body["status"] != "blocked"
    assert all(item["blocking"] is False for item in body["items"] if item["key"].startswith("template_"))


def test_generic_service_falls_back_to_generic_template(client, db, auth_setup):
    generic = service(db, name="Kontrolni pregled")
    appt = appointment(db, service_obj=generic)
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    body = response.json()
    assert "Nema specificnog clinical readiness templatea za ovu uslugu; koristi se genericki preview." in body["limitations"]
    assert any(item["key"] == "template_generic_confirm_planned_service" for item in body["items"])
    assert any(item["key"] == "template_generic_confirm_consent_need" for item in body["items"])


def test_template_items_do_not_enforce_workflow(client, db, auth_setup):
    colonoscopy = service(db, name="Kolonoskopija")
    appt = appointment(db, service_obj=colonoscopy, status="scheduled")
    original_status = appt.status
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    body = response.json()
    template_items = [item for item in body["items"] if item["key"].startswith("template_")]
    assert template_items
    assert body["status"] != "blocked"
    assert all(item["blocking"] is False for item in template_items)
    assert all(item["audit_required"] is False for item in template_items)
    db.expire(appt)
    assert appt.status == original_status
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count


def test_unreviewed_ai_extraction_remains_excluded_with_service_templates(client, db, auth_setup):
    colonoscopy = service(db, name="Kolonoskopija")
    appt = appointment(db, service_obj=colonoscopy)
    doc = clinical_document(db, appt.patient, physician_reviewed=False)
    doc.recommendations = ["Postoji otvoreno pitanje iz nepregledanog AI prijedloga"]
    db.commit()
    headers = auth_headers(client)

    response = preview(client, appt.id, headers)

    assert response.status_code == 200
    body = response.json()
    assert all(item.get("source_ref") != f"ClinicalDocument:{doc.id}" for item in body["items"])
    assert not any(item["label"] == "Postoji otvoreno pitanje iz nepregledanog AI prijedloga" for item in body["items"])


def test_patient_clinical_summary_remains_excluded_with_service_templates(client, db, auth_setup):
    colonoscopy = service(db, name="Kolonoskopija")
    appt = appointment(db, service_obj=colonoscopy)
    db.add(
        PatientClinicalSummaryRecord(
            patient_id=appt.patient_id,
            summary_text="Pregledani sazetak bez izvora.",
            open_items=["Sazetak bez izvora ne smije uci u readiness preview"],
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
    assert "Sazetak bez izvora ne smije uci u readiness preview" not in labels
