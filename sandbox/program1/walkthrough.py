"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from .models import SAFETY_BANNER
from .scenarios import SCENARIOS
from .trial import TRIAL_CHECKLIST


WALKTHROUGH_COMMANDS = (
    "python -m sandbox.program1.cli summary --scenario alpha",
    "python -m sandbox.program1.cli summary --scenario beta --json",
    "python -m sandbox.program1.cli trial --scenario alpha",
    "python -m sandbox.program1.cli trial --scenario beta --json",
    "python -m sandbox.program1.cli review-feedback",
)


def build_walkthrough_packet() -> dict[str, object]:
    """Build a local-only synthetic clinician walkthrough packet."""

    return {
        "safety_banner": SAFETY_BANNER,
        "available_scenarios": sorted(SCENARIOS),
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
        packet["safety_banner"],
        "Local sandbox only. Non-production. Not for clinical use.",
        "",
        "Available synthetic scenarios:",
    ]
    lines.extend(f"- {scenario}" for scenario in packet["available_scenarios"])
    lines.extend(["", "Suggested local command sequence:"])
    lines.extend(f"- {command}" for command in packet["command_sequence"])
    lines.extend(["", "Recommended clinician checklist:"])
    lines.extend(f"- {item}" for item in packet["clinician_checklist"])
    lines.extend(
        [
            "",
            "Safety confirmations:",
            f"- local_only: {packet['local_only']}",
            f"- non_production: {packet['non_production']}",
            f"- clinical_use_authorized: {packet['clinical_use_authorized']}",
            f"- real_patient_data_allowed: {packet['real_patient_data_allowed']}",
            f"- phi_pii_allowed: {packet['phi_pii_allowed']}",
            f"- cloud_ready: {packet['cloud_ready']}",
            f"- network_or_database_used: {packet['network_or_database_used']}",
            f"- external_integrations_enabled: {packet['external_integrations_enabled']}",
            f"- patient_messaging_enabled: {packet['patient_messaging_enabled']}",
            f"- appointment_mutation_enabled: {packet['appointment_mutation_enabled']}",
            f"- clinical_writeback_enabled: {packet['clinical_writeback_enabled']}",
            f"- approval_override_enabled: {packet['approval_override_enabled']}",
            f"- go_live_authorized: {packet['go_live_authorized']}",
        ]
    )
    return "\n".join(lines)
