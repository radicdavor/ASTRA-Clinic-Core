from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.main import app
from app.models import domain
from app.schemas.common import (
    CLINICAL_OPEN_QUESTION_STATUSES,
    ClinicalOpenQuestionPreview,
    ClinicalOpenQuestionSourceReference,
)


FORBIDDEN_OPEN_QUESTION_FIELDS = {
    "task_id",
    "outcome_evidence_id",
    "diagnosis_confirmed",
    "treatment_plan",
    "patient_message_id",
    "approval_status",
    "clearance_status",
    "resolved_by_ai",
    "auto_close",
}

FORBIDDEN_OPEN_QUESTION_STATUSES = {
    "resolved_by_ai",
    "diagnosed",
    "treated",
    "patient_notified",
    "task_completed",
    "outcome_confirmed",
    "approved",
    "cleared",
    "overridden",
}


def question_source() -> ClinicalOpenQuestionSourceReference:
    return ClinicalOpenQuestionSourceReference(
        source_type="clinical_document",
        source_label="External pathology report",
        source_reference="clinical_document:42:key_findings:0",
        source_document_id=42,
        source_finding_key="pathology-dysplasia-question",
        extraction_candidate_key="candidate-pathology-dysplasia",
        confidence_label="unknown",
        limitations=["Question source requires physician interpretation."],
    )


def open_question() -> ClinicalOpenQuestionPreview:
    return ClinicalOpenQuestionPreview(
        question_key="open-question-pathology-follow-up",
        label="Does pathology require follow-up decision?",
        status="awaiting_review",
        source_reference=question_source(),
        linked_finding_key="pathology-dysplasia-question",
        limitations=["Open question is not diagnosis or recommendation."],
        created_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
    )


def test_open_question_preview_serialization_shape_is_safe():
    payload = open_question().model_dump(mode="json")

    assert FORBIDDEN_OPEN_QUESTION_FIELDS.isdisjoint(payload.keys())
    assert payload["requires_clinician_review"] is True
    assert payload["is_persisted"] is False
    assert "nije Task" in payload["not_decision_disclaimer"]
    assert set(payload) == {
        "question_key",
        "label",
        "status",
        "source_reference",
        "linked_finding_key",
        "limitations",
        "requires_clinician_review",
        "created_at",
        "is_persisted",
        "not_decision_disclaimer",
    }


def test_open_question_status_vocabulary_is_safe():
    assert FORBIDDEN_OPEN_QUESTION_STATUSES.isdisjoint(CLINICAL_OPEN_QUESTION_STATUSES)

    for status in CLINICAL_OPEN_QUESTION_STATUSES:
        item = open_question().model_copy(update={"status": status})
        assert item.status == status


@pytest.mark.parametrize("status", sorted(FORBIDDEN_OPEN_QUESTION_STATUSES))
def test_open_question_rejects_forbidden_statuses(status: str):
    payload = open_question().model_dump()
    payload["status"] = status

    with pytest.raises(ValidationError):
        ClinicalOpenQuestionPreview(**payload)


@pytest.mark.parametrize("field,value", [
    ("requires_clinician_review", False),
    ("is_persisted", True),
])
def test_open_question_rejects_unsafe_flags(field: str, value: bool):
    payload = open_question().model_dump()
    payload[field] = value

    with pytest.raises(ValidationError):
        ClinicalOpenQuestionPreview(**payload)


def test_open_question_source_reference_is_required():
    payload = question_source().model_dump()
    payload["source_reference"] = " "

    with pytest.raises(ValidationError):
        ClinicalOpenQuestionSourceReference(**payload)


def test_open_question_forbids_runtime_semantic_fields():
    payload = open_question().model_dump()
    payload["task_id"] = 123

    with pytest.raises(ValidationError):
        ClinicalOpenQuestionPreview(**payload)


def test_open_question_runtime_routes_do_not_exist():
    route_methods = {
        (getattr(route, "path", ""), tuple(sorted(getattr(route, "methods", []) or [])))
        for route in app.routes
    }
    forbidden_paths = {
        "/api/open-questions",
        "/api/patients/{patient_id}/open-questions",
        "/api/findings/{finding_id}/open-questions",
        "/api/clinical-findings/{finding_id}/open-questions",
    }

    for path, methods in route_methods:
        assert path not in forbidden_paths or not {"GET", "POST", "PATCH", "PUT", "DELETE"}.intersection(methods)


def test_open_question_db_model_table_and_service_are_absent():
    repo = Path(__file__).resolve().parents[2]

    assert not hasattr(domain, "ClinicalOpenQuestion")
    assert "clinical_open_questions" not in domain.Base.metadata.tables
    assert not (repo / "app" / "services" / "clinical_open_questions.py").exists()

