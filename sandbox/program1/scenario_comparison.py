"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from .display import humanize_label, render_safety_banner
from .session_recap import SESSION_RECAP_REVIEW_NOTE
from .scenarios import build_scenario
from .workflow import build_workflow_summary


COMPARISON_TITLE = "Program 1 Synthetic Sandbox Scenario Comparison"
COMPARISON_PURPOSE = (
    "This local synthetic comparison shows how two demo scenarios differ for "
    "sandbox review. It does not compare real patients and does not support "
    "clinical decision-making."
)
COMPARISON_SUMMARY = (
    "Alpha demonstrates a synthetic review visit with more than one finding.",
    "Beta demonstrates a synthetic safety-boundary review.",
    (
        "Neither scenario contains real patient data, PHI, PII, diagnosis, "
        "treatment advice, triage, patient instruction, or clinical recommendation."
    ),
)


def _scenario_summary(name: str) -> dict[str, object]:
    _patient, _encounter, _findings, review = build_scenario(name)
    summary = build_workflow_summary(review)
    return {
        "patient": summary["patient"],
        "encounter": summary["encounter"],
        "findings": summary["findings"],
        "review_note": SESSION_RECAP_REVIEW_NOTE,
    }


def build_scenario_comparison() -> dict[str, object]:
    """Build a local synthetic scenario comparison without persistence or export."""

    return {
        "comparison_title": COMPARISON_TITLE,
        "comparison_purpose": COMPARISON_PURPOSE,
        "scenarios": {
            "alpha": _scenario_summary("alpha"),
            "beta": _scenario_summary("beta"),
        },
        "comparison_summary": list(COMPARISON_SUMMARY),
        "synthetic_only": True,
        "non_production": True,
        "clinical_use_authorized": False,
        "real_patient_data_allowed": False,
        "phi_pii_allowed": False,
        "persisted": False,
        "exported": False,
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


def render_scenario_comparison(comparison: dict[str, object]) -> str:
    """Render a clinician-readable local scenario comparison."""

    alpha = comparison["scenarios"]["alpha"]
    beta = comparison["scenarios"]["beta"]
    lines = [
        str(comparison["comparison_title"]),
        render_safety_banner().split("\n", 1)[1],
        "",
        "Comparison purpose:",
        str(comparison["comparison_purpose"]),
        "",
        "Scenario Alpha:",
        "Patient:",
        humanize_label(alpha["patient"]),
        "",
        "Encounter:",
        humanize_label(alpha["encounter"]),
        "",
        "Findings:",
    ]
    lines.extend(f"- {humanize_label(finding)}" for finding in alpha["findings"])
    lines.extend(
        [
            "",
            "Clinician review note:",
            str(alpha["review_note"]),
            "",
            "Scenario Beta:",
            "Patient:",
            humanize_label(beta["patient"]),
            "",
            "Encounter:",
            humanize_label(beta["encounter"]),
            "",
            "Findings:",
        ]
    )
    lines.extend(f"- {humanize_label(finding)}" for finding in beta["findings"])
    lines.extend(
        [
            "",
            "Clinician review note:",
            str(beta["review_note"]),
            "",
            "Comparison summary:",
        ]
    )
    lines.extend(f"- {item}" for item in comparison["comparison_summary"])
    lines.extend(
        [
            "",
            "Safety confirmations:",
            "- Real patient data: not allowed",
            "- PHI/PII: not allowed",
            "- Clinical use: not authorized",
            "- Persistence: disabled",
            "- Export: disabled",
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
