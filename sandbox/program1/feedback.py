"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from dataclasses import dataclass

from .models import SyntheticDataError, require_synthetic_text


@dataclass(frozen=True)
class SyntheticTrialFeedback:
    """Structured local-only feedback for synthetic sandbox usability trials."""

    scenario_id: str
    reviewer_role: str
    workflow_clarity_score: int
    missing_information: str
    confusing_output: str
    usefulness_notes: str
    safety_concerns: str
    next_iteration_suggestions: str
    synthetic_only_confirmation: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "scenario_id", require_synthetic_text(self.scenario_id, "scenario_id")
        )
        object.__setattr__(
            self,
            "reviewer_role",
            require_synthetic_text(self.reviewer_role, "reviewer_role"),
        )
        for field_name in (
            "missing_information",
            "confusing_output",
            "usefulness_notes",
            "safety_concerns",
            "next_iteration_suggestions",
        ):
            object.__setattr__(
                self,
                field_name,
                require_synthetic_text(getattr(self, field_name), field_name),
            )
        if not 1 <= self.workflow_clarity_score <= 5:
            raise SyntheticDataError("workflow_clarity_score must be between 1 and 5.")
        if self.synthetic_only_confirmation is not True:
            raise SyntheticDataError("synthetic_only_confirmation must be true.")


def build_feedback_template(scenario_id: str = "SYNTHETIC_SCENARIO_ALPHA") -> dict[str, object]:
    """Return a synthetic-only local feedback template."""

    return {
        "scenario_id": require_synthetic_text(scenario_id, "scenario_id"),
        "reviewer_role": "DEMO_CLINICIAN_REVIEWER",
        "workflow_clarity_score": 3,
        "missing_information": "EXAMPLE_MISSING_INFORMATION_NOTE",
        "confusing_output": "EXAMPLE_CONFUSING_OUTPUT_NOTE",
        "usefulness_notes": "EXAMPLE_USEFULNESS_NOTES",
        "safety_concerns": "EXAMPLE_SAFETY_CONCERNS_NONE_REPORTED",
        "next_iteration_suggestions": "EXAMPLE_NEXT_ITERATION_SUGGESTIONS",
        "synthetic_only_confirmation": True,
    }


def validate_feedback(payload: dict[str, object]) -> SyntheticTrialFeedback:
    """Validate local synthetic feedback without writing files or calling services."""

    return SyntheticTrialFeedback(**payload)
