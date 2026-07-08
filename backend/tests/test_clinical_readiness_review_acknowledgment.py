from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.database import Base
from app.main import app
from app.schemas.common import ClinicalReadinessReviewAcknowledgment


FORBIDDEN_FIELDS = {
    "approval_status",
    "clearance_status",
    "override_status",
    "outcome_evidence_id",
    "task_id",
    "appointment_status",
    "patient_message_id",
    "procedure_approved",
    "patient_ready",
}


def acknowledgment() -> ClinicalReadinessReviewAcknowledgment:
    return ClinicalReadinessReviewAcknowledgment(
        acknowledgment_key="ack-missing-consent-review",
        advisory_signal_key="missing_consent_document",
        snapshot_id=42,
        appointment_id=7,
        patient_id=3,
        actor_role="physician",
        reason="Pregledan je savjetodavni signal i izvor treba provjeriti prije odluke.",
        created_at=datetime(2026, 7, 8, 12, 30, tzinfo=UTC),
    )


def test_review_acknowledgment_serialization_shape_is_safe():
    payload = acknowledgment().model_dump(mode="json")

    assert payload["is_decision"] is False
    assert payload["is_clearance"] is False
    assert payload["is_override"] is False
    assert "ne znaci odobrenje" in payload["not_decision_disclaimer"]
    assert FORBIDDEN_FIELDS.isdisjoint(payload.keys())
    assert set(payload) == {
        "acknowledgment_key",
        "advisory_signal_key",
        "snapshot_id",
        "appointment_id",
        "patient_id",
        "actor_role",
        "reason",
        "created_at",
        "limitations",
        "is_decision",
        "is_clearance",
        "is_override",
        "not_decision_disclaimer",
    }


def test_review_acknowledgment_requires_non_empty_reason():
    with pytest.raises(ValidationError):
        ClinicalReadinessReviewAcknowledgment(
            acknowledgment_key="ack-empty-reason",
            advisory_signal_key="missing_consent_document",
            appointment_id=7,
            patient_id=3,
            actor_role="physician",
            reason="   ",
            created_at=datetime(2026, 7, 8, 12, 30, tzinfo=UTC),
        )


@pytest.mark.parametrize("field_name", ["is_decision", "is_clearance", "is_override"])
def test_review_acknowledgment_rejects_positive_decision_flags(field_name: str):
    payload = acknowledgment().model_dump()
    payload[field_name] = True

    with pytest.raises(ValidationError):
        ClinicalReadinessReviewAcknowledgment(**payload)


def test_review_acknowledgment_forbids_extra_runtime_semantic_fields():
    payload = acknowledgment().model_dump()
    payload["approval_status"] = "approved"

    with pytest.raises(ValidationError):
        ClinicalReadinessReviewAcknowledgment(**payload)


def test_review_acknowledgment_schema_has_no_side_effect_contract_fields():
    fields = set(ClinicalReadinessReviewAcknowledgment.model_fields)

    assert FORBIDDEN_FIELDS.isdisjoint(fields)
    assert "appointment_status" not in fields
    assert "patient_message_id" not in fields


def test_review_acknowledgment_endpoint_does_not_exist():
    route_paths = {getattr(route, "path", "") for route in app.routes}

    assert "/api/clinical-readiness-review-acknowledgments" not in route_paths
    assert "/api/appointments/{appointment_id}/clinical-readiness-review-acknowledgments" not in route_paths
    assert all("acknowledgment" not in path for path in route_paths)


def test_review_acknowledgment_db_model_and_table_do_not_exist():
    table_names = set(Base.metadata.tables)
    mapper_class_names = {mapper.class_.__name__ for mapper in Base.registry.mappers}

    assert "clinical_readiness_review_acknowledgments" not in table_names
    assert "ClinicalReadinessReviewAcknowledgment" not in mapper_class_names
