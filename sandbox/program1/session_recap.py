"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from .display import HUMAN_REVIEW_NOTE, humanize_label, render_safety_banner
from .feedback_input import build_feedback_input_preview
from .scenarios import build_scenario
from .workflow import build_workflow_summary


SESSION_RECAP_REVIEW_NOTE = (
    "This sandbox shows where a clinician would review the synthetic finding. "
    "No diagnosis, treatment, triage, patient messaging, appointment changes, "
    "workflow action, or clinical writeback is made."
)

DESIGN_ITERATION_NOTE = (
    "This recap may help discuss future sandbox design improvements. It does "
    "not create a clinical task, appointment action, patient message, workflow "
    "obligation, or implementation approval."
)


def build_session_recap(
    scenario: str = "alpha",
    feedback: str | None = None,
) -> dict[str, object]:
    """Build a local-only synthetic session recap without persistence or export."""

    _patient, _encounter, _findings, review = build_scenario(scenario)
    summary = build_workflow_summary(review)
    feedback_preview = build_feedback_input_preview(feedback)
    return {
        "scenario": scenario,
        "patient": summary["patient"],
        "encounter": summary["encounter"],
        "findings": summary["findings"],
        "review_note": HUMAN_REVIEW_NOTE,
        "display_review_note": SESSION_RECAP_REVIEW_NOTE,
        "feedback_preview": feedback_preview["entered_feedback"],
        "feedback_entered": not feedback_preview["empty_feedback"],
        "feedback_boundary": feedback_preview["interpretation"],
        "design_iteration_note": DESIGN_ITERATION_NOTE,
        "synthetic_only": True,
        "non_production": True,
        "clinical_use_authorized": False,
        "real_patient_data_allowed": False,
        "phi_pii_allowed": False,
        "persisted": False,
        "sent_externally": False,
        "network_or_database_used": False,
        "patient_message_created": False,
        "appointment_mutation_performed": False,
        "workflow_enforced": False,
        "clinical_writeback_performed": False,
        "clinical_task_created": False,
        "approval_override_created": False,
        "go_live_authorized": False,
    }


def render_session_recap(recap: dict[str, object]) -> str:
    """Render a one-screen local synthetic session recap."""

    lines = [
        "Program 1 Synthetic Sandbox Session Recap",
        render_safety_banner().split("\n", 1)[1],
        "",
        "Scenario:",
        str(recap["scenario"]).title(),
        "",
        "Patient:",
        humanize_label(recap["patient"]),
        "",
        "Encounter:",
        humanize_label(recap["encounter"]),
        "",
        "Findings:",
    ]
    lines.extend(f"- {humanize_label(finding)}" for finding in recap["findings"])
    lines.extend(
        [
            "",
            "Clinician review note:",
            str(recap["display_review_note"]),
            "",
            "Synthetic feedback preview:",
        ]
    )
    if recap["feedback_entered"]:
        lines.append(f'"{recap["feedback_preview"]}"')
    else:
        lines.append("No feedback text was entered. No data was stored or transmitted.")
    lines.extend(
        [
            "",
            "Feedback boundary:",
            str(recap["feedback_boundary"]),
            "",
            "Design iteration note:",
            str(recap["design_iteration_note"]),
            "",
            "Safety confirmations:",
            "- Real patient data: not allowed",
            "- PHI/PII: not allowed",
            "- Clinical use: not authorized",
            "- Persistence: disabled",
            "- Transmission: disabled",
            "- Network/database: disabled",
            "- Patient messaging: disabled",
            "- Appointment mutation: disabled",
            "- Workflow enforcement: disabled",
            "- Clinical writeback: disabled",
            "- Clinical task creation: disabled",
            "- Approval/override capability: disabled",
            "- Go-live authorization: disabled",
        ]
    )
    return "\n".join(lines)
