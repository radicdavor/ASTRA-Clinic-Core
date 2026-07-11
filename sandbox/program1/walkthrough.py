"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from .display import (
    humanize_label,
    render_allowed_state,
    render_authorized_state,
    render_enabled_state,
    render_safety_banner,
    review_note_for_scenario,
)
from .models import SAFETY_BANNER
from .scenarios import SCENARIOS, build_scenario
from .trial import TRIAL_CHECKLIST
from .workflow import build_workflow_summary


WALKTHROUGH_COMMANDS = (
    "python -m sandbox.program1.cli summary --scenario alpha",
    "python -m sandbox.program1.cli summary --scenario beta --json",
    "python -m sandbox.program1.cli trial --scenario alpha",
    "python -m sandbox.program1.cli trial --scenario beta --json",
    "python -m sandbox.program1.cli review-feedback",
)


def build_walkthrough_packet() -> dict[str, object]:
    """Build a local-only synthetic clinician walkthrough packet."""

    scenario_summaries: dict[str, dict[str, object]] = {}
    for name in sorted(SCENARIOS):
        _patient, _encounter, _findings, review = build_scenario(name)
        summary = build_workflow_summary(review)
        summary["scenario"] = name
        scenario_summaries[name] = summary
    return {
        "safety_banner": SAFETY_BANNER,
        "available_scenarios": sorted(SCENARIOS),
        "walkthrough_purpose": (
            "This terminal walkthrough shows how a clinician could inspect a "
            "synthetic Program 1 sandbox scenario without clinical use, real data, "
            "patient messaging, appointment changes, workflow action, or writeback."
        ),
        "scenario_summaries": scenario_summaries,
        "feedback_explanation": (
            "Feedback examples demonstrate how a clinician might comment on the "
            "sandbox design. They are local-only examples, not production records "
            "and not patient-care notes."
        ),
        "iteration_queue_explanation": (
            "The design iteration queue is for possible future sandbox design "
            "discussion only. It does not create clinical tasks, patient messages, "
            "appointment actions, workflow obligations, or implementation approval."
        ),
        "command_sequence": list(WALKTHROUGH_COMMANDS),
        "clinician_checklist": list(TRIAL_CHECKLIST),
        "local_only": True,
        "non_production": True,
        "clinical_use_authorized": False,
        "real_patient_data_allowed": False,
        "phi_pii_allowed": False,
        "cloud_ready": False,
        "network_or_database_used": False,
        "external_integrations_enabled": False,
        "patient_messaging_enabled": False,
        "appointment_mutation_enabled": False,
        "clinical_writeback_enabled": False,
        "approval_override_enabled": False,
        "go_live_authorized": False,
    }


def render_walkthrough(packet: dict[str, object]) -> str:
    """Render the local-only synthetic clinician walkthrough."""

    lines = [
        render_safety_banner(),
        "Local sandbox only. Non-production. Not for clinical use.",
        "",
        "What this walkthrough demonstrates:",
        str(packet["walkthrough_purpose"]),
        "",
        "Available synthetic scenarios:",
    ]
    lines.extend(
        f"- {str(scenario).title()}: "
        f"{humanize_label(packet['scenario_summaries'][scenario]['patient'])}"
        for scenario in packet["available_scenarios"]
    )
    lines.extend(["", "Clinician-readable scenario examples:"])
    for scenario in packet["available_scenarios"]:
        summary = packet["scenario_summaries"][scenario]
        lines.extend(
            [
                "",
                f"Scenario {str(scenario).title()}",
                f"Patient: {humanize_label(summary['patient'])}",
                f"Encounter: {humanize_label(summary['encounter'])}",
                "Findings:",
            ]
        )
        lines.extend(f"- {humanize_label(finding)}" for finding in summary["findings"])
        lines.extend(["Clinician review note:", review_note_for_scenario(scenario)])
    lines.extend(
        [
            "",
            "Feedback demonstration:",
            str(packet["feedback_explanation"]),
            "",
            "Design iteration queue:",
            str(packet["iteration_queue_explanation"]),
        ]
    )
    lines.extend(["", "Suggested local command sequence:"])
    lines.extend(f"- {command}" for command in packet["command_sequence"])
    lines.extend(["", "Recommended clinician checklist:"])
    lines.extend(f"- {humanize_label(item)}" for item in packet["clinician_checklist"])
    lines.extend(
        [
            "",
            "Safety confirmations:",
            "- Local-only sandbox: enabled",
            "- Non-production status: enabled",
            f"- Clinical use: {render_authorized_state(packet['clinical_use_authorized'])}",
            f"- Real patient data: {render_allowed_state(packet['real_patient_data_allowed'])}",
            f"- PHI/PII: {render_allowed_state(packet['phi_pii_allowed'])}",
            f"- Cloud readiness: {render_enabled_state(packet['cloud_ready'])}",
            f"- Network/database behavior: {render_enabled_state(packet['network_or_database_used'])}",
            f"- External integrations: {render_enabled_state(packet['external_integrations_enabled'])}",
            f"- Patient messaging: {render_enabled_state(packet['patient_messaging_enabled'])}",
            f"- Appointment mutation: {render_enabled_state(packet['appointment_mutation_enabled'])}",
            f"- Clinical writeback: {render_enabled_state(packet['clinical_writeback_enabled'])}",
            f"- Approval/override capability: {render_enabled_state(packet['approval_override_enabled'])}",
            f"- Go-live: {render_authorized_state(packet['go_live_authorized'])}",
        ]
    )
    return "\n".join(lines)
