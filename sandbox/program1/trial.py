"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from .display import (
    HUMAN_REVIEW_NOTE,
    humanize_label,
    render_allowed_state,
    render_authorized_state,
    render_enabled_state,
    render_safety_banner,
)
from .feedback import build_feedback_template
from .models import SAFETY_BANNER
from .scenarios import build_scenario
from .workflow import build_workflow_summary


TRIAL_CHECKLIST = (
    "DEMO_CHECKLIST_CONFIRM_SYNTHETIC_ONLY",
    "DEMO_CHECKLIST_REVIEW_SCENARIO_SUMMARY",
    "DEMO_CHECKLIST_NOTE_MISSING_WORKFLOW_STEPS",
    "DEMO_CHECKLIST_NOTE_CONFUSING_OUTPUT",
    "DEMO_CHECKLIST_NOTE_PERCEIVED_USEFULNESS",
    "DEMO_CHECKLIST_CONFIRM_NO_CLINICAL_USE_AUTHORIZED",
)

FEEDBACK_FIELD_LABELS = {
    "scenario_id": "Scenario being reviewed",
    "reviewer_role": "Reviewer role",
    "workflow_clarity_score": "Workflow clarity score",
    "missing_information": "Missing information",
    "confusing_output": "Confusing output",
    "usefulness_notes": "Usefulness notes",
    "safety_concerns": "Safety concerns",
    "next_iteration_suggestions": "Next iteration suggestions",
    "synthetic_only_confirmation": "Synthetic-only confirmation",
}


def build_trial_packet(scenario: str = "alpha") -> dict[str, object]:
    """Build a local-only synthetic clinician trial packet."""

    _patient, _encounter, _findings, review = build_scenario(scenario)
    summary = build_workflow_summary(review)
    summary["scenario"] = scenario
    return {
        "safety_banner": SAFETY_BANNER,
        "scenario": scenario,
        "summary": summary,
        "trial_checklist": list(TRIAL_CHECKLIST),
        "feedback_template": build_feedback_template(
            f"SYNTHETIC_SCENARIO_{scenario.upper()}"
        ),
        "clinical_use_authorized": False,
        "real_patient_data_allowed": False,
        "phi_pii_allowed": False,
        "network_or_database_used": False,
        "external_integrations_enabled": False,
    }


def render_trial_packet(packet: dict[str, object]) -> str:
    """Render a local-only synthetic clinician trial packet."""

    summary = packet["summary"]
    lines = [
        render_safety_banner(),
        "No clinical use is authorized.",
        "",
        f"Scenario: {str(packet['scenario']).title()}",
        "",
        "Patient:",
        humanize_label(summary["patient"]),
        "",
        "Encounter:",
        humanize_label(summary["encounter"]),
        "",
        "Findings:",
    ]
    lines.extend(f"- {humanize_label(finding)}" for finding in summary["findings"])
    lines.extend(
        [
            "",
            "Clinician review note:",
            HUMAN_REVIEW_NOTE,
            "",
            "Clinician trial checklist:",
        ]
    )
    lines.extend(f"- {humanize_label(item)}" for item in packet["trial_checklist"])
    lines.extend(
        [
            "",
            "Feedback template fields:",
        ]
    )
    lines.extend(
        f"- {FEEDBACK_FIELD_LABELS.get(key, humanize_label(key))}"
        for key in packet["feedback_template"]
    )
    lines.extend(
        [
            "",
            "Safety confirmations:",
            f"- Clinical use: {render_authorized_state(packet['clinical_use_authorized'])}",
            f"- Real patient data: {render_allowed_state(packet['real_patient_data_allowed'])}",
            f"- PHI/PII: {render_allowed_state(packet['phi_pii_allowed'])}",
            f"- Network/database behavior: {render_enabled_state(packet['network_or_database_used'])}",
            f"- External integrations: {render_enabled_state(packet['external_integrations_enabled'])}",
        ]
    )
    return "\n".join(lines)
