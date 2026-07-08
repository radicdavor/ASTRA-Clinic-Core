from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.main import app
from app.models import domain
from app.schemas.common import (
    CLINICAL_EVIDENCE_TIMELINE_EVENT_TYPES,
    CLINICAL_EVIDENCE_TIMELINE_SOURCE_TYPES,
    ClinicalEvidenceTimelineEventPreview,
    ClinicalEvidenceTimelineSourceReference,
)
from app.services.seed import PERMISSIONS


FORBIDDEN_TIMELINE_FIELDS = {
    "diagnosis_confirmed",
    "treatment_plan",
    "task_id",
    "outcome_evidence_id",
    "patient_message_id",
    "approval_status",
    "clearance_status",
    "override_status",
    "appointment_status",
    "resolved_by_ai",
}

FORBIDDEN_TIMELINE_EVENT_TYPES = {
    "diagnosis_confirmed_by_ai",
    "treatment_started_automatically",
    "patient_notified_automatically",
    "task_completed",
    "outcome_proven",
    "procedure_approved",
    "patient_cleared",
    "override_applied",
}


def timeline_source() -> ClinicalEvidenceTimelineSourceReference:
    return ClinicalEvidenceTimelineSourceReference(
        source_object_type="clinical_open_question",
        source_object_reference="clinical_open_question:7",
        patient_id=3,
        source_label="Open question",
        provenance_label="Source-linked open question",
        source_document_reference="clinical_document:42",
    )


def timeline_event() -> ClinicalEvidenceTimelineEventPreview:
    return ClinicalEvidenceTimelineEventPreview(
        event_key="timeline-open-question-7",
        event_type="open_question_awaiting_review",
        label="Open question awaiting review",
        source_reference=timeline_source(),
        event_timestamp=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
        display_timestamp=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
        requires_review=True,
        created_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC),
    )


def test_timeline_event_serialization_shape_is_safe():
    payload = timeline_event().model_dump(mode="json")

    assert FORBIDDEN_TIMELINE_FIELDS.isdisjoint(payload.keys())
    assert payload["is_decision"] is False
    assert payload["requires_review"] is True
    assert "nije diagnosis" in payload["no_decision_disclaimer"]
    assert payload["source_reference"]["source_object_type"] == "clinical_open_question"


def test_timeline_event_type_vocabulary_is_safe():
    assert FORBIDDEN_TIMELINE_EVENT_TYPES.isdisjoint(CLINICAL_EVIDENCE_TIMELINE_EVENT_TYPES)

    for event_type in CLINICAL_EVIDENCE_TIMELINE_EVENT_TYPES:
        item = timeline_event().model_copy(update={"event_type": event_type})
        assert item.event_type == event_type


def test_timeline_source_types_are_safe():
    assert "task" not in CLINICAL_EVIDENCE_TIMELINE_SOURCE_TYPES
    assert "outcome_evidence" not in CLINICAL_EVIDENCE_TIMELINE_SOURCE_TYPES
    assert "patient_message" not in CLINICAL_EVIDENCE_TIMELINE_SOURCE_TYPES


@pytest.mark.parametrize("event_type", sorted(FORBIDDEN_TIMELINE_EVENT_TYPES))
def test_timeline_rejects_forbidden_event_types(event_type: str):
    payload = timeline_event().model_dump()
    payload["event_type"] = event_type

    with pytest.raises(ValidationError):
        ClinicalEvidenceTimelineEventPreview(**payload)


def test_timeline_rejects_decision_semantics():
    payload = timeline_event().model_dump()
    payload["is_decision"] = True

    with pytest.raises(ValidationError):
        ClinicalEvidenceTimelineEventPreview(**payload)


def test_timeline_source_reference_is_required():
    payload = timeline_source().model_dump()
    payload["source_object_reference"] = " "

    with pytest.raises(ValidationError):
        ClinicalEvidenceTimelineSourceReference(**payload)


def test_timeline_forbids_runtime_semantic_fields():
    payload = timeline_event().model_dump()
    payload["approval_status"] = "approved"

    with pytest.raises(ValidationError):
        ClinicalEvidenceTimelineEventPreview(**payload)


def test_timeline_runtime_routes_models_services_permissions_do_not_exist():
    route_methods = {
        (getattr(route, "path", ""), tuple(sorted(getattr(route, "methods", []) or [])))
        for route in app.routes
    }
    forbidden_patient_timeline_paths = {
        "/api/patients/{patient_id}/clinical-evidence-timeline",
        "/api/patients/{patient_id}/clinical-evidence-timeline/{event_id}",
    }
    for path, methods in route_methods:
        if path in forbidden_patient_timeline_paths:
            assert not {"GET", "POST", "PATCH", "PUT", "DELETE"}.intersection(methods)

    repo = Path(__file__).resolve().parents[1]
    assert not hasattr(domain, "ClinicalEvidenceTimelineEvent")
    assert "clinical_evidence_timeline_events" not in domain.Base.metadata.tables
    service_text = (repo / "app" / "services" / "clinical_evidence_timeline.py").read_text(encoding="utf-8")
    assert "def create" not in service_text
    assert "def persist" not in service_text
    assert "def write" not in service_text
    assert "clinical_evidence_timeline.read" not in PERMISSIONS
