from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.main import app
from app.schemas.common import (
    ClinicalFindingExtractionBatchPreview,
    ClinicalFindingExtractionCandidate,
    ClinicalFindingExtractionSource,
)


FORBIDDEN_EXTRACTION_FIELDS = {
    "diagnosis_confirmed",
    "treatment_plan",
    "patient_instruction",
    "task_id",
    "outcome_evidence_id",
    "patient_message_id",
    "approval_status",
    "clearance_status",
    "auto_persist",
    "auto_notify",
    "resolved_by_ai",
}


def extraction_source() -> ClinicalFindingExtractionSource:
    return ClinicalFindingExtractionSource(
        source_document_id=42,
        source_type="clinical_document",
        source_label="External pathology report",
        source_reference="clinical_document:42:key_findings:0",
        text_span_reference="raw_text:120-180",
        page_reference="page:1",
        section_reference="key_findings",
        extraction_method="manual_contract_preview",
        extracted_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
        limitations=["Source text requires physician review."],
    )


def extraction_candidate() -> ClinicalFindingExtractionCandidate:
    return ClinicalFindingExtractionCandidate(
        candidate_key="candidate-pathology-dysplasia",
        label="Possible dysplasia mention requires review",
        category="pathology",
        source=extraction_source(),
        confidence_label="unknown",
        limitations=["Candidate is not diagnosis and is not persisted."],
        created_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC),
    )


def test_extraction_candidate_serialization_shape_is_safe():
    payload = extraction_candidate().model_dump(mode="json")

    assert FORBIDDEN_EXTRACTION_FIELDS.isdisjoint(payload.keys())
    assert payload["requires_human_review"] is True
    assert payload["is_persisted"] is False
    assert payload["suggested_lifecycle_status"] == "awaiting_review"
    assert "nije dijagnoza" in payload["not_decision_disclaimer"]
    assert set(payload) == {
        "candidate_key",
        "label",
        "category",
        "source",
        "confidence_label",
        "limitations",
        "requires_human_review",
        "suggested_lifecycle_status",
        "created_at",
        "is_persisted",
        "not_decision_disclaimer",
    }


def test_extraction_source_requires_traceability():
    payload = extraction_source().model_dump()
    payload["source_reference"] = " "

    with pytest.raises(ValidationError):
        ClinicalFindingExtractionSource(**payload)


@pytest.mark.parametrize("field,value", [
    ("requires_human_review", False),
    ("is_persisted", True),
    ("suggested_lifecycle_status", "reviewed"),
    ("confidence_label", "clinical_certain"),
])
def test_extraction_candidate_rejects_unsafe_semantics(field: str, value):
    payload = extraction_candidate().model_dump()
    payload[field] = value

    with pytest.raises(ValidationError):
        ClinicalFindingExtractionCandidate(**payload)


def test_extraction_candidate_forbids_runtime_semantic_fields():
    payload = extraction_candidate().model_dump()
    payload["auto_persist"] = True

    with pytest.raises(ValidationError):
        ClinicalFindingExtractionCandidate(**payload)


def test_extraction_batch_preview_is_not_runtime_extraction():
    batch = ClinicalFindingExtractionBatchPreview(
        clinical_document_id=42,
        patient_id=7,
        candidates=[extraction_candidate()],
    )

    payload = batch.model_dump(mode="json")
    assert payload["is_runtime_extraction"] is False
    assert "ne sprema findings" in payload["warning"]

    with pytest.raises(ValidationError):
        ClinicalFindingExtractionBatchPreview(
            clinical_document_id=42,
            patient_id=7,
            candidates=[extraction_candidate()],
            is_runtime_extraction=True,
        )


def test_finding_extraction_runtime_routes_do_not_exist():
    route_methods = {
        (getattr(route, "path", ""), tuple(sorted(getattr(route, "methods", []) or [])))
        for route in app.routes
    }
    forbidden_paths = {
        "/api/clinical-findings/extract",
        "/api/patients/{patient_id}/clinical-findings/extract",
        "/api/clinical-documents/{document_id}/finding-candidates",
        "/api/clinical-documents/{document_id}/findings/extract",
    }

    for path, methods in route_methods:
        assert path not in forbidden_paths or not {"GET", "POST", "PATCH", "PUT", "DELETE"}.intersection(methods)


def test_finding_extraction_service_is_absent():
    repo = Path(__file__).resolve().parents[2]

    assert not (repo / "app" / "services" / "clinical_finding_extraction.py").exists()
