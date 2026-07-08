from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.main import app
from app.models import domain
from app.schemas.common import (
    CLINICAL_REVIEW_OBJECT_TYPES,
    CLINICAL_REVIEW_STATUSES,
    ClinicalReviewPreview,
    ClinicalReviewSourceReference,
)
from app.services.seed import PERMISSIONS


FORBIDDEN_REVIEW_FIELDS = {
    "approval_status",
    "clearance_status",
    "override_status",
    "diagnosis_confirmed",
    "treatment_plan",
    "task_id",
    "outcome_evidence_id",
    "patient_message_id",
    "appointment_status",
    "resolved_by_ai",
}

FORBIDDEN_REVIEW_STATUSES = {
    "approved",
    "cleared",
    "overridden",
    "diagnosed",
    "treated",
    "patient_notified",
    "task_completed",
    "outcome_confirmed",
    "resolved_by_ai",
}


def review_source() -> ClinicalReviewSourceReference:
    return ClinicalReviewSourceReference(
        source_type="clinical_document",
        source_label="External pathology report",
        source_reference="clinical_document:42:key_findings:0",
        reviewed_object_type="open_question",
        reviewed_object_reference="clinical_open_question:7",
    )


def review_preview() -> ClinicalReviewPreview:
    return ClinicalReviewPreview(
        review_key="review-open-question-7",
        reviewed_object_type="open_question",
        reviewed_object_reference="clinical_open_question:7",
        status="awaiting_review",
        source_reference=review_source(),
        created_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
    )


def test_review_preview_serialization_shape_is_safe():
    payload = review_preview().model_dump(mode="json")

    assert FORBIDDEN_REVIEW_FIELDS.isdisjoint(payload.keys())
    assert payload["requires_clinician_decision"] is True
    assert payload["is_persisted"] is False
    assert "nije approval" in payload["no_decision_disclaimer"]
    assert payload["source_reference"]["reviewed_object_type"] == "open_question"


def test_review_status_vocabulary_is_safe():
    assert FORBIDDEN_REVIEW_STATUSES.isdisjoint(CLINICAL_REVIEW_STATUSES)

    for status in CLINICAL_REVIEW_STATUSES:
        item = review_preview().model_copy(update={"status": status})
        assert item.status == status


def test_review_object_types_are_source_linked():
    assert {"clinical_document", "finding", "open_question", "extraction_candidate"}.issubset(CLINICAL_REVIEW_OBJECT_TYPES)
    assert "task" not in CLINICAL_REVIEW_OBJECT_TYPES
    assert "outcome_evidence" not in CLINICAL_REVIEW_OBJECT_TYPES
    assert "patient_message" not in CLINICAL_REVIEW_OBJECT_TYPES


@pytest.mark.parametrize("status", sorted(FORBIDDEN_REVIEW_STATUSES))
def test_review_rejects_forbidden_statuses(status: str):
    payload = review_preview().model_dump()
    payload["status"] = status

    with pytest.raises(ValidationError):
        ClinicalReviewPreview(**payload)


@pytest.mark.parametrize("field,value", [
    ("requires_clinician_decision", False),
    ("is_persisted", True),
])
def test_review_rejects_unsafe_flags(field: str, value: bool):
    payload = review_preview().model_dump()
    payload[field] = value

    with pytest.raises(ValidationError):
        ClinicalReviewPreview(**payload)


def test_review_source_reference_is_required():
    payload = review_source().model_dump()
    payload["source_reference"] = " "

    with pytest.raises(ValidationError):
        ClinicalReviewSourceReference(**payload)


def test_review_forbids_runtime_semantic_fields():
    payload = review_preview().model_dump()
    payload["approval_status"] = "approved"

    with pytest.raises(ValidationError):
        ClinicalReviewPreview(**payload)


def test_review_runtime_routes_models_services_permissions_do_not_exist():
    route_methods = {
        (getattr(route, "path", ""), tuple(sorted(getattr(route, "methods", []) or [])))
        for route in app.routes
    }
    for path, methods in route_methods:
        if "clinical-review" in path or "clinical_reviews" in path or "review-workflow" in path:
            assert not {"POST", "PATCH", "PUT", "DELETE"}.intersection(methods)

    repo = Path(__file__).resolve().parents[1]
    assert not hasattr(domain, "ClinicalReview")
    assert "clinical_reviews" not in domain.Base.metadata.tables
    assert not (repo / "app" / "services" / "clinical_reviews.py").exists()
    assert "clinical_reviews.read" not in PERMISSIONS
    assert "clinical_reviews.review" not in PERMISSIONS
