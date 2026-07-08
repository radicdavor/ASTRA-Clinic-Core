from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.database import Base
from app.main import app
from app.models.domain import ClinicalReadinessReviewAcknowledgment as ClinicalReadinessReviewAcknowledgmentModel
from app.schemas.common import (
    ClinicalReadinessAcknowledgmentDetailResponse,
    ClinicalReadinessAcknowledgmentListResponse,
    ClinicalReadinessAcknowledgmentReadItem,
    ClinicalReadinessReviewAcknowledgment,
    ClinicalReadinessReviewAcknowledgmentCreateRequest,
    ClinicalReadinessReviewAcknowledgmentResponse,
)
from app.services.seed import PERMISSIONS, ROLE_PERMISSIONS


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


def test_review_acknowledgment_write_endpoint_does_not_exist():
    route_paths = {getattr(route, "path", "") for route in app.routes}

    assert "/api/clinical-readiness-review-acknowledgments" not in route_paths
    assert "/api/appointments/{appointment_id}/clinical-readiness-review-acknowledgments" not in route_paths
    assert "/api/appointments/{appointment_id}/clinical-readiness/acknowledgments" in route_paths
    assert "/api/appointments/{appointment_id}/clinical-readiness/acknowledgments/{acknowledgment_id}" in route_paths
    write_methods = {"POST", "PATCH", "PUT", "DELETE"}
    for route in app.routes:
        if "acknowledgment" in getattr(route, "path", ""):
            assert write_methods.isdisjoint(getattr(route, "methods", set()))


def test_review_acknowledgment_db_model_and_table_do_not_exist():
    table_names = set(Base.metadata.tables)
    mapper_class_names = {mapper.class_.__name__ for mapper in Base.registry.mappers}

    assert "clinical_readiness_review_acknowledgments" in table_names
    assert "ClinicalReadinessReviewAcknowledgment" in mapper_class_names


def test_review_acknowledgment_write_permissions_are_not_seeded():
    forbidden_permissions = {
        "clinical_readiness.acknowledgments.write",
        "clinical_readiness.acknowledgments.manage",
    }

    assert "clinical_readiness.acknowledgments.read" in set(PERMISSIONS)
    assert forbidden_permissions.isdisjoint(set(PERMISSIONS))
    for permission_names in ROLE_PERMISSIONS.values():
        assert "clinical_readiness.acknowledgments.read" in set(PERMISSIONS)
        assert forbidden_permissions.isdisjoint(set(permission_names))


def test_review_acknowledgment_migration_is_not_present():
    migration_table_names = set(Base.metadata.tables)

    assert "clinical_readiness_review_acknowledgments" in migration_table_names


def test_review_acknowledgment_model_shape_is_safe_db_foundation():
    table = ClinicalReadinessReviewAcknowledgmentModel.__table__
    columns = set(table.columns.keys())

    assert {
        "id",
        "appointment_id",
        "patient_id",
        "snapshot_id",
        "advisory_signal_key",
        "actor_user_id",
        "actor_role",
        "reason",
        "limitations_json",
        "schema_version",
        "not_decision_disclaimer",
        "is_decision",
        "is_clearance",
        "is_override",
        "created_at",
    } <= columns
    assert FORBIDDEN_FIELDS.isdisjoint(columns)
    assert "resolved_at" not in columns


def test_review_acknowledgment_model_has_false_only_safety_constraints():
    constraint_sql = {str(constraint.sqltext) for constraint in ClinicalReadinessReviewAcknowledgmentModel.__table__.constraints if hasattr(constraint, "sqltext")}

    assert "length(trim(reason)) > 0" in constraint_sql
    assert "is_decision = false" in constraint_sql
    assert "is_clearance = false" in constraint_sql
    assert "is_override = false" in constraint_sql


def test_review_acknowledgment_migration_shape_has_no_forbidden_workflow_columns():
    repo_root = Path(__file__).resolve().parents[1]
    migration = repo_root / "alembic" / "versions" / "0017_acknowledgment_persistence_foundation.py"
    content = migration.read_text()

    assert "clinical_readiness_review_acknowledgments" in content
    assert "ck_clinical_readiness_review_acknowledgments_reason_non_empty" in content
    assert "ck_clinical_readiness_review_acknowledgments_not_decision" in content
    assert "ck_clinical_readiness_review_acknowledgments_not_clearance" in content
    assert "ck_clinical_readiness_review_acknowledgments_not_override" in content
    assert "approval_status" not in content
    assert "clearance_status" not in content
    assert "override_status" not in content
    assert "outcome_evidence_id" not in content
    assert "task_id" not in content
    assert "patient_message_id" not in content
    assert "appointment_status" not in content
    assert "resolved_at" not in content


def test_review_acknowledgment_create_request_shape_is_passive_and_safe():
    request = ClinicalReadinessReviewAcknowledgmentCreateRequest(
        advisory_signal_key="missing_consent_document",
        snapshot_id=42,
        reason="Pregledati signal prije klinicke odluke.",
        client_context_key="appointment-workspace",
        idempotency_key="ack-demo-key",
    )
    payload = request.model_dump(mode="json")

    assert payload["reason"] == "Pregledati signal prije klinicke odluke."
    assert FORBIDDEN_FIELDS.isdisjoint(payload.keys())
    assert set(payload) == {
        "advisory_signal_key",
        "snapshot_id",
        "reason",
        "client_context_key",
        "idempotency_key",
    }


def test_review_acknowledgment_create_request_requires_reason_and_forbids_extra_fields():
    with pytest.raises(ValidationError):
        ClinicalReadinessReviewAcknowledgmentCreateRequest(
            advisory_signal_key="missing_consent_document",
            reason=" ",
        )

    with pytest.raises(ValidationError):
        ClinicalReadinessReviewAcknowledgmentCreateRequest(
            advisory_signal_key="missing_consent_document",
            reason="Pregledano.",
            approval_status="approved",
        )


def test_review_acknowledgment_response_shape_is_passive_and_safe():
    response = ClinicalReadinessReviewAcknowledgmentResponse(
        acknowledgment_key="ack-missing-consent-review",
        advisory_signal_key="missing_consent_document",
        snapshot_id=42,
        appointment_id=7,
        patient_id=3,
        actor_role="physician",
        reason="Pregledan je savjetodavni signal.",
        created_at=datetime(2026, 7, 8, 12, 30, tzinfo=UTC),
    )
    payload = response.model_dump(mode="json")

    assert payload["is_decision"] is False
    assert payload["is_clearance"] is False
    assert payload["is_override"] is False
    assert "ne predstavlja clinical approval" in payload["warning"]
    assert FORBIDDEN_FIELDS.isdisjoint(payload.keys())


@pytest.mark.parametrize("field_name", ["is_decision", "is_clearance", "is_override"])
def test_review_acknowledgment_response_rejects_positive_runtime_flags(field_name: str):
    payload = ClinicalReadinessReviewAcknowledgmentResponse(
        acknowledgment_key="ack-missing-consent-review",
        advisory_signal_key="missing_consent_document",
        appointment_id=7,
        patient_id=3,
        actor_role="physician",
        reason="Pregledan je savjetodavni signal.",
        created_at=datetime(2026, 7, 8, 12, 30, tzinfo=UTC),
    ).model_dump()
    payload[field_name] = True

    with pytest.raises(ValidationError):
        ClinicalReadinessReviewAcknowledgmentResponse(**payload)


def read_item_payload() -> dict:
    return {
        "id": 1,
        "acknowledgment_key": "ack-1",
        "appointment_id": 7,
        "patient_id": 3,
        "advisory_signal_key": "no_reviewed_clinical_documents",
        "snapshot_id": None,
        "actor_user_id": 11,
        "actor_role": "physician",
        "reason": "Pregledan je savjetodavni signal.",
        "limitations": ["Acknowledgment je read-only prikaz ljudskog pregleda signala."],
        "schema_version": "acknowledgment.v1",
        "created_at": datetime(2026, 7, 8, 12, 30, tzinfo=UTC),
        "safe_disclaimer": "Acknowledgment nije clinical approval, readiness clearance ili override.",
    }


def test_acknowledgment_read_item_shape_is_safe():
    payload = ClinicalReadinessAcknowledgmentReadItem(**read_item_payload()).model_dump(mode="json")

    assert payload["acknowledgment_key"] == "ack-1"
    assert payload["is_decision"] is False
    assert payload["is_clearance"] is False
    assert payload["is_override"] is False
    assert FORBIDDEN_FIELDS.isdisjoint(payload.keys())
    assert "resolved_at" not in payload


@pytest.mark.parametrize("field_name", ["is_decision", "is_clearance", "is_override"])
def test_acknowledgment_read_item_rejects_positive_runtime_flags(field_name: str):
    payload = read_item_payload()
    payload[field_name] = True

    with pytest.raises(ValidationError):
        ClinicalReadinessAcknowledgmentReadItem(**payload)


def test_acknowledgment_list_response_shape_is_read_only():
    item = ClinicalReadinessAcknowledgmentReadItem(**read_item_payload())
    response = ClinicalReadinessAcknowledgmentListResponse(
        appointment_id=7,
        acknowledgments=[item],
        count=1,
        is_read_only=True,
        warning="Read-only prikaz; nije odobrenje ili clearance.",
    )
    payload = response.model_dump(mode="json")

    assert payload["is_read_only"] is True
    assert payload["count"] == 1
    assert "acknowledgments" in payload
    assert "approval_status" not in payload
    assert "appointment_status" not in payload


def test_acknowledgment_detail_response_shape_is_safe():
    response = ClinicalReadinessAcknowledgmentDetailResponse(
        **read_item_payload(),
        warning="Acknowledgment ne predstavlja clinical approval, readiness clearance, override, Outcome Evidence ili dozvolu za postupak.",
    )
    payload = response.model_dump(mode="json")

    assert payload["warning"]
    assert payload["is_decision"] is False
    assert payload["is_clearance"] is False
    assert payload["is_override"] is False
    assert FORBIDDEN_FIELDS.isdisjoint(payload.keys())
    assert "resolved_at" not in payload
