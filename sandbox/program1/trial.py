"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

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


def build_trial_packet(scenario: str = "alpha") -> dict[str, object]:
    """Build a local-only synthetic clinician trial packet."""

    _patient, _encounter, _findings, review = build_scenario(scenario)
    return {
        "safety_banner": SAFETY_BANNER,
        "scenario": scenario,
        "summary": build_workflow_summary(review),
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
        packet["safety_banner"],
        "No clinical use is authorized.",
        "",
        f"Scenario: {packet['scenario']}",
        f"Patient: {summary['patient']}",
        f"Encounter: {summary['encounter']}",
        "Findings:",
    ]
    lines.extend(f"- {finding}" for finding in summary["findings"])
    lines.extend(
        [
            f"Review note: {summary['review_note']}",
            "",
            "Clinician trial checklist:",
        ]
    )
    lines.extend(f"- {item}" for item in packet["trial_checklist"])
    lines.extend(
        [
            "",
            "Feedback template fields:",
        ]
    )
    lines.extend(f"- {key}" for key in packet["feedback_template"])
    lines.extend(
        [
            "",
            "Safety confirmations:",
            f"- clinical_use_authorized: {packet['clinical_use_authorized']}",
            f"- real_patient_data_allowed: {packet['real_patient_data_allowed']}",
            f"- phi_pii_allowed: {packet['phi_pii_allowed']}",
            f"- network_or_database_used: {packet['network_or_database_used']}",
            f"- external_integrations_enabled: {packet['external_integrations_enabled']}",
        ]
    )
    return "\n".join(lines)
