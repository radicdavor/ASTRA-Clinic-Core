from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.common import ClinicalReadinessAdvisorySignal


FORBIDDEN_FIELDS = {
    "approved",
    "cleared",
    "clearance",
    "override",
    "outcome_evidence_id",
    "task_id",
    "task_created",
    "patient_ready",
    "procedure_approved",
    "enforcement_result",
}


def advisory_signal() -> ClinicalReadinessAdvisorySignal:
    return ClinicalReadinessAdvisorySignal(
        signal_key="missing_consent_document",
        label="Nedostaje dokument za pregled",
        severity="review_required",
        category="documentation",
        source_type="clinical_readiness_preview",
        source_reference="preview:item:missing_consent_document",
        explanation="Potrebno je provjeriti izvor prije postupka.",
        limitations=["Demo/pilot advisory signal."],
        created_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
    )


def test_advisory_signal_serialization_shape_is_safe():
    payload = advisory_signal().model_dump(mode="json")

    assert payload["is_decision"] is False
    assert "nije klinicka odluka" in payload["not_decision_disclaimer"]
    assert FORBIDDEN_FIELDS.isdisjoint(payload.keys())
    assert set(payload) == {
        "signal_key",
        "label",
        "severity",
        "category",
        "source_type",
        "source_reference",
        "explanation",
        "limitations",
        "created_at",
        "is_decision",
        "not_decision_disclaimer",
    }


def test_advisory_signal_rejects_decision_semantics():
    with pytest.raises(ValidationError):
        ClinicalReadinessAdvisorySignal(
            signal_key="decision_attempt",
            label="Unsafe decision attempt",
            severity="warning",
            category="clinical_review",
            source_type="test",
            explanation="Should fail.",
            limitations=[],
            created_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
            is_decision=True,
        )


def test_advisory_signal_rejects_unknown_severity_and_category():
    with pytest.raises(ValidationError):
        ClinicalReadinessAdvisorySignal(
            signal_key="bad_status",
            label="Bad status",
            severity="cleared",
            category="clearance",
            source_type="test",
            explanation="Should fail.",
            limitations=[],
            created_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
