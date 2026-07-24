from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.auth.dependencies import hash_api_key
from app.models.domain import (
    ApiKey,
    AuditLog,
    ClinicalEpisode,
    ClinicalFinding,
    ClinicalOpenQuestion,
    ClinicalPlan,
    ClinicalReadinessReviewAcknowledgment,
    ClinicalReadinessSnapshot,
)
from app.services.seed import PERMISSIONS
from tests.conftest import login_token
from tests.factories import appointment, default_clinic, patient


FORBIDDEN_RESPONSE_FIELDS = {
    "diagnosis_confirmed",
    "treatment_plan",
    "patient_notified",
    "task_id",
    "outcome_evidence_id",
    "approval_status",
    "clearance_status",
    "override_status",
    "resolved_by_ai",
    "patient_message_id",
    "appointment_status",
}


def auth_headers(client, email="admin@test.local"):
    token = login_token(client, email)
    return {"Authorization": f"Bearer {token}"}


def timeline_endpoint(client, patient_id, headers, **params):
    return client.get(f"/api/patients/{patient_id}/clinical-evidence-timeline", headers=headers, params=params)


def create_finding(db, patient_obj, **overrides):
    clinic = default_clinic(db)
    payload = {
        "patient_id": patient_obj.id,
        "institution_id": clinic.institution_id if clinic else None,
        "source_document_id": None,
        "source_type": "clinical_document",
        "source_label": "Pathology report",
        "source_reference": "clinical_document:12:key_findings:0",
        "finding_key": "finding-pathology-review",
        "label": "Finding requires review",
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
    clinic = default_clinic(db)
    payload = {
        "patient_id": patient_obj.id,
        "institution_id": clinic.institution_id if clinic else None,
        "finding_id": None,
        "source_document_id": None,
        "source_type": "clinical_document",
        "source_label": "Pathology report",
        "source_reference": "clinical_document:12:key_findings:0",
        "question_key": "question-pathology-follow-up",
        "label": "Does pathology require follow-up?",
        "status": "awaiting_review",
        "requires_clinician_review": True,
        "limitations_json": ["Open question requires clinician interpretation."],
        "schema_version": "clinical_open_question.v1",
    }
    payload.update(overrides)
    question = ClinicalOpenQuestion(**payload)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def create_snapshot(db, patient_obj, user_id: int, **overrides):
    appt = appointment(db, patient_obj=patient_obj)
    payload = {
        "appointment_id": appt.id,
        "patient_id": patient_obj.id,
        "service_id": appt.service_id,
        "created_by_user_id": user_id,
        "schema_version": "clinical-readiness-snapshot-v1",
        "preview_generated_at": datetime(2026, 7, 8, 8, 0, tzinfo=UTC),
        "preview_status": "needs_physician_review",
        "preview_summary": "Read-only preview summary.",
        "template_key": "colonoscopy",
        "template_label": "Kolonoskopija",
        "template_version": "demo-v1",
        "template_binding_status": "explicit",
        "template_binding_warning": None,
        "is_preview_snapshot": True,
        "items_json": [{"key": "demo", "label": "Demo item"}],
        "limitations_json": ["Snapshot is advisory context."],
        "source_warnings_json": [],
        "source_refs_json": [{"type": "ClinicalDocument", "id": 1}],
        "disclaimer": "Snapshot nije clearance.",
        "snapshot_reason": "Pilot review.",
    }
    payload.update(overrides)
    snapshot = ClinicalReadinessSnapshot(**payload)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def create_acknowledgment(db, patient_obj, user_id: int, **overrides):
    appt = None if "appointment_id" in overrides else appointment(db, patient_obj=patient_obj)
    payload = {
        "appointment_id": appt.id if appt else overrides["appointment_id"],
        "patient_id": patient_obj.id,
        "snapshot_id": None,
        "advisory_signal_key": "signal:missing-context",
        "actor_user_id": user_id,
        "actor_role": "physician",
        "reason": "Human reviewed advisory context.",
        "limitations_json": ["Acknowledgment is not approval."],
        "schema_version": "acknowledgment.v1",
        "not_decision_disclaimer": "Acknowledgment nije klinicka odluka.",
        "is_decision": False,
        "is_clearance": False,
        "is_override": False,
    }
    payload.update(overrides)
    acknowledgment = ClinicalReadinessReviewAcknowledgment(**payload)
    db.add(acknowledgment)
    db.commit()
    db.refresh(acknowledgment)
    return acknowledgment


def assert_event_shape_is_safe(event):
    assert FORBIDDEN_RESPONSE_FIELDS.isdisjoint(event.keys())
    assert event["is_decision"] is False
    assert event["source_reference"]["source_object_reference"]
    assert event["source_reference"]["source_object_type"]
    assert event["source_reference"]["provenance_label"]
    assert event["limitations"]
    assert "official truth" not in str(event).lower()


def test_timeline_list_requires_auth(client, db):
    p = patient(db)

    response = timeline_endpoint(client, p.id, headers={})

    assert response.status_code == 401


def test_timeline_list_requires_read_permission(client, db, auth_setup):
    p = patient(db)

    response = timeline_endpoint(client, p.id, headers=auth_headers(client, "limited@test.local"))

    assert response.status_code == 403


def test_api_key_timeline_read_denied_even_with_read_scope(client, db):
    p = patient(db)
    api_key = ApiKey(
        name="Timeline read integration",
        key_hash=hash_api_key("raw-timeline-read-key"),
        scopes=["clinical_evidence_timeline.read"],
        active=True,
    )
    db.add(api_key)
    db.commit()

    response = timeline_endpoint(client, p.id, headers={"X-ASTRA-API-Key": "raw-timeline-read-key"})

    assert response.status_code == 403


def test_timeline_empty_state_is_read_only(client, db, auth_setup):
    p = patient(db)

    response = timeline_endpoint(client, p.id, headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["patient_id"] == p.id
    assert body["events"] == []
    assert body["count"] == 0
    assert body["is_read_only"] is True
    assert "diagnosis" in body["warning"]


def test_timeline_aggregates_source_objects_newest_first_and_without_side_effects(client, db, auth_setup):
    p = patient(db)
    finding = create_finding(db, p)
    question = create_question(db, p)
    snapshot = create_snapshot(db, p, auth_setup["admin"].id)
    acknowledgment = create_acknowledgment(db, p, auth_setup["admin"].id, appointment_id=snapshot.appointment_id)
    audit_count = db.query(AuditLog).count()
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()

    response = timeline_endpoint(client, p.id, headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 4
    event_types = {event["event_type"] for event in body["events"]}
    assert {
        "finding_requires_review",
        "open_question_awaiting_review",
        "readiness_snapshot_captured",
        "acknowledgment_recorded",
    }.issubset(event_types)
    timestamps = [event["event_timestamp"] for event in body["events"]]
    assert timestamps == sorted(timestamps, reverse=True)
    references = {event["source_reference"]["source_object_reference"] for event in body["events"]}
    assert f"clinical_finding:{finding.id}" in references
    assert f"clinical_open_question:{question.id}" in references
    assert f"clinical_readiness_snapshot:{snapshot.id}" in references
    assert f"clinical_readiness_acknowledgment:{acknowledgment.id}" in references
    for event in body["events"]:
        assert_event_shape_is_safe(event)
    assert db.query(AuditLog).count() == audit_count
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count


def test_timeline_filters_by_event_source_requires_review_and_date(client, db, auth_setup):
    p = patient(db)
    finding = create_finding(db, p)
    create_question(db, p)
    db.refresh(finding)
    date_from = (finding.created_at - timedelta(seconds=1)).isoformat()
    date_to = (finding.created_at + timedelta(seconds=1)).isoformat()

    response = timeline_endpoint(
        client,
        p.id,
        headers=auth_headers(client),
        event_type="finding_requires_review",
        source_type="clinical_finding",
        requires_review=True,
        date_from=date_from,
        date_to=date_to,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    event = body["events"][0]
    assert event["event_type"] == "finding_requires_review"
    assert event["source_reference"]["source_object_type"] == "clinical_finding"
    assert event["requires_review"] is True


def test_timeline_is_patient_scoped(client, db, auth_setup):
    p = patient(db)
    other = patient(db, first_name="Other", last_name="Patient")
    create_finding(db, p)
    create_finding(db, other, finding_key="other-finding")

    response = timeline_endpoint(client, p.id, headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["events"][0]["source_reference"]["patient_id"] == p.id


def test_timeline_missing_patient_returns_404(client, db, auth_setup):
    response = timeline_endpoint(client, 9999, headers=auth_headers(client))

    assert response.status_code == 404


def test_timeline_superseded_snapshot_mapping_is_additive(client, db, auth_setup):
    p = patient(db)
    superseded_at = datetime(2026, 7, 8, 9, 0, tzinfo=UTC)
    snapshot = create_snapshot(db, p, auth_setup["admin"].id, superseded_at=superseded_at, superseded_reason="Newer snapshot")

    response = timeline_endpoint(client, p.id, headers=auth_headers(client))

    assert response.status_code == 200
    event_keys = {event["event_key"] for event in response.json()["events"]}
    assert f"clinical_readiness_snapshot:{snapshot.id}:captured" in event_keys
    assert f"clinical_readiness_snapshot:{snapshot.id}:superseded" in event_keys


def test_timeline_write_routes_permissions_models_and_frontend_actions_absent(client, db, auth_setup):
    p = patient(db)
    headers = auth_headers(client)
    responses = [
        client.post(f"/api/patients/{p.id}/clinical-evidence-timeline", headers=headers, json={}),
        client.patch(f"/api/patients/{p.id}/clinical-evidence-timeline/1", headers=headers, json={}),
        client.put(f"/api/patients/{p.id}/clinical-evidence-timeline/1", headers=headers, json={}),
        client.delete(f"/api/patients/{p.id}/clinical-evidence-timeline/1", headers=headers),
        client.post(f"/api/patients/{p.id}/clinical-evidence-timeline/1/review", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-evidence-timeline/1/approve", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-evidence-timeline/1/clear", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-evidence-timeline/1/resolve", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-evidence-timeline/1/task", headers=headers, json={}),
        client.post(f"/api/patients/{p.id}/clinical-evidence-timeline/1/notify", headers=headers, json={}),
    ]

    assert all(response.status_code in {404, 405} for response in responses)
    assert "clinical_evidence_timeline.write" not in PERMISSIONS
    assert "clinical_evidence_timeline.review" not in PERMISSIONS
    assert "clinical_evidence_timeline.approve" not in PERMISSIONS
    assert "clinical_evidence_timeline.clear" not in PERMISSIONS
    assert "clinical_evidence_timeline.resolve" not in PERMISSIONS

    repo = Path(__file__).resolve().parents[1]
    assert "ClinicalEvidenceTimelineEvent" not in (repo / "app" / "models" / "domain.py").read_text(encoding="utf-8")
    frontend_client_path = repo.parent / "frontend" / "src" / "api" / "client.ts"
    if frontend_client_path.exists():
        frontend_client = frontend_client_path.read_text(encoding="utf-8")
        assert "getClinicalEvidenceTimeline" in frontend_client
        assert "postClinicalEvidenceTimeline" not in frontend_client
        assert "createClinicalEvidenceTimeline" not in frontend_client
        assert "updateClinicalEvidenceTimeline" not in frontend_client
        assert "deleteClinicalEvidenceTimeline" not in frontend_client
