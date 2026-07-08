from app.auth.dependencies import hash_api_key
from app.models.domain import ApiKey, AuditLog, ClinicalEpisode, ClinicalFinding, ClinicalOpenQuestion, ClinicalPlan
from app.services.seed import PERMISSIONS
from tests.conftest import login_token
from tests.factories import patient


FORBIDDEN_RESPONSE_FIELDS = {
    "diagnosis_confirmed",
    "treatment_plan",
    "patient_notified",
    "task_id",
    "outcome_evidence_id",
    "approval_status",
    "clearance_status",
    "resolved_by_ai",
    "patient_message_id",
    "appointment_status",
    "auto_closed_at",
}


def auth_headers(client, email="admin@test.local"):
    token = login_token(client, email)
    return {"Authorization": f"Bearer {token}"}


def questions_list_endpoint(client, patient_id, headers, **params):
    return client.get(f"/api/patients/{patient_id}/clinical-open-questions", headers=headers, params=params)


def question_detail_endpoint(client, patient_id, question_id, headers):
    return client.get(f"/api/patients/{patient_id}/clinical-open-questions/{question_id}", headers=headers)


def create_finding(db, patient_obj, **overrides):
    payload = {
        "patient_id": patient_obj.id,
        "source_document_id": None,
        "source_type": "clinical_document",
        "source_label": "External pathology report",
        "source_reference": "clinical_document:12:key_findings:0",
        "finding_key": "pathology-dysplasia-question",
        "label": "Pathology finding requires review",
        "category": "pathology",
        "lifecycle_status": "awaiting_review",
        "requires_review": True,
        "limitations_json": ["Finding is source-linked context, not diagnosis."],
        "schema_version": "clinical_finding.v1",
    }
    payload.update(overrides)
    finding = ClinicalFinding(**payload)
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


def create_question(db, patient_obj, **overrides):
    payload = {
        "patient_id": patient_obj.id,
        "finding_id": None,
        "source_document_id": None,
        "source_type": "clinical_document",
        "source_label": "External pathology report",
        "source_reference": "clinical_document:12:key_findings:0",
        "question_key": "question-pathology-follow-up",
        "label": "Does pathology require follow-up decision?",
        "status": "awaiting_review",
        "requires_clinician_review": True,
        "limitations_json": ["Open question is source-linked and requires physician interpretation."],
        "schema_version": "clinical_open_question.v1",
    }
    payload.update(overrides)
    question = ClinicalOpenQuestion(**payload)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def assert_forbidden_fields_absent(payload):
    assert FORBIDDEN_RESPONSE_FIELDS.isdisjoint(payload.keys())


def test_open_questions_list_requires_auth(client, db):
    p = patient(db)

    response = questions_list_endpoint(client, p.id, headers={})

    assert response.status_code == 401


def test_open_questions_detail_requires_auth(client, db):
    p = patient(db)
    question = create_question(db, p)

    response = question_detail_endpoint(client, p.id, question.id, headers={})

    assert response.status_code == 401


def test_open_questions_read_requires_permission(client, db, auth_setup):
    p = patient(db)

    response = questions_list_endpoint(client, p.id, headers=auth_headers(client, "limited@test.local"))

    assert response.status_code == 403


def test_api_key_open_questions_read_denied_even_with_read_scope(client, db):
    p = patient(db)
    api_key = ApiKey(
        name="Open questions read integration",
        key_hash=hash_api_key("raw-open-questions-read-key"),
        scopes=["clinical_open_questions.read"],
        active=True,
    )
    db.add(api_key)
    db.commit()

    response = questions_list_endpoint(client, p.id, headers={"X-ASTRA-API-Key": "raw-open-questions-read-key"})

    assert response.status_code == 403


def test_open_questions_list_returns_empty_state(client, db, auth_setup):
    p = patient(db)

    response = questions_list_endpoint(client, p.id, headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["patient_id"] == p.id
    assert body["questions"] == []
    assert body["count"] == 0
    assert body["is_read_only"] is True
    assert "dijagnozu" in body["warning"]


def test_open_questions_list_returns_newest_first_and_source_linked_shape(client, db, auth_setup):
    p = patient(db)
    first = create_question(db, p, question_key="first-question", label="First question")
    second = create_question(db, p, question_key="second-question", label="Second question")
    audit_count = db.query(AuditLog).count()

    response = questions_list_endpoint(client, p.id, headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [item["id"] for item in body["questions"]] == [second.id, first.id]
    item = body["questions"][0]
    assert item["source_type"] == "clinical_document"
    assert item["source_label"] == "External pathology report"
    assert item["source_reference_summary"] == "clinical_document:12:key_findings:0"
    assert item["requires_clinician_review"] is True
    assert item["no_decision_disclaimer"]
    assert_forbidden_fields_absent(item)
    assert db.query(AuditLog).count() == audit_count


def test_open_questions_list_supports_patient_scoped_finding_filter(client, db, auth_setup):
    p = patient(db)
    finding = create_finding(db, p)
    matched = create_question(db, p, question_key="matched-question", finding_id=finding.id)
    create_question(db, p, question_key="unmatched-question")

    response = questions_list_endpoint(client, p.id, headers=auth_headers(client), finding_id=finding.id)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["questions"][0]["id"] == matched.id
    assert body["questions"][0]["finding_id"] == finding.id


def test_open_questions_invalid_finding_filter_is_patient_scoped(client, db, auth_setup):
    p = patient(db)
    other = patient(db, first_name="Other", last_name="Patient")
    other_finding = create_finding(db, other)

    response = questions_list_endpoint(client, p.id, headers=auth_headers(client), finding_id=other_finding.id)

    assert response.status_code == 404


def test_open_question_detail_is_patient_scoped_source_linked_and_read_only(client, db, auth_setup):
    p = patient(db)
    other = patient(db, first_name="Other", last_name="Patient")
    finding = create_finding(db, p)
    question = create_question(db, p, finding_id=finding.id)
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    audit_count = db.query(AuditLog).count()

    wrong_scope = question_detail_endpoint(client, other.id, question.id, headers=auth_headers(client))
    correct_scope = question_detail_endpoint(client, p.id, question.id, headers=auth_headers(client))

    assert wrong_scope.status_code == 404
    assert correct_scope.status_code == 200
    body = correct_scope.json()
    assert body["id"] == question.id
    assert body["patient_id"] == p.id
    assert body["finding_id"] == finding.id
    assert body["source_reference"] == "clinical_document:12:key_findings:0"
    assert body["linked_finding_key"] == finding.finding_key
    assert "dijagnozu" in body["warning"]
    assert_forbidden_fields_absent(body)
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert db.query(AuditLog).count() == audit_count


def test_open_questions_missing_patient_and_missing_detail_return_404(client, db, auth_setup):
    p = patient(db)

    missing_patient = questions_list_endpoint(client, 9999, headers=auth_headers(client))
    missing_detail = question_detail_endpoint(client, p.id, 9999, headers=auth_headers(client))

    assert missing_patient.status_code == 404
    assert missing_detail.status_code == 404


def test_open_questions_write_review_routes_absent(client, db, auth_setup):
    p = patient(db)
    question = create_question(db, p)
    headers = auth_headers(client)

    responses = [
        client.post(f"/api/patients/{p.id}/clinical-open-questions", headers=headers, json={}),
        client.patch(f"/api/patients/{p.id}/clinical-open-questions/{question.id}", headers=headers, json={}),
        client.put(f"/api/patients/{p.id}/clinical-open-questions/{question.id}", headers=headers, json={}),
        client.delete(f"/api/patients/{p.id}/clinical-open-questions/{question.id}", headers=headers),
        client.post(f"/api/patients/{p.id}/clinical-open-questions/{question.id}/review", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-open-questions/{question.id}/approve", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-open-questions/{question.id}/clear", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-open-questions/{question.id}/resolve", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-open-questions/{question.id}/notify", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-open-questions/{question.id}/task", headers=headers, json={}),
    ]

    assert all(response.status_code in {404, 405} for response in responses)


def test_open_questions_write_permissions_and_frontend_actions_absent():
    assert "clinical_open_questions.write" not in PERMISSIONS
    assert "clinical_open_questions.review" not in PERMISSIONS
    assert "clinical_open_questions.approve" not in PERMISSIONS
    assert "clinical_open_questions.clear" not in PERMISSIONS
    assert "clinical_open_questions.resolve" not in PERMISSIONS


def test_open_question_read_response_keeps_source_linking_and_no_official_truth(client, db, auth_setup):
    p = patient(db)
    question = create_question(
        db,
        p,
        source_type="pathology",
        source_label="Pathology source",
        source_reference="pathology:report:line-4",
        limitations_json=["Source must be checked by clinician."],
    )

    detail = question_detail_endpoint(client, p.id, question.id, headers=auth_headers(client))
    item = detail.json()

    assert detail.status_code == 200
    assert item["source_type"] == "pathology"
    assert item["source_label"] == "Pathology source"
    assert item["source_reference"] == "pathology:report:line-4"
    assert item["limitations"] == ["Source must be checked by clinician."]
    assert "official truth" not in str(item).lower()
    assert "diagnosis" not in str(item).lower()
    assert "treatment_plan" not in item
