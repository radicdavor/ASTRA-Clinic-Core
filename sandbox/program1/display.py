"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from .models import SAFETY_BANNER


HUMAN_REVIEW_NOTE = (
    "This sandbox shows where a clinician would review the synthetic finding. "
    "The note is intentionally non-clinical and does not recommend diagnosis, "
    "treatment, triage, patient messaging, appointment changes, workflow action, "
    "or clinical writeback."
)

SCENARIO_REVIEW_NOTES = {
    "gamma": (
        "This sandbox shows where a clinician would notice incomplete synthetic "
        "context. No diagnosis, treatment, triage, patient messaging, appointment "
        "changes, workflow action, or clinical writeback is made."
    ),
    "delta": (
        "This sandbox shows where a clinician would notice conflicting synthetic "
        "information. No diagnosis, treatment, triage, patient messaging, "
        "appointment changes, workflow action, or clinical writeback is made."
    ),
    "epsilon": (
        "This sandbox shows where safety boundaries are reviewed in a synthetic "
        "scenario. No diagnosis, treatment, triage, patient messaging, "
        "appointment changes, workflow action, or clinical writeback is made."
    ),
}

SCENARIO_PURPOSES = {
    "alpha": "Baseline synthetic review visit with more than one finding.",
    "beta": "Safety-boundary review for existing local sandbox behavior.",
    "gamma": (
        "Demonstrates incomplete documentation context without creating clinical "
        "recommendations or tasks."
    ),
    "delta": (
        "Demonstrates conflicting synthetic information without resolving it "
        "clinically or creating an action."
    ),
    "epsilon": (
        "Demonstrates disabled action boundaries without patient messages, "
        "clinical tasks, appointment changes, workflow actions, or writeback."
    ),
}

HUMAN_LABELS = {
    "DEMO_ONLY_PATIENT_ALPHA": "Synthetic patient A",
    "DEMO_ONLY_PATIENT_BETA": "Synthetic patient B",
    "DEMO_ONLY_PATIENT_GAMMA": "Synthetic patient C",
    "DEMO_ONLY_PATIENT_DELTA": "Synthetic patient D",
    "DEMO_ONLY_PATIENT_EPSILON": "Synthetic patient E",
    "DEMO_ENCOUNTER_SYNTHETIC_REVIEW": "Example review visit",
    "DEMO_ENCOUNTER_SYNTHETIC_BOUNDARY_CHECK": "Boundary review visit",
    "DEMO_ENCOUNTER_INCOMPLETE_DOCUMENTATION_REVIEW": (
        "Incomplete documentation review visit"
    ),
    "DEMO_ENCOUNTER_CONFLICTING_INFORMATION_REVIEW": (
        "Conflicting information review visit"
    ),
    "DEMO_ENCOUNTER_SAFETY_BOUNDARY_STRESS_REVIEW": (
        "Safety-boundary stress review visit"
    ),
    "DEMO_FINDING_CONTEXT_REVIEW": "Missing context in uploaded record",
    "DEMO_FINDING_FOLLOWUP_PLACEHOLDER": "Follow-up context placeholder",
    "DEMO_FINDING_BOUNDARY_VISIBILITY": "Visibility of safety boundary",
    "DEMO_FINDING_MISSING_SOURCE_DOCUMENT_CONTEXT": "Missing source document context",
    "DEMO_FINDING_MISSING_PRIOR_REVIEW_REFERENCE": "Missing prior review reference",
    "DEMO_FINDING_CONFLICTING_SYNTHETIC_NOTE_CONTEXT": (
        "Conflicting synthetic note context"
    ),
    "DEMO_FINDING_FOLLOWUP_CLARIFICATION_PLACEHOLDER": (
        "Follow-up clarification placeholder"
    ),
    "DEMO_FINDING_PATIENT_FACING_ACTION_REMAINS_DISABLED": (
        "Patient-facing action remains disabled"
    ),
    "DEMO_FINDING_CLINICAL_WORKFLOW_ACTION_REMAINS_DISABLED": (
        "Clinical workflow action remains disabled"
    ),
    "DEMO_THEME_WORKFLOW_CLARITY": "Workflow clarity",
    "DEMO_THEME_USEFULNESS_REVIEW": "Perceived usefulness",
    "EXAMPLE_CHANGE_CLARIFY_SYNTHETIC_SUMMARY_OUTPUT": (
        "Clarify the synthetic summary output for easier review"
    ),
    "EXAMPLE_CHANGE_KEEP_SANDBOX_BOUNDARY_VISIBLE": (
        "Keep the sandbox-only safety boundary visible throughout the walkthrough"
    ),
    "DEMO_BOUNDARY_SYNTHETIC_LOCAL_ONLY": "Synthetic local sandbox only",
    "DEMO_PROHIBIT_PRODUCTION_CLINICAL_REAL_DATA_ESCALATION": (
        "No production, clinical, or real-data escalation"
    ),
    "DEMO_STATUS_PROPOSED_FOR_FUTURE_SANDBOX_REVIEW": (
        "Proposed for future sandbox design review"
    ),
}


def review_note_for_scenario(scenario: object) -> str:
    """Return clinician-readable non-clinical review note text for a scenario."""

    return SCENARIO_REVIEW_NOTES.get(str(scenario), HUMAN_REVIEW_NOTE)

HUMAN_CHECKLIST = {
    "DEMO_CHECKLIST_CONFIRM_SYNTHETIC_ONLY": "Confirm the scenario is synthetic only",
    "DEMO_CHECKLIST_REVIEW_SCENARIO_SUMMARY": "Review the scenario summary",
    "DEMO_CHECKLIST_NOTE_MISSING_WORKFLOW_STEPS": "Note missing workflow steps",
    "DEMO_CHECKLIST_NOTE_CONFUSING_OUTPUT": "Note confusing output",
    "DEMO_CHECKLIST_NOTE_PERCEIVED_USEFULNESS": "Note perceived usefulness",
    "DEMO_CHECKLIST_CONFIRM_NO_CLINICAL_USE_AUTHORIZED": (
        "Confirm that no clinical use is authorized"
    ),
}

SAFETY_CONFIRMATION_LABELS = {
    "real_patient_data_allowed": "Real patient data",
    "phi_pii_allowed": "PHI/PII",
    "clinical_use_authorized": "Clinical use",
    "patient_messaging_enabled": "Patient messaging",
    "appointment_mutation_enabled": "Appointment mutation",
    "clinical_writeback_enabled": "Clinical writeback",
    "approval_override_enabled": "Approval/override capability",
    "go_live_authorized": "Go-live",
    "network_or_database_used": "Network/database behavior",
    "external_integrations_enabled": "External integrations",
    "cloud_ready": "Cloud readiness",
}


def render_safety_banner() -> str:
    """Return the local sandbox safety banner."""

    return (
        "Program 1 Synthetic Sandbox\n"
        f"Status: {SAFETY_BANNER}"
    )


def humanize_label(value: object) -> str:
    """Translate internal synthetic labels into clinician-readable display text."""

    text = str(value)
    if text in HUMAN_LABELS:
        return HUMAN_LABELS[text]
    if text in HUMAN_CHECKLIST:
        return HUMAN_CHECKLIST[text]
    if text.startswith("SYNTHETIC_QUEUE_ITEM_"):
        suffix = text.rsplit("_", 1)[-1].lower()
        return f"Design iteration queue item {suffix}"
    return (
        text.replace("SYNTHETIC_", "")
        .replace("DEMO_", "")
        .replace("EXAMPLE_", "")
        .replace("_", " ")
        .strip()
        .title()
    )


def render_allowed_state(value: object) -> str:
    """Render a boolean safety value as an allowed/not allowed phrase."""

    return "allowed" if value is True else "not allowed"


def render_enabled_state(value: object) -> str:
    """Render a boolean safety value as an enabled/disabled phrase."""

    return "enabled" if value is True else "disabled"


def render_authorized_state(value: object) -> str:
    """Render a boolean safety value as an authorized/not authorized phrase."""

    return "authorized" if value is True else "not authorized"
