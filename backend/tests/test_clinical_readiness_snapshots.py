from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.domain import AuditLog, ClinicalEpisode, ClinicalPlan, ClinicalReadinessSnapshot
from tests.factories import appointment


DISCLAIMER = "Snapshot je zapis preview prikaza, ne clinical approval."


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
