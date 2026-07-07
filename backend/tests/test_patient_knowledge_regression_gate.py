from datetime import datetime

from app.models.domain import AuditLog, PatientClinicalSummaryRecord
from tests.conftest import login_token
from tests.factories import appointment, clinical_document, patient


KNOWLEDGE_CATEGORIES = [
    "known_problems",
    "completed_procedures",
    "pathology",
    "laboratory",
    "imaging",
    "current_therapy",
    "open_questions",
    "latest_recommendations",
]


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def all_knowledge_items(summary_body):
    return [item for category in KNOWLEDGE_CATEGORIES for item in summary_body[category]]


def assert_no_official_knowledge(summary_body):
    assert summary_body["generated_from_reviewed_documents"] == 0
    assert all_knowledge_items(summary_body) == []


def test_gate_unreviewed_ai_never_official(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    generated = clinical_document(db, p, physician_reviewed=False)
    generated.ai_extraction_status = "generated"
    generated.key_findings = ["GERB/refluks naveden u dokumentu"]
    edited = clinical_document(db, p, physician_reviewed=False)
    edited.ai_extraction_status = "edited"
    edited.key_findings = ["H. pylori status naveden u dokumentu"]
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert_no_official_knowledge(summary.json())


def test_gate_reviewed_source_required_for_official_knowledge(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    reviewed = clinical_document(db, p, physician_reviewed=True)
    incompatible = clinical_document(db, p, physician_reviewed=True)
    incompatible.review_status = "needs_physician_review"
    missing_flag = clinical_document(db, p, physician_reviewed=False)
    missing_flag.review_status = "reviewed"
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["generated_from_reviewed_documents"] == 1
    assert {source["document_id"] for item in all_knowledge_items(body) for source in item["sources"]} == {reviewed.id}


def test_gate_summary_is_not_source_of_truth(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    record = PatientClinicalSummaryRecord(
        patient_id=p.id,
        summary_text="Pregledani sazetak bez source dokumenta.",
        known_conditions=["Summary ne stvara official fact"],
        key_findings=["Nalaz bez izvora"],
        open_items=["Otvoreno pitanje bez izvora"],
        risks=[],
        last_recommendations=["Preporuka bez izvora"],
        source_document_ids=[],
        status="reviewed",
        generated_by="physician",
        reviewed_by=1,
        reviewed_at=datetime(2026, 7, 6),
    )
    db.add(record)
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["reviewed_summary"]["id"] == record.id
    assert_no_official_knowledge(body)


def test_gate_open_questions_require_reviewed_source(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    reviewed = clinical_document(db, p, physician_reviewed=True)
    reviewed.key_findings = []
    reviewed.recommendations = ["Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled"]
    unreviewed = clinical_document(db, p, physician_reviewed=False)
    unreviewed.recommendations = ["Nepregledano otvoreno pitanje"]
    rejected = clinical_document(db, p, physician_reviewed=False)
    rejected.review_status = "rejected"
    rejected.recommendations = ["Odbijeno otvoreno pitanje"]
    superseded = clinical_document(db, p, physician_reviewed=True)
    superseded.review_status = "superseded"
    superseded.recommendations = ["Zamijenjeno otvoreno pitanje"]
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    open_questions = summary.json()["open_questions"]
    assert len(open_questions) == 1
    assert open_questions[0]["text"] == "Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled"
    assert {source["document_id"] for source in open_questions[0]["sources"]} == {reviewed.id}
    assert open_questions[0]["display_kind"] == "open_question"
    assert open_questions[0]["requires_attention"] is True


def test_gate_ai_rejection_preserves_raw_source(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    raw_text = doc.raw_text

    rejected = client.post(f"/api/clinical-documents/{doc.id}/reject-summary", headers=headers)
    assert rejected.status_code == 200
    body = rejected.json()
    assert body["raw_text"] == raw_text
    assert body["ai_summary"] is None
    assert body["key_findings"] == []
    assert body["recommendations"] == []
    assert body["ai_extraction_status"] == "rejected"
    assert body["review_status"] == "draft"
    assert body["physician_reviewed"] is False

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert_no_official_knowledge(summary.json())


def test_gate_evidence_timeline_read_only(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    db.add(AuditLog(action="clinical_document_reviewed", entity_type="ClinicalDocument", entity_id=doc.id, summary="Existing evidence"))
    db.commit()
    before_document = client.get(f"/api/clinical-documents/{doc.id}", headers=headers).json()
    before_audit_count = db.query(AuditLog).count()

    timeline = client.get(f"/api/clinical-documents/{doc.id}/evidence-timeline", headers=headers)
    assert timeline.status_code == 200
    after_document = client.get(f"/api/clinical-documents/{doc.id}", headers=headers).json()
    assert db.query(AuditLog).count() == before_audit_count
    assert after_document["review_status"] == before_document["review_status"]
    assert after_document["ai_extraction_status"] == before_document["ai_extraction_status"]
    assert timeline.json()[0]["knowledge_impact"] == "may_enable_official_knowledge"


def test_gate_readiness_is_operational_not_clinical(client, db, auth_setup):
    headers = auth_headers(client)
    response = client.get("/api/readiness", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ready_for_demo", "attention_needed", "blocked"}
    serialized = str(body).lower()
    assert "clinical readiness gate" not in serialized
    assert "ready with warning" not in serialized
    assert "not ready" not in serialized
    assert "needs nurse action" not in serialized


def test_gate_episode_engine_stays_deferred(client, db, auth_setup):
    headers = auth_headers(client)
    appointment(db)

    response = client.get("/api/readiness", headers=headers)
    assert response.status_code == 200
    check = next(item for item in response.json()["checks"] if item["key"] == "clinical_episodes")
    assert check["status"] == "ok"
    assert check["decision_impact"] == "none"
    assert "deferred" in check["message"].lower()
    assert "ne blokira" in check["message"].lower()


def test_gate_demo_real_data_guardrail(client):
    response = client.get("/api/public-config")
    assert response.status_code == 200
    body = response.json()
    assert body["demo_mode"] is True
    assert body["real_data_allowed"] is False
    assert response.headers["X-ASTRA-REAL-DATA-ALLOWED"] == "false"
    assert any("real patient data" in warning.lower() for warning in body["warnings"])


def test_gate_patient_summary_stale_still_warns(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    old_doc = clinical_document(db, p, physician_reviewed=True)
    old_doc.updated_at = datetime(2026, 7, 1, 9, 0)
    db.commit()

    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    reviewed = client.post(f"/api/patients/{p.id}/clinical-summary/review", headers=headers)
    assert reviewed.status_code == 200
    record = db.get(PatientClinicalSummaryRecord, reviewed.json()["id"])
    record.updated_at = datetime(2026, 7, 2, 9, 0)
    new_doc = clinical_document(db, p, physician_reviewed=True)
    new_doc.updated_at = datetime(2026, 7, 3, 9, 0)
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["reviewed_summary_is_stale"] is True
    assert body["summary_warning"] == "Pregledani sazetak je zastario jer postoje noviji pregledani dokumenti."

    readiness = client.get("/api/readiness", headers=headers)
    assert readiness.status_code == 200
    check = next(item for item in readiness.json()["checks"] if item["key"] == "patient_summary_stale")
    assert check["status"] == "warning"
    assert check["count"] == 1
