from app.auth.dependencies import hash_api_key
from app.models.domain import ApiKey, AuditLog, ClinicalEpisode, ClinicalFinding, ClinicalPlan
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
}


def auth_headers(client, email="admin@test.local"):
    token = login_token(client, email)
    return {"Authorization": f"Bearer {token}"}


def findings_list_endpoint(client, patient_id, headers):
    return client.get(f"/api/patients/{patient_id}/clinical-findings", headers=headers)


def finding_detail_endpoint(client, patient_id, finding_id, headers):
    return client.get(f"/api/patients/{patient_id}/clinical-findings/{finding_id}", headers=headers)


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


def assert_forbidden_fields_absent(payload):
    assert FORBIDDEN_RESPONSE_FIELDS.isdisjoint(payload.keys())


def test_findings_list_requires_auth(client, db):
    p = patient(db)

    response = findings_list_endpoint(client, p.id, headers={})

    assert response.status_code == 401


def test_findings_detail_requires_auth(client, db):
    p = patient(db)
    finding = create_finding(db, p)

    response = finding_detail_endpoint(client, p.id, finding.id, headers={})

    assert response.status_code == 401


def test_findings_list_requires_read_permission(client, db, auth_setup):
    p = patient(db)

    response = findings_list_endpoint(client, p.id, headers=auth_headers(client, "limited@test.local"))

    assert response.status_code == 403


def test_api_key_findings_read_denied_even_with_read_scope(client, db):
    p = patient(db)
    api_key = ApiKey(
        name="Findings read integration",
        key_hash=hash_api_key("raw-findings-read-key"),
        scopes=["clinical_findings.read"],
        active=True,
    )
    db.add(api_key)
    db.commit()

    response = findings_list_endpoint(client, p.id, headers={"X-ASTRA-API-Key": "raw-findings-read-key"})

    assert response.status_code == 403


def test_findings_list_returns_empty_state(client, db, auth_setup):
    p = patient(db)

    response = findings_list_endpoint(client, p.id, headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["patient_id"] == p.id
    assert body["findings"] == []
    assert body["count"] == 0
    assert body["is_read_only"] is True
    assert "dijagnozu" in body["warning"].lower()


def test_findings_list_returns_newest_first_and_source_linked_shape(client, db, auth_setup):
    p = patient(db)
    first = create_finding(db, p, finding_key="first-finding", label="First finding")
    second = create_finding(db, p, finding_key="second-finding", label="Second finding")
    audit_count = db.query(AuditLog).count()

    response = findings_list_endpoint(client, p.id, headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [item["id"] for item in body["findings"]] == [second.id, first.id]
    item = body["findings"][0]
    assert item["source_type"] == "clinical_document"
    assert item["source_label"] == "External pathology report"
    assert item["source_reference"] == "clinical_document:12:key_findings:0"
    assert item["safe_disclaimer"]
    assert_forbidden_fields_absent(item)
    assert db.query(AuditLog).count() == audit_count


def test_findings_detail_is_patient_scoped_and_read_only(client, db, auth_setup):
    p = patient(db)
    other = patient(db, first_name="Other", last_name="Patient")
    finding = create_finding(db, p)
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    audit_count = db.query(AuditLog).count()

    wrong_scope = finding_detail_endpoint(client, other.id, finding.id, headers=auth_headers(client))
    correct_scope = finding_detail_endpoint(client, p.id, finding.id, headers=auth_headers(client))

    assert wrong_scope.status_code == 404
    assert correct_scope.status_code == 200
    body = correct_scope.json()
    assert body["id"] == finding.id
    assert body["patient_id"] == p.id
    assert body["source_reference"] == "clinical_document:12:key_findings:0"
    assert "dijagnozu" in body["warning"].lower()
    assert_forbidden_fields_absent(body)
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert db.query(AuditLog).count() == audit_count


def test_findings_missing_patient_and_missing_detail_return_404(client, db, auth_setup):
    p = patient(db)

    missing_patient = findings_list_endpoint(client, 9999, headers=auth_headers(client))
    missing_detail = finding_detail_endpoint(client, p.id, 9999, headers=auth_headers(client))

    assert missing_patient.status_code == 404
    assert missing_detail.status_code == 404


def test_findings_write_routes_absent(client, db, auth_setup):
    p = patient(db)
    finding = create_finding(db, p)
    headers = auth_headers(client)

    responses = [
        client.post(f"/api/patients/{p.id}/clinical-findings", headers=headers, json={}),
        client.patch(f"/api/patients/{p.id}/clinical-findings/{finding.id}", headers=headers, json={}),
        client.put(f"/api/patients/{p.id}/clinical-findings/{finding.id}", headers=headers, json={}),
        client.delete(f"/api/patients/{p.id}/clinical-findings/{finding.id}", headers=headers),
        client.post(f"/api/patients/{p.id}/clinical-findings/{finding.id}/review", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-findings/{finding.id}/approve", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-findings/{finding.id}/clear", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-findings/{finding.id}/resolve", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-findings/{finding.id}/notify", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-findings/{finding.id}/task", headers=headers, json={}),
    ]

    assert all(response.status_code in {404, 405} for response in responses)
