from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.database import Base
from app.main import app
from app.schemas.common import (
    CLINICAL_FINDING_LIFECYCLE_STATUSES,
    ClinicalFindingPreview,
    ClinicalFindingSourceReference,
)


FORBIDDEN_FIELDS = {
    "diagnosis_confirmed",
    "treatment_plan",
    "patient_notified",
    "task_id",
    "outcome_evidence_id",
    "approval_status",
    "clearance_status",
    "resolved_by_ai",
    "appointment_status",
    "patient_message_id",
}

FORBIDDEN_STATUSES = {
    "approved",
    "cleared",
    "resolved_by_ai",
    "diagnosed_by_ai",
    "treatment_started",
    "patient_notified",
    "task_completed",
    "outcome_proven",
}


def finding() -> ClinicalFindingPreview:
    return ClinicalFindingPreview(
        finding_key="pathology-dysplasia-question",
        label="Pathology finding requires review",
        category="pathology",
        status="awaiting_review",
        source_reference=ClinicalFindingSourceReference(
            source_type="clinical_document",
            source_id=12,
            source_label="External pathology report",
            source_reference="clinical_document:12:key_findings:0",
            reviewed=False,
            extraction_method="manual_review",
            limitations=["Source requires physician review."],
        ),
        limitations=["Finding is not diagnosis by itself."],
        requires_review=True,
        created_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
    )


def test_clinical_finding_preview_serialization_shape_is_safe():
    payload = finding().model_dump(mode="json")

    assert FORBIDDEN_FIELDS.isdisjoint(payload.keys())
    assert payload["requires_review"] is True
    assert "nije automatska dijagnoza" in payload["not_decision_disclaimer"]
    assert set(payload) == {
        "finding_key",
        "label",
        "category",
        "status",
        "source_reference",
        "limitations",
        "requires_review",
        "created_at",
        "not_decision_disclaimer",
    }


def test_clinical_finding_status_vocabulary_is_safe():
    assert FORBIDDEN_STATUSES.isdisjoint(CLINICAL_FINDING_LIFECYCLE_STATUSES)

    for status in CLINICAL_FINDING_LIFECYCLE_STATUSES:
        item = finding().model_copy(update={"status": status})
        assert item.status == status


@pytest.mark.parametrize("status", sorted(FORBIDDEN_STATUSES))
def test_clinical_finding_rejects_forbidden_statuses(status: str):
    payload = finding().model_dump()
    payload["status"] = status

    with pytest.raises(ValidationError):
        ClinicalFindingPreview(**payload)


def test_clinical_finding_forbids_runtime_semantic_fields():
    payload = finding().model_dump()
    payload["diagnosis_confirmed"] = True

    with pytest.raises(ValidationError):
        ClinicalFindingPreview(**payload)


def test_clinical_finding_source_reference_is_source_linked_and_safe():
    source = finding().source_reference.model_dump()

    assert source["source_type"] == "clinical_document"
    assert source["source_id"] == 12
    assert source["reviewed"] is False
    assert FORBIDDEN_FIELDS.isdisjoint(source.keys())


def test_clinical_finding_runtime_routes_do_not_exist():
    route_paths = {getattr(route, "path", "") for route in app.routes}

    assert "/api/findings" not in route_paths
    assert "/api/patients/{patient_id}/findings" not in route_paths
    assert "/api/appointments/{appointment_id}/findings" not in route_paths


def test_clinical_finding_db_model_and_table_do_not_exist():
    table_names = set(Base.metadata.tables)
    mapper_class_names = {mapper.class_.__name__ for mapper in Base.registry.mappers}

    assert "clinical_findings" not in table_names
    assert "ClinicalFinding" not in mapper_class_names

