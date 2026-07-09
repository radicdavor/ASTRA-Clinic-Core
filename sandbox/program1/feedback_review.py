"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from dataclasses import asdict

from .display import (
    humanize_label,
    render_allowed_state,
    render_authorized_state,
    render_enabled_state,
    render_safety_banner,
)
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
        render_safety_banner(),
        "Local sandbox only. Not for clinical use.",
        (
            "Example feedback is shown only to demonstrate how a clinician might "
            "comment on the sandbox design. It is not stored in a production system, "
            "not sent to anyone, and not used for patient care."
        ),
        "",
        f"Feedback examples reviewed: {review['feedback_count']}",
        "Recurring themes:",
    ]
    lines.extend(f"- {humanize_label(theme)}" for theme in review["themes"])
    lines.append("")
    lines.append("Design iteration queue:")
    for item in review["iteration_queue"]:
        lines.extend(
            [
                f"- {humanize_label(item['item_id'])}: {humanize_label(item['theme'])}",
                (
                    "  This item demonstrates a possible future design discussion item. "
                    "It does not create a clinical task, appointment action, patient "
                    "message, or workflow obligation."
                ),
                f"  Proposed change: {humanize_label(item['proposed_change'])}",
                f"  Safety boundary: {humanize_label(item['safety_boundary'])}",
                f"  Prohibited escalation: {humanize_label(item['prohibited_escalation'])}",
                f"  Status: {humanize_label(item['status'])}",
            ]
        )
    lines.extend(
        [
            "",
            "Safety confirmations:",
            "- Local-only sandbox: enabled",
            f"- Network/database behavior: {render_enabled_state(review['network_or_database_used'])}",
            f"- External integrations: {render_enabled_state(review['external_integrations_enabled'])}",
            f"- Clinical use: {render_authorized_state(review['clinical_use_authorized'])}",
            f"- Real patient data: {render_allowed_state(review['real_patient_data_allowed'])}",
            f"- PHI/PII: {render_allowed_state(review['phi_pii_allowed'])}",
        ]
    )
    return "\n".join(lines)
