from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.domain import AuditLog, ClinicalEpisode, ClinicalPlan, ClinicalReadinessSnapshot, PatientClinicalSummaryRecord
from app.services.clinical_readiness_snapshots import (
    CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT,
    CLINICAL_READINESS_SNAPSHOT_DISCLAIMER,
    capture_clinical_readiness_snapshot,
)
from tests.conftest import login_token
from tests.factories import appointment, clinical_document, service


DISCLAIMER = "Snapshot je zapis preview prikaza, ne clinical approval."


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def preview(client, appointment_id, headers):
    return client.get(f"/api/appointments/{appointment_id}/clinical-readiness-preview", headers=headers)


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
