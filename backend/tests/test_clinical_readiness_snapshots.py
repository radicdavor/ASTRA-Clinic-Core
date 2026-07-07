from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import hash_api_key
from app.core.security import hash_password
from app.models.domain import (
    ApiKey,
    AuditLog,
    ClinicalEpisode,
    ClinicalPlan,
    ClinicalReadinessSnapshot,
    PatientClinicalSummaryRecord,
    Permission,
    Role,
    User,
)
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


def supersede_endpoint(client, appointment_id, snapshot_id, headers, payload=None):
    return client.post(
        f"/api/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}/supersede",
        headers=headers,
        json=payload if payload is not None else {"reason": "Endpoint supersession reason."},
    )


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


def test_supersession_endpoint_requires_authentication(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Endpoint auth.",
    )

    response = supersede_endpoint(client, appt.id, snapshot.id, headers={})

    assert response.status_code == 401


def test_supersession_endpoint_requires_supersede_permission(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Endpoint permission.",
    )
    headers = {"Authorization": f"Bearer {login_token(client, 'limited@test.local')}"}

    response = supersede_endpoint(client, appt.id, snapshot.id, headers=headers)

    assert response.status_code == 403
    assert "clinical_readiness.snapshots.supersede" in response.json()["detail"]


def test_api_key_supersession_denied_even_with_snapshot_scope(client, db):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=1,
        reason="API key old snapshot.",
    )
    api_key = ApiKey(
        name="Snapshot supersession integration",
        key_hash=hash_api_key("raw-supersession-key"),
        scopes=["clinical_readiness.snapshots.supersede"],
        active=True,
    )
    db.add(api_key)
    db.commit()

    response = supersede_endpoint(
        client,
        appt.id,
        snapshot.id,
        headers={"X-ASTRA-API-Key": "raw-supersession-key"},
    )

    assert response.status_code == 403
    db.refresh(snapshot)
    assert snapshot.superseded_by_snapshot_id is None


def test_supersession_endpoint_requires_reason(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Endpoint reason.",
    )

    response = supersede_endpoint(client, appt.id, snapshot.id, headers=auth_headers(client), payload={"reason": "   "})

    assert response.status_code == 422


def test_supersession_endpoint_supersedes_snapshot_without_workflow_side_effects(client, db, auth_setup):
    appt = appointment(db, status="scheduled")
    original_status = appt.status
    old_snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Endpoint initial snapshot.",
    )
    old_payload = {
        "items": list(old_snapshot.items_json),
        "limitations": list(old_snapshot.limitations_json),
        "source_warnings": list(old_snapshot.source_warnings_json),
        "source_refs": list(old_snapshot.source_refs_json),
        "reason": old_snapshot.snapshot_reason,
    }
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))

    response = supersede_endpoint(
        client,
        appt.id,
        old_snapshot.id,
        headers=auth_headers(client),
        payload={"reason": "Endpoint supersession."},
    )

    assert response.status_code == 200
    body = response.json()
    new_snapshot = db.get(ClinicalReadinessSnapshot, body["new_snapshot"]["id"])
    db.refresh(old_snapshot)
    assert new_snapshot is not None
    assert body["old_snapshot_id"] == old_snapshot.id
    assert body["new_snapshot"]["appointment_id"] == appt.id
    assert body["new_snapshot"]["snapshot_reason"] == "Supersession: Endpoint supersession."
    assert body["superseded_at"] is not None
    assert body["superseded_reason"] == "Endpoint supersession."
    assert "Ne predstavlja clinical approval" in body["warning"]
    forbidden = {"approved", "cleared", "procedure_allowed", "task_created", "outcome_evidence_id", "override_status"}
    assert forbidden.isdisjoint(body.keys())
    assert forbidden.isdisjoint(body["new_snapshot"].keys())
    assert old_snapshot.superseded_by_snapshot_id == new_snapshot.id
    assert old_snapshot.superseded_at is not None
    assert old_snapshot.superseded_reason == "Endpoint supersession."
    assert old_snapshot.items_json == old_payload["items"]
    assert old_snapshot.limitations_json == old_payload["limitations"]
    assert old_snapshot.source_warnings_json == old_payload["source_warnings"]
    assert old_snapshot.source_refs_json == old_payload["source_refs"]
    assert old_snapshot.snapshot_reason == old_payload["reason"]

    event = db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_SUPERSEDED_EVENT).one()
    assert event.entity_id == old_snapshot.id
    assert event.after_json["old_snapshot_id"] == old_snapshot.id
    assert event.after_json["new_snapshot_id"] == new_snapshot.id
    assert event.after_json["supersede_reason"] == "Endpoint supersession."

    db.expire(appt)
    assert appt.status == original_status
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "outcome_evidence" not in table_names
    assert "tasks" not in table_names

    history = history_endpoint(client, appt.id, auth_headers(client))
    assert history.status_code == 200
    old_history_item = next(item for item in history.json()["snapshots"] if item["id"] == old_snapshot.id)
    assert old_history_item["superseded_by_snapshot_id"] == new_snapshot.id

    detail = detail_endpoint(client, appt.id, old_snapshot.id, auth_headers(client))
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["items"] == old_payload["items"]
    assert detail_body["limitations"] == old_payload["limitations"]
    assert detail_body["source_warnings"] == old_payload["source_warnings"]
    assert detail_body["source_refs"] == old_payload["source_refs"]


def test_supersession_endpoint_rejects_wrong_appointment(client, db, auth_setup):
    appt = appointment(db)
    other_appt = appointment(db, room_obj=room(db, name="Wrong endpoint room"))
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Wrong appointment endpoint.",
    )

    response = supersede_endpoint(client, other_appt.id, snapshot.id, headers=auth_headers(client))

    assert response.status_code == 404


def test_supersession_endpoint_rejects_already_superseded_snapshot(client, db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Already superseded endpoint.",
    )
    first = supersede_endpoint(client, appt.id, snapshot.id, headers=auth_headers(client), payload={"reason": "First endpoint supersession."})
    second = supersede_endpoint(client, appt.id, snapshot.id, headers=auth_headers(client), payload={"reason": "Second endpoint supersession."})

    assert first.status_code == 200
    assert second.status_code == 409


def test_supersession_endpoint_keeps_normal_capture_working(client, db, auth_setup):
    appt = appointment(db)

    response = capture_endpoint(client, appt.id, headers=auth_headers(client), payload={"reason": "Normal capture still works."})

    assert response.status_code == 200
    assert response.json()["snapshot_reason"] == "Normal capture still works."


def test_db_invariant_rejects_snapshot_payload_and_capture_metadata_mutation(db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Immutable capture reason.",
    )
    original_items = list(snapshot.items_json)
    original_reason = snapshot.snapshot_reason

    snapshot.items_json = [{"key": "tampered", "label": "Tampered payload"}]

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()
    stored = db.get(ClinicalReadinessSnapshot, snapshot.id)
    assert stored.items_json == original_items
    assert stored.snapshot_reason == original_reason

    stored.snapshot_reason = "Mutated reason."

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()
    stored = db.get(ClinicalReadinessSnapshot, snapshot.id)
    assert stored.snapshot_reason == original_reason


def test_db_invariant_rejects_snapshot_appointment_and_patient_reassignment(db, auth_setup):
    appt = appointment(db)
    other_appt = appointment(db, room_obj=room(db, name="Immutable reassignment room"))
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Immutable linkage.",
    )
    original_appointment_id = snapshot.appointment_id
    original_patient_id = snapshot.patient_id

    snapshot.appointment_id = other_appt.id

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()
    stored = db.get(ClinicalReadinessSnapshot, snapshot.id)
    assert stored.appointment_id == original_appointment_id
    assert stored.patient_id == original_patient_id

    stored.patient_id = other_appt.patient_id

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()
    stored = db.get(ClinicalReadinessSnapshot, snapshot.id)
    assert stored.appointment_id == original_appointment_id
    assert stored.patient_id == original_patient_id


def test_db_invariant_allows_first_supersession_but_rejects_reassignment(db, auth_setup):
    appt = appointment(db)
    old_snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Initial immutable supersession snapshot.",
    )
    new_snapshot = supersede_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        old_snapshot_id=old_snapshot.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Allowed first supersession.",
    )
    replacement_attempt = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Replacement attempt.",
    )
    db.refresh(old_snapshot)

    assert old_snapshot.superseded_by_snapshot_id == new_snapshot.id
    assert old_snapshot.superseded_reason == "Allowed first supersession."
    old_snapshot.superseded_by_snapshot_id = replacement_attempt.id
    old_snapshot.superseded_reason = "Reassigned supersession."

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()
    stored = db.get(ClinicalReadinessSnapshot, old_snapshot.id)
    assert stored.superseded_by_snapshot_id == new_snapshot.id
    assert stored.superseded_reason == "Allowed first supersession."


def test_db_invariant_rejects_snapshot_row_deletion(db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Deletion guard.",
    )
    snapshot_id = snapshot.id
    snapshot_count = db.query(ClinicalReadinessSnapshot).count()

    db.delete(snapshot)

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()
    assert db.get(ClinicalReadinessSnapshot, snapshot_id) is not None
    assert db.query(ClinicalReadinessSnapshot).count() == snapshot_count


def test_snapshot_lifecycle_end_to_end_without_workflow_side_effects(client, db, auth_setup):
    colonoscopy = service(db, name="Kolonoskopija")
    appt = appointment(db, service_obj=colonoscopy, status="scheduled")
    clinical_document(db, appt.patient, physician_reviewed=True)
    original_status = appt.status
    initial_snapshot_count = db.query(ClinicalReadinessSnapshot).count()
    initial_audit_count = db.query(AuditLog).count()
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))
    headers = auth_headers(client)

    preview_response = preview(client, appt.id, headers)

    assert preview_response.status_code == 200
    assert db.query(ClinicalReadinessSnapshot).count() == initial_snapshot_count
    assert db.query(AuditLog).count() == initial_audit_count

    capture_response = capture_endpoint(
        client,
        appt.id,
        headers=headers,
        payload={"reason": "End-to-end capture.", "idempotency_key": "e2e-key"},
    )

    assert capture_response.status_code == 200
    captured_body = capture_response.json()
    captured_snapshot = db.get(ClinicalReadinessSnapshot, captured_body["id"])
    assert captured_snapshot is not None
    assert captured_snapshot.items_json == captured_body["items"]
    assert db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT).count() == 1

    retry_response = capture_endpoint(
        client,
        appt.id,
        headers=headers,
        payload={"reason": "End-to-end capture.", "idempotency_key": "e2e-key"},
    )

    assert retry_response.status_code == 200
    assert retry_response.json()["id"] == captured_snapshot.id
    assert db.query(ClinicalReadinessSnapshot).count() == initial_snapshot_count + 1
    assert db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT).count() == 1

    history_after_capture = history_endpoint(client, appt.id, headers)
    assert history_after_capture.status_code == 200
    assert history_after_capture.json()["snapshots"][0]["id"] == captured_snapshot.id

    detail_after_capture = detail_endpoint(client, appt.id, captured_snapshot.id, headers)
    assert detail_after_capture.status_code == 200
    old_payload = {
        "items": detail_after_capture.json()["items"],
        "limitations": detail_after_capture.json()["limitations"],
        "source_warnings": detail_after_capture.json()["source_warnings"],
        "source_refs": detail_after_capture.json()["source_refs"],
    }

    supersede_response = supersede_endpoint(
        client,
        appt.id,
        captured_snapshot.id,
        headers=headers,
        payload={"reason": "End-to-end supersession."},
    )

    assert supersede_response.status_code == 200
    new_snapshot_id = supersede_response.json()["new_snapshot"]["id"]
    new_snapshot = db.get(ClinicalReadinessSnapshot, new_snapshot_id)
    db.refresh(captured_snapshot)
    assert new_snapshot is not None
    assert captured_snapshot.superseded_by_snapshot_id == new_snapshot.id
    assert captured_snapshot.items_json == old_payload["items"]
    assert captured_snapshot.limitations_json == old_payload["limitations"]
    assert captured_snapshot.source_warnings_json == old_payload["source_warnings"]
    assert captured_snapshot.source_refs_json == old_payload["source_refs"]

    history_after_supersession = history_endpoint(client, appt.id, headers)
    assert history_after_supersession.status_code == 200
    history_items = history_after_supersession.json()["snapshots"]
    assert history_items[0]["id"] == new_snapshot.id
    old_history_item = next(item for item in history_items if item["id"] == captured_snapshot.id)
    assert old_history_item["superseded_by_snapshot_id"] == new_snapshot.id

    old_detail_after_supersession = detail_endpoint(client, appt.id, captured_snapshot.id, headers)
    assert old_detail_after_supersession.status_code == 200
    assert old_detail_after_supersession.json()["items"] == old_payload["items"]
    assert old_detail_after_supersession.json()["limitations"] == old_payload["limitations"]
    assert old_detail_after_supersession.json()["source_warnings"] == old_payload["source_warnings"]
    assert old_detail_after_supersession.json()["source_refs"] == old_payload["source_refs"]

    capture_event = db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT).one()
    assert capture_event.entity_id == captured_snapshot.id
    assert db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_SNAPSHOT_SUPERSEDED_EVENT).count() == 1
    db.expire(appt)
    assert appt.status == original_status
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "outcome_evidence" not in table_names
    assert "tasks" not in table_names
    assert "patient_messages" not in table_names


def test_snapshot_permission_matrix_regression(client, db, auth_setup):
    read_permission = db.query(Permission).filter(Permission.name == "clinical_readiness.snapshots.read").one()
    write_permission = db.query(Permission).filter(Permission.name == "clinical_readiness.snapshots.write").one()
    supersede_permission = db.query(Permission).filter(Permission.name == "clinical_readiness.snapshots.supersede").one()
    read_role = Role(name="snapshot-read-only", description="Snapshot read only", permissions=[read_permission])
    write_role = Role(name="snapshot-write-only", description="Snapshot write only", permissions=[write_permission])
    supersede_role = Role(name="snapshot-supersede-only", description="Snapshot supersede only", permissions=[supersede_permission])
    read_user = User(
        email="snapshot-read@test.local",
        full_name="Snapshot Read",
        password_hash=hash_password("secret"),
        role=read_role,
    )
    write_user = User(
        email="snapshot-write@test.local",
        full_name="Snapshot Write",
        password_hash=hash_password("secret"),
        role=write_role,
    )
    supersede_user = User(
        email="snapshot-supersede@test.local",
        full_name="Snapshot Supersede",
        password_hash=hash_password("secret"),
        role=supersede_role,
    )
    db.add_all([read_role, write_role, supersede_role, read_user, write_user, supersede_user])
    db.commit()

    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Permission matrix initial snapshot.",
    )
    read_headers = {"Authorization": f"Bearer {login_token(client, 'snapshot-read@test.local')}"}
    write_headers = {"Authorization": f"Bearer {login_token(client, 'snapshot-write@test.local')}"}
    supersede_headers = {"Authorization": f"Bearer {login_token(client, 'snapshot-supersede@test.local')}"}
    limited_headers = {"Authorization": f"Bearer {login_token(client, 'limited@test.local')}"}

    assert history_endpoint(client, appt.id, read_headers).status_code == 200
    assert detail_endpoint(client, appt.id, snapshot.id, read_headers).status_code == 200
    assert capture_endpoint(client, appt.id, read_headers, payload={"reason": "Read-only capture attempt."}).status_code == 403

    write_capture = capture_endpoint(client, appt.id, write_headers, payload={"reason": "Write-only capture."})
    assert write_capture.status_code == 200
    assert supersede_endpoint(client, appt.id, snapshot.id, write_headers, payload={"reason": "Write-only supersede attempt."}).status_code == 403

    supersede_response = supersede_endpoint(
        client,
        appt.id,
        snapshot.id,
        supersede_headers,
        payload={"reason": "Supersede-only action."},
    )
    assert supersede_response.status_code == 200

    assert history_endpoint(client, appt.id, limited_headers).status_code == 403
    assert detail_endpoint(client, appt.id, snapshot.id, limited_headers).status_code == 403
    assert capture_endpoint(client, appt.id, limited_headers, payload={"reason": "Limited capture attempt."}).status_code == 403

    api_key = ApiKey(
        name="Snapshot matrix API key",
        key_hash=hash_api_key("matrix-api-key"),
        scopes=["clinical_readiness.snapshots.write", "clinical_readiness.snapshots.supersede"],
        active=True,
    )
    db.add(api_key)
    db.commit()
    api_headers = {"X-ASTRA-API-Key": "matrix-api-key"}

    assert capture_endpoint(client, appt.id, api_headers, payload={"reason": "API capture attempt."}).status_code == 403
    assert supersede_endpoint(client, appt.id, write_capture.json()["id"], api_headers, payload={"reason": "API supersede attempt."}).status_code == 403

    admin_capture = capture_endpoint(client, appt.id, auth_headers(client), payload={"reason": "Admin still allowed."})
    assert admin_capture.status_code == 200
