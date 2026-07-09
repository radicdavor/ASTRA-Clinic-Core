"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from dataclasses import asdict

from .feedback import build_feedback_template, validate_feedback
from .iteration_queue import SyntheticIterationQueueItem, build_iteration_queue
from .models import SAFETY_BANNER


def build_synthetic_feedback_examples() -> list[dict[str, object]]:
    """Return safe synthetic feedback examples for local review."""

    alpha = build_feedback_template("SYNTHETIC_SCENARIO_ALPHA")
    alpha.update(
        {
            "workflow_clarity_score": 3,
            "missing_information": "EXAMPLE_MISSING_INFORMATION_MORE_STEP_LABELS",
            "confusing_output": "EXAMPLE_CONFUSING_OUTPUT_REVIEW_NOTE_LABEL",
            "usefulness_notes": "EXAMPLE_USEFULNESS_NOTES_WORKFLOW_OVERVIEW_HELPFUL",
            "safety_concerns": "EXAMPLE_SAFETY_CONCERNS_BOUNDARY_VISIBLE",
            "next_iteration_suggestions": "EXAMPLE_NEXT_ITERATION_ADD_STEP_NUMBERS",
        }
    )
    beta = build_feedback_template("SYNTHETIC_SCENARIO_BETA")
    beta.update(
        {
            "workflow_clarity_score": 4,
            "missing_information": "EXAMPLE_MISSING_INFORMATION_NONE_FOR_SANDBOX",
            "confusing_output": "EXAMPLE_CONFUSING_OUTPUT_NONE_FOR_SANDBOX",
            "usefulness_notes": "EXAMPLE_USEFULNESS_NOTES_COMPARE_SCENARIOS",
            "safety_concerns": "EXAMPLE_SAFETY_CONCERNS_NONE_REPORTED",
            "next_iteration_suggestions": "EXAMPLE_NEXT_ITERATION_KEEP_SAFETY_FLAGS",
        }
    )
    return [alpha, beta]


def review_feedback(
    feedback_examples: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Validate synthetic feedback and build a local-only iteration queue."""

    examples = feedback_examples or build_synthetic_feedback_examples()
    validated = [validate_feedback(example) for example in examples]
    queue = build_iteration_queue([asdict(item) for item in validated])
    return {
        "safety_banner": SAFETY_BANNER,
        "summary": "DEMO_SUMMARY_SYNTHETIC_FEEDBACK_REVIEW_LOCAL_ONLY",
        "feedback_count": len(validated),
        "themes": sorted({item.theme for item in queue}),
        "iteration_queue": [asdict(item) for item in queue],
        "local_only": True,
        "network_or_database_used": False,
        "external_integrations_enabled": False,
        "clinical_use_authorized": False,
        "real_patient_data_allowed": False,
        "phi_pii_allowed": False,
    }


def render_feedback_review(review: dict[str, object]) -> str:
    """Render a local-only feedback review summary."""

    lines = [
        review["safety_banner"],
        "Local sandbox only. Not for clinical use.",
        "",
        f"Feedback examples reviewed: {review['feedback_count']}",
        "Recurring themes:",
    ]
    lines.extend(f"- {theme}" for theme in review["themes"])
    lines.append("")
    lines.append("Iteration queue:")
    for item in review["iteration_queue"]:
        lines.extend(
            [
                f"- {item['item_id']}: {item['theme']}",
                f"  proposed_change: {item['proposed_change']}",
                f"  safety_boundary: {item['safety_boundary']}",
                f"  prohibited_escalation: {item['prohibited_escalation']}",
                f"  status: {item['status']}",
            ]
        )
    lines.extend(
        [
            "",
            "Safety confirmations:",
            f"- local_only: {review['local_only']}",
            f"- network_or_database_used: {review['network_or_database_used']}",
            f"- external_integrations_enabled: {review['external_integrations_enabled']}",
            f"- clinical_use_authorized: {review['clinical_use_authorized']}",
            f"- real_patient_data_allowed: {review['real_patient_data_allowed']}",
            f"- phi_pii_allowed: {review['phi_pii_allowed']}",
        ]
    )
    return "\n".join(lines)
