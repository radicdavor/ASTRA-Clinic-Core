from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import hash_api_key
from app.models.domain import ApiKey, AuditLog, ClinicalEpisode, ClinicalPlan, ClinicalReadinessSnapshot, PatientClinicalSummaryRecord
from app.services.clinical_readiness_snapshots import (
    CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT,
    CLINICAL_READINESS_SNAPSHOT_DISCLAIMER,
    CLINICAL_READINESS_SNAPSHOT_SUPERSEDED_EVENT,
    capture_clinical_readiness_snapshot,
    supersede_clinical_readiness_snapshot,
)
from tests.conftest import login_token
from tests.factories import appointment, clinical_document, room, service


DISCLAIMER = "Snapshot je zapis preview prikaza, ne clinical approval."


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def preview(client, appointment_id, headers):
    return client.get(f"/api/appointments/{appointment_id}/clinical-readiness-preview", headers=headers)


def capture_endpoint(client, appointment_id, headers, payload=None):
    return client.post(
        f"/api/appointments/{appointment_id}/clinical-readiness-snapshots",
        headers=headers,
        json=payload if payload is not None else {"reason": "Endpoint capture reason."},
    )


def history_endpoint(client, appointment_id, headers):
    return client.get(f"/api/appointments/{appointment_id}/clinical-readiness-snapshots", headers=headers)


def detail_endpoint(client, appointment_id, snapshot_id, headers):
    return client.get(f"/api/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}", headers=headers)


def test_clinical_readiness_snapshot_table_exists_after_metadata_setup(db):
    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))

    assert "clinical_readiness_snapshots" in table_names


def snapshot_payload(appt, user_id: int) -> dict:
    return {
        "appointment_id": appt.id,
        "patient_id": appt.patient_id,
        "service_id": appt.service_id,
        "created_by_user_id": user_id,
        "schema_version": "clinical-readiness-snapshot-v1",
        "preview_generated_at": datetime(2026, 7, 7, 10, 30, tzinfo=UTC),
        "preview_status": "ready_with_warning",
        "preview_summary": "Read-only preview summary.",
        "template_key": "colonoscopy",
        "template_label": "Kolonoskopija",
        "template_version": "demo-v1",
        "template_binding_status": "explicit",
        "template_binding_warning": None,
        "is_preview_snapshot": True,
        "items_json": [{"key": "demo", "label": "Demo item"}],
        "limitations_json": ["Demo limitation"],
        "source_warnings_json": ["Source warning"],
        "source_refs_json": [{"type": "ClinicalDocument", "id": 1}],
        "disclaimer": DISCLAIMER,
        "snapshot_reason": "Pilot review prije kolonoskopije.",
    }


def test_clinical_readiness_snapshot_persists_immutable_preview_payload(db, auth_setup):
    appt = appointment(db)
    snapshot = ClinicalReadinessSnapshot(**snapshot_payload(appt, auth_setup["admin"].id))

    db.add(snapshot)
    db.commit()

    stored = db.get(ClinicalReadinessSnapshot, snapshot.id)
    assert stored is not None
    assert stored.appointment_id == appt.id
    assert stored.patient_id == appt.patient_id
    assert stored.service_id == appt.service_id
    assert stored.schema_version == "clinical-readiness-snapshot-v1"
    assert stored.preview_status == "ready_with_warning"
    assert stored.template_key == "colonoscopy"
    assert stored.template_version == "demo-v1"
    assert stored.is_preview_snapshot is True
    assert stored.items_json == [{"key": "demo", "label": "Demo item"}]
    assert stored.limitations_json == ["Demo limitation"]
    assert stored.source_warnings_json == ["Source warning"]
    assert stored.source_refs_json == [{"type": "ClinicalDocument", "id": 1}]
    assert stored.disclaimer == DISCLAIMER
    assert stored.snapshot_reason == "Pilot review prije kolonoskopije."


def test_clinical_readiness_snapshot_requires_non_empty_reason(db, auth_setup):
    appt = appointment(db)
    payload = snapshot_payload(appt, auth_setup["admin"].id)
    payload["snapshot_reason"] = "   "
    snapshot = ClinicalReadinessSnapshot(**payload)

    db.add(snapshot)

    with pytest.raises(IntegrityError):
        db.commit()


def test_clinical_readiness_snapshot_model_does_not_create_workflow_objects(db, auth_setup):
    appt = appointment(db, status="scheduled")
    original_status = appt.status
    audit_count = db.query(AuditLog).count()
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    snapshot = ClinicalReadinessSnapshot(**snapshot_payload(appt, auth_setup["admin"].id))

    db.add(snapshot)
    db.commit()
    db.expire(appt)

    assert appt.status == original_status
    assert db.query(AuditLog).count() == audit_count
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count


def test_capture_requires_reason(db, auth_setup):
    appt = appointment(db)

    with pytest.raises(ValueError):
        capture_clinical_readiness_snapshot(db, appointment_id=appt.id, actor_user_id=auth_setup["admin"].id, reason=" ")


def test_capture_requires_actor_user_id(db):
    appt = appointment(db)

    with pytest.raises(ValueError):
        capture_clinical_readiness_snapshot(db, appointment_id=appt.id, actor_user_id=None, reason="Pilot review.")


def test_capture_creates_snapshot_and_copies_preview_payload(db, auth_setup):
    colonoscopy = service(db, name="Kolonoskopija")
    appt = appointment(db, service_obj=colonoscopy)
    clinical_document(db, appt.patient, physician_reviewed=True)

    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Pilot review prije kolonoskopije.",
    )

    assert db.query(ClinicalReadinessSnapshot).count() == 1
    assert snapshot.appointment_id == appt.id
    assert snapshot.patient_id == appt.patient_id
    assert snapshot.service_id == appt.service_id
    assert snapshot.snapshot_reason == "Pilot review prije kolonoskopije."
    assert snapshot.schema_version == "clinical-readiness-snapshot-v1"
    assert snapshot.template_key == "colonoscopy"
    assert snapshot.template_version == "demo-v1"
    assert snapshot.template_binding_status in {"explicit", "keyword_fallback", "generic_fallback"}
    assert snapshot.is_preview_snapshot is True
    assert snapshot.disclaimer == CLINICAL_READINESS_SNAPSHOT_DISCLAIMER
    assert snapshot.items_json
    assert isinstance(snapshot.items_json[0], dict)
    assert isinstance(snapshot.limitations_json, list)
    assert isinstance(snapshot.source_warnings_json, list)
    assert isinstance(snapshot.source_refs_json, list)


def test_capture_writes_audit_event_with_required_payload(db, auth_setup):
    colonoscopy = service(db, name="Kolonoskopija")
    appt = appointment(db, service_obj=colonoscopy)

    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Audit reason.",
    )

    event = db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT).one()
    payload = event.after_json
    assert event.entity_type == "ClinicalReadinessSnapshot"
    assert event.entity_id == snapshot.id
    assert payload["snapshot_id"] == snapshot.id
    assert payload["appointment_id"] == appt.id
    assert payload["patient_id"] == appt.patient_id
    assert payload["service_id"] == appt.service_id
    assert payload["created_by_user_id"] == auth_setup["admin"].id
    assert payload["capture_reason"] == "Audit reason."
    assert payload["schema_version"] == "clinical-readiness-snapshot-v1"
    assert payload["template_key"] == snapshot.template_key
    assert payload["template_version"] == snapshot.template_version
    assert payload["item_count"] == len(snapshot.items_json)
    assert payload["limitation_count"] == len(snapshot.limitations_json)
    assert payload["source_warning_count"] == len(snapshot.source_warnings_json)
    assert payload["is_preview_snapshot"] is True
    assert payload["disclaimer"] == CLINICAL_READINESS_SNAPSHOT_DISCLAIMER


def test_capture_rolls_back_snapshot_when_audit_fails(db, auth_setup, monkeypatch):
    import app.services.clinical_readiness_snapshots as snapshot_service

    appt = appointment(db)

    def fail_audit(*args, **kwargs):
        raise RuntimeError("audit failed")

    monkeypatch.setattr(snapshot_service, "audit", fail_audit)

    with pytest.raises(RuntimeError):
        snapshot_service.capture_clinical_readiness_snapshot(
            db,
            appointment_id=appt.id,
            actor_user_id=auth_setup["admin"].id,
            reason="Audit failure test.",
        )

    assert db.query(ClinicalReadinessSnapshot).count() == 0
    assert db.query(AuditLog).count() == 0


def test_capture_does_not_change_appointment_or_create_workflow_objects(db, auth_setup):
    appt = appointment(db, status="scheduled")
    original_status = appt.status
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))

    capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Workflow safety test.",
    )
    db.expire(appt)

    assert appt.status == original_status
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "outcome_evidence" not in table_names
    assert "tasks" not in table_names


def test_preview_get_still_does_not_create_snapshot_or_audit(client, db, auth_setup):
    appt = appointment(db)
    snapshot_count = db.query(ClinicalReadinessSnapshot).count()
    audit_count = db.query(AuditLog).count()

    response = preview(client, appt.id, auth_headers(client))

    assert response.status_code == 200
    assert db.query(ClinicalReadinessSnapshot).count() == snapshot_count
    assert db.query(AuditLog).count() == audit_count


def test_capture_does_not_use_patient_summary_as_source_truth(db, auth_setup):
    appt = appointment(db)
    db.add(
        PatientClinicalSummaryRecord(
            patient_id=appt.patient_id,
            summary_text="Summary-only claim",
            open_items=["Summary-only open question"],
            status="reviewed",
            generated_by="physician",
            reviewed_by=auth_setup["admin"].id,
            reviewed_at=datetime(2026, 7, 7, tzinfo=UTC),
        )
    )
    db.commit()

    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Summary source truth guardrail.",
    )

    labels = [item.get("label") for item in snapshot.items_json]
    assert "Summary-only open question" not in labels
    assert all(ref.get("source_type") != "patient_clinical_summary" for ref in snapshot.source_refs_json)


def test_capture_does_not_use_unreviewed_ai_as_official_source(db, auth_setup):
    appt = appointment(db)
    doc = clinical_document(db, appt.patient, physician_reviewed=False)
    doc.recommendations = ["Unreviewed AI-only warning"]
    db.commit()

    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Unreviewed AI guardrail.",
    )

    labels = [item.get("label") for item in snapshot.items_json]
    assert "Unreviewed AI-only warning" not in labels
    assert all(ref.get("source_ref") != f"ClinicalDocument:{doc.id}" for ref in snapshot.source_refs_json)


def test_capture_endpoint_requires_authentication(client, db):
    appt = appointment(db)

    response = capture_endpoint(client, appt.id, headers={})

    assert response.status_code == 401


def test_capture_endpoint_requires_snapshot_write_permission(client, db, auth_setup):
    appt = appointment(db)
    headers = {"Authorization": f"Bearer {login_token(client, 'limited@test.local')}"}

    response = capture_endpoint(client, appt.id, headers=headers)

    assert response.status_code == 403
    assert "clinical_readiness.snapshots.write" in response.json()["detail"]


def test_capture_endpoint_requires_reason(client, db, auth_setup):
    appt = appointment(db)

    response = capture_endpoint(client, appt.id, headers=auth_headers(client), payload={"reason": "   "})

    assert response.status_code == 422


def test_capture_endpoint_creates_snapshot_and_audit_without_workflow_side_effects(client, db, auth_setup):
    colonoscopy = service(db, name="Kolonoskopija")
    appt = appointment(db, service_obj=colonoscopy, status="scheduled")
    original_status = appt.status
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))

    response = capture_endpoint(client, appt.id, headers=auth_headers(client), payload={"reason": "Endpoint pilot review."})

    assert response.status_code == 200
    body = response.json()
    snapshot = db.get(ClinicalReadinessSnapshot, body["id"])
    assert snapshot is not None
    assert body["appointment_id"] == appt.id
    assert body["patient_id"] == appt.patient_id
    assert body["service_id"] == appt.service_id
    assert body["snapshot_reason"] == "Endpoint pilot review."
    assert body["is_preview_snapshot"] is True
    assert "Ne predstavlja clinical approval" in body["disclaimer"]
    assert body["template_key"] == snapshot.template_key
    assert body["template_version"] == snapshot.template_version
    assert body["template_binding_status"] == snapshot.template_binding_status
    assert body["items"] == snapshot.items_json
    assert body["limitations"] == snapshot.limitations_json
    assert body["source_warnings"] == snapshot.source_warnings_json
    assert body["source_refs"] == snapshot.source_refs_json
    assert db.query(ClinicalReadinessSnapshot).count() == 1
    event = db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT).one()
    assert event.entity_id == snapshot.id
    assert event.after_json["capture_reason"] == "Endpoint pilot review."
    db.expire(appt)
    assert appt.status == original_status
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "outcome_evidence" not in table_names
    assert "tasks" not in table_names


def test_capture_endpoint_rejects_client_preview_payload(client, db, auth_setup):
    appt = appointment(db)

    response = capture_endpoint(
        client,
        appt.id,
        headers=auth_headers(client),
        payload={
            "reason": "Do not trust client payload.",
            "items": [{"key": "client_claim", "label": "Client supplied item"}],
            "preview_status": "ready",
        },
    )

    assert response.status_code == 422
    assert db.query(ClinicalReadinessSnapshot).count() == 0
    assert db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT).count() == 0


def test_capture_endpoint_response_excludes_forbidden_approval_fields(client, db, auth_setup):
    appt = appointment(db)

    response = capture_endpoint(client, appt.id, headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    forbidden = {"approved", "cleared", "procedure_allowed", "task_created", "outcome_evidence_id", "override_status"}
    assert forbidden.isdisjoint(body.keys())


def test_api_key_capture_denied_even_with_snapshot_scope(client, db):
    appt = appointment(db)
    api_key = ApiKey(
        name="Snapshot integration",
        key_hash=hash_api_key("raw-snapshot-key"),
        scopes=["clinical_readiness.snapshots.write"],
        active=True,
    )
    db.add(api_key)
    db.commit()

    response = capture_endpoint(
        client,
        appt.id,
        headers={"X-ASTRA-API-Key": "raw-snapshot-key"},
    )

    assert response.status_code == 403
    assert db.query(ClinicalReadinessSnapshot).count() == 0


def test_history_endpoint_requires_authentication(client, db):
    appt = appointment(db)

    response = history_endpoint(client, appt.id, headers={})

    assert response.status_code == 401


def test_history_endpoint_requires_read_permission(client, db, auth_setup):
    appt = appointment(db)
    auth_setup["limited"].role.permissions = []
    db.commit()
    headers = {"Authorization": f"Bearer {login_token(client, 'limited@test.local')}"}

    response = history_endpoint(client, appt.id, headers=headers)

    assert response.status_code == 403
    assert "clinical_readiness.snapshots.read" in response.json()["detail"]


def test_history_endpoint_returns_appointment_scoped_newest_first_summary(client, db, auth_setup):
    appt = appointment(db)
    other_appt = appointment(db, room_obj=room(db, name="Room 2"))
    first = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="First snapshot.",
    )
    second = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Second snapshot.",
    )
    capture_clinical_readiness_snapshot(
        db,
        appointment_id=other_appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Other appointment snapshot.",
    )

    response = history_endpoint(client, appt.id, auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["appointment_id"] == appt.id
    assert body["count"] == 2
    assert body["is_preview_history"] is True
    assert "Ne predstavlja clinical approval" in body["warning"]
    ids = [snapshot["id"] for snapshot in body["snapshots"]]
    assert ids == [second.id, first.id]
    assert all(snapshot["appointment_id"] == appt.id for snapshot in body["snapshots"])
    item = body["snapshots"][0]
    assert item["item_count"] == len(second.items_json)
    assert item["limitation_count"] == len(second.limitations_json)
    assert item["source_warning_count"] == len(second.source_warnings_json)
    assert "items" not in item
    assert "limitations" not in item
    assert "source_refs" not in item


def test_history_endpoint_response_excludes_approval_fields(client, db, auth_setup):
    appt = appointment(db)
    capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Response safety.",
    )

    response = history_endpoint(client, appt.id, auth_headers(client))

    assert response.status_code == 200
    forbidden = {"approved", "cleared", "procedure_allowed", "task_created", "outcome_evidence_id", "override_status"}
    body = response.json()
    assert forbidden.isdisjoint(body.keys())
    assert forbidden.isdisjoint(body["snapshots"][0].keys())


def test_history_endpoint_is_read_only_and_writes_no_audit(client, db, auth_setup):
    appt = appointment(db, status="scheduled")
    capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Existing snapshot.",
    )
    original_status = appt.status
    snapshot_count = db.query(ClinicalReadinessSnapshot).count()
    audit_count = db.query(AuditLog).count()
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))

    response = history_endpoint(client, appt.id, auth_headers(client))

    assert response.status_code == 200
    db.expire(appt)
    assert appt.status == original_status
    assert db.query(ClinicalReadinessSnapshot).count() == snapshot_count
    assert db.query(AuditLog).count() == audit_count
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "outcome_evidence" not in table_names
    assert "tasks" not in table_names


def test_capture_endpoint_still_requires_write_permission_with_read_permission(client, db, auth_setup):
    appt = appointment(db)
    auth_setup["limited"].role.permissions = [permission for permission in auth_setup["admin"].role.permissions if permission.name == "clinical_readiness.snapshots.read"]
    db.commit()
    headers = {"Authorization": f"Bearer {login_token(client, 'limited@test.local')}"}

    response = capture_endpoint(client, appt.id, headers=headers)

    assert response.status_code == 403
    assert "clinical_readiness.snapshots.write" in response.json()["detail"]


def test_detail_endpoint_requires_authentication(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Detail auth guard.",
    )

    response = detail_endpoint(client, appt.id, snapshot.id, headers={})

    assert response.status_code == 401


def test_detail_endpoint_requires_read_permission(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Detail permission guard.",
    )
    auth_setup["limited"].role.permissions = []
    db.commit()
    headers = {"Authorization": f"Bearer {login_token(client, 'limited@test.local')}"}

    response = detail_endpoint(client, appt.id, snapshot.id, headers=headers)

    assert response.status_code == 403
    assert "clinical_readiness.snapshots.read" in response.json()["detail"]


def test_detail_endpoint_returns_full_copied_payload(client, db, auth_setup):
    colonoscopy = service(db, name="Kolonoskopija")
    appt = appointment(db, service_obj=colonoscopy)
    clinical_document(db, appt.patient, physician_reviewed=True)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Detail payload review.",
    )

    response = detail_endpoint(client, appt.id, snapshot.id, auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == snapshot.id
    assert body["appointment_id"] == appt.id
    assert body["patient_id"] == appt.patient_id
    assert body["service_id"] == appt.service_id
    assert body["preview_summary"] == snapshot.preview_summary
    assert body["template_binding_warning"] == snapshot.template_binding_warning
    assert body["snapshot_reason"] == "Detail payload review."
    assert body["items"] == snapshot.items_json
    assert body["limitations"] == snapshot.limitations_json
    assert body["source_warnings"] == snapshot.source_warnings_json
    assert body["source_refs"] == snapshot.source_refs_json
    assert body["superseded_by_snapshot_id"] == snapshot.superseded_by_snapshot_id
    assert "Ne predstavlja clinical approval" in body["warning"]


def test_detail_endpoint_is_appointment_scoped(client, db, auth_setup):
    appt = appointment(db)
    other_appt = appointment(db, room_obj=room(db, name="Room 2"))
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Scoped detail.",
    )

    response = detail_endpoint(client, other_appt.id, snapshot.id, auth_headers(client))

    assert response.status_code == 404


def test_detail_endpoint_read_is_side_effect_free(client, db, auth_setup):
    appt = appointment(db, status="scheduled")
    original_status = appt.status
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Read-only detail.",
    )
    snapshot_count = db.query(ClinicalReadinessSnapshot).count()
    audit_count = db.query(AuditLog).count()
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))

    response = detail_endpoint(client, appt.id, snapshot.id, auth_headers(client))

    assert response.status_code == 200
    db.expire(appt)
    assert appt.status == original_status
    assert db.query(ClinicalReadinessSnapshot).count() == snapshot_count
    assert db.query(AuditLog).count() == audit_count
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "outcome_evidence" not in table_names
    assert "tasks" not in table_names


def test_detail_endpoint_response_excludes_forbidden_approval_fields(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Forbidden field detail.",
    )

    response = detail_endpoint(client, appt.id, snapshot.id, auth_headers(client))

    assert response.status_code == 200
    forbidden = {"approved", "cleared", "procedure_allowed", "task_created", "outcome_evidence_id", "override_status"}
    assert forbidden.isdisjoint(response.json().keys())


def test_capture_without_idempotency_key_can_create_multiple_snapshots(db, auth_setup):
    appt = appointment(db)

    first = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Explicit first capture.",
    )
    second = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Explicit second capture.",
    )

    assert first.id != second.id
    assert db.query(ClinicalReadinessSnapshot).count() == 2


def test_capture_same_idempotency_key_and_fingerprint_returns_existing_snapshot_without_audit(db, auth_setup):
    appt = appointment(db)

    first = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Retry-safe capture.",
        idempotency_key=" retry-key ",
    )
    audit_count = db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT).count()
    second = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Retry-safe capture.",
        idempotency_key="retry-key",
    )

    assert second.id == first.id
    assert db.query(ClinicalReadinessSnapshot).count() == 1
    assert db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT).count() == audit_count
    assert first.idempotency_key == "retry-key"
    assert first.idempotency_fingerprint


def test_capture_endpoint_same_idempotency_key_different_reason_returns_conflict(client, db, auth_setup):
    appt = appointment(db)
    headers = auth_headers(client)

    first = capture_endpoint(
        client,
        appt.id,
        headers=headers,
        payload={"reason": "Original reason.", "idempotency_key": "same-key"},
    )
    second = capture_endpoint(
        client,
        appt.id,
        headers=headers,
        payload={"reason": "Different reason.", "idempotency_key": "same-key"},
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert db.query(ClinicalReadinessSnapshot).count() == 1


def test_capture_endpoint_idempotency_does_not_trust_client_preview_timestamp(client, db, auth_setup):
    appt = appointment(db, status="scheduled")
    original_status = appt.status
    headers = auth_headers(client)
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))

    first = capture_endpoint(
        client,
        appt.id,
        headers=headers,
        payload={
            "reason": "Client timestamp ignored.",
            "idempotency_key": "timestamp-key",
            "client_preview_generated_at": "1999-01-01T00:00:00Z",
        },
    )
    second = capture_endpoint(
        client,
        appt.id,
        headers=headers,
        payload={
            "reason": "Client timestamp ignored.",
            "idempotency_key": "timestamp-key",
            "client_preview_generated_at": "2030-01-01T00:00:00Z",
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    db.expire(appt)
    assert appt.status == original_status
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "outcome_evidence" not in table_names
    assert "tasks" not in table_names


def test_snapshot_update_and_delete_endpoints_do_not_exist(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="No mutation endpoints.",
    )
    path = f"/api/appointments/{appt.id}/clinical-readiness-snapshots/{snapshot.id}"
    headers = auth_headers(client)

    patch_response = client.patch(path, headers=headers, json={"snapshot_reason": "Edited"})
    delete_response = client.delete(path, headers=headers)

    assert patch_response.status_code == 405
    assert delete_response.status_code == 405


def test_snapshot_detail_and_history_reads_do_not_mutate_snapshot_payload(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Immutable read.",
    )
    before = {
        "items": list(snapshot.items_json),
        "limitations": list(snapshot.limitations_json),
        "source_warnings": list(snapshot.source_warnings_json),
        "source_refs": list(snapshot.source_refs_json),
        "summary": snapshot.preview_summary,
        "reason": snapshot.snapshot_reason,
        "disclaimer": snapshot.disclaimer,
    }

    assert history_endpoint(client, appt.id, auth_headers(client)).status_code == 200
    assert detail_endpoint(client, appt.id, snapshot.id, auth_headers(client)).status_code == 200
    db.refresh(snapshot)

    assert snapshot.items_json == before["items"]
    assert snapshot.limitations_json == before["limitations"]
    assert snapshot.source_warnings_json == before["source_warnings"]
    assert snapshot.source_refs_json == before["source_refs"]
    assert snapshot.preview_summary == before["summary"]
    assert snapshot.snapshot_reason == before["reason"]
    assert snapshot.disclaimer == before["disclaimer"]


def test_capture_creates_new_row_and_does_not_update_existing_snapshot_payload(db, auth_setup):
    appt = appointment(db)
    first = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Initial immutable payload.",
    )
    first_payload = list(first.items_json)

    second = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Second explicit capture.",
    )
    db.refresh(first)

    assert second.id != first.id
    assert first.items_json == first_payload
    assert first.snapshot_reason == "Initial immutable payload."
    assert db.query(ClinicalReadinessSnapshot).count() == 2


def test_supersession_requires_non_empty_reason(db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Initial snapshot.",
    )

    with pytest.raises(ValueError):
        supersede_clinical_readiness_snapshot(
            db,
            appointment_id=appt.id,
            old_snapshot_id=snapshot.id,
            actor_user_id=auth_setup["admin"].id,
            reason="   ",
        )


def test_supersession_requires_actor_user_id(db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Initial snapshot.",
    )

    with pytest.raises(ValueError):
        supersede_clinical_readiness_snapshot(
            db,
            appointment_id=appt.id,
            old_snapshot_id=snapshot.id,
            actor_user_id=None,
            reason="Needs human actor.",
        )


def test_supersession_rejects_unknown_old_snapshot(db, auth_setup):
    appt = appointment(db)

    with pytest.raises(LookupError):
        supersede_clinical_readiness_snapshot(
            db,
            appointment_id=appt.id,
            old_snapshot_id=999999,
            actor_user_id=auth_setup["admin"].id,
            reason="Unknown snapshot.",
        )


def test_supersession_rejects_wrong_appointment(db, auth_setup):
    appt = appointment(db)
    other_appt = appointment(db, room_obj=room(db, name="Supersession room"))
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Initial snapshot.",
    )

    with pytest.raises(LookupError):
        supersede_clinical_readiness_snapshot(
            db,
            appointment_id=other_appt.id,
            old_snapshot_id=snapshot.id,
            actor_user_id=auth_setup["admin"].id,
            reason="Wrong appointment.",
        )


def test_supersession_creates_new_snapshot_marks_old_and_writes_audit(client, db, auth_setup):
    appt = appointment(db, status="scheduled")
    original_status = appt.status
    old_snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Initial snapshot.",
    )
    old_payload = {
        "items": list(old_snapshot.items_json),
        "limitations": list(old_snapshot.limitations_json),
        "source_warnings": list(old_snapshot.source_warnings_json),
        "source_refs": list(old_snapshot.source_refs_json),
        "disclaimer": old_snapshot.disclaimer,
        "preview_status": old_snapshot.preview_status,
        "template_key": old_snapshot.template_key,
        "template_version": old_snapshot.template_version,
        "reason": old_snapshot.snapshot_reason,
    }
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))

    new_snapshot = supersede_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        old_snapshot_id=old_snapshot.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Novi pregled nakon dodatnih izvora.",
    )
    db.refresh(old_snapshot)

    assert new_snapshot.id != old_snapshot.id
    assert new_snapshot.appointment_id == appt.id
    assert new_snapshot.snapshot_reason == "Supersession: Novi pregled nakon dodatnih izvora."
    assert old_snapshot.superseded_by_snapshot_id == new_snapshot.id
    assert old_snapshot.superseded_at is not None
    assert old_snapshot.superseded_reason == "Novi pregled nakon dodatnih izvora."
    assert old_snapshot.items_json == old_payload["items"]
    assert old_snapshot.limitations_json == old_payload["limitations"]
    assert old_snapshot.source_warnings_json == old_payload["source_warnings"]
    assert old_snapshot.source_refs_json == old_payload["source_refs"]
    assert old_snapshot.disclaimer == old_payload["disclaimer"]
    assert old_snapshot.preview_status == old_payload["preview_status"]
    assert old_snapshot.template_key == old_payload["template_key"]
    assert old_snapshot.template_version == old_payload["template_version"]
    assert old_snapshot.snapshot_reason == old_payload["reason"]

    event = db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_SUPERSEDED_EVENT).one()
    assert event.entity_type == "ClinicalReadinessSnapshot"
    assert event.entity_id == old_snapshot.id
    assert event.summary == "Clinical Readiness Snapshot zamijenjen novim preview zapisom"
    payload = event.after_json
    assert payload["old_snapshot_id"] == old_snapshot.id
    assert payload["new_snapshot_id"] == new_snapshot.id
    assert payload["appointment_id"] == appt.id
    assert payload["patient_id"] == appt.patient_id
    assert payload["service_id"] == appt.service_id
    assert payload["superseded_by_user_id"] == auth_setup["admin"].id
    assert payload["supersede_reason"] == "Novi pregled nakon dodatnih izvora."
    assert payload["old_template_key"] == old_snapshot.template_key
    assert payload["new_template_key"] == new_snapshot.template_key
    assert payload["old_template_version"] == old_snapshot.template_version
    assert payload["new_template_version"] == new_snapshot.template_version
    assert payload["old_preview_status"] == old_snapshot.preview_status
    assert payload["new_preview_status"] == new_snapshot.preview_status
    assert payload["old_created_at"]
    assert payload["new_created_at"]
    assert payload["is_preview_snapshot"] is True

    db.expire(appt)
    assert appt.status == original_status
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "outcome_evidence" not in table_names
    assert "tasks" not in table_names

    history = history_endpoint(client, appt.id, auth_headers(client))
    assert history.status_code == 200
    history_items = history.json()["snapshots"]
    assert history_items[0]["id"] == new_snapshot.id
    old_history_item = next(item for item in history_items if item["id"] == old_snapshot.id)
    assert old_history_item["superseded_by_snapshot_id"] == new_snapshot.id
    assert old_history_item["superseded_at"] is not None
    assert old_history_item["superseded_reason"] == "Novi pregled nakon dodatnih izvora."

    detail = detail_endpoint(client, appt.id, old_snapshot.id, auth_headers(client))
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["items"] == old_payload["items"]
    assert detail_body["limitations"] == old_payload["limitations"]
    assert detail_body["source_warnings"] == old_payload["source_warnings"]
    assert detail_body["source_refs"] == old_payload["source_refs"]


def test_supersession_rejects_already_superseded_snapshot(db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Initial snapshot.",
    )
    supersede_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        old_snapshot_id=snapshot.id,
        actor_user_id=auth_setup["admin"].id,
        reason="First supersession.",
    )

    with pytest.raises(ValueError):
        supersede_clinical_readiness_snapshot(
            db,
            appointment_id=appt.id,
            old_snapshot_id=snapshot.id,
            actor_user_id=auth_setup["admin"].id,
            reason="Second supersession.",
        )


def test_supersession_rolls_back_new_snapshot_and_old_metadata_when_audit_fails(db, auth_setup, monkeypatch):
    import app.services.clinical_readiness_snapshots as snapshot_service

    appt = appointment(db)
    old_snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Initial snapshot.",
    )
    snapshot_count = db.query(ClinicalReadinessSnapshot).count()
    audit_count = db.query(AuditLog).count()

    def fail_supersession_audit(*args, **kwargs):
        if args[1] == CLINICAL_READINESS_SNAPSHOT_SUPERSEDED_EVENT:
            raise RuntimeError("supersession audit failed")
        return None

    monkeypatch.setattr(snapshot_service, "audit", fail_supersession_audit)

    with pytest.raises(RuntimeError):
        snapshot_service.supersede_clinical_readiness_snapshot(
            db,
            appointment_id=appt.id,
            old_snapshot_id=old_snapshot.id,
            actor_user_id=auth_setup["admin"].id,
            reason="Audit rollback.",
        )

    stored_old = db.get(ClinicalReadinessSnapshot, old_snapshot.id)
    assert db.query(ClinicalReadinessSnapshot).count() == snapshot_count
    assert db.query(AuditLog).count() == audit_count
    assert stored_old.superseded_by_snapshot_id is None
    assert stored_old.superseded_at is None
    assert stored_old.superseded_reason is None


def test_supersession_route_is_not_implemented_in_b23(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Future supersession metadata only.",
    )

    assert hasattr(snapshot, "superseded_by_snapshot_id")
    assert hasattr(snapshot, "superseded_at")
    assert hasattr(snapshot, "superseded_reason")
    assert client.post(
        f"/api/appointments/{appt.id}/clinical-readiness-snapshots/{snapshot.id}/supersede",
        headers=auth_headers(client),
        json={"reason": "Not implemented"},
    ).status_code in {404, 405}
