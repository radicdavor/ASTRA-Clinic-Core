"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from datetime import date

from .models import SyntheticEncounter, SyntheticFinding, SyntheticPatient
from .workflow import build_clinician_review_note


def build_synthetic_review_scenario_alpha():
    """Build the baseline synthetic review scenario."""

    patient = SyntheticPatient(
        synthetic_patient_id="SYNTHETIC_PATIENT_ALPHA",
        display_label="DEMO_ONLY_PATIENT_ALPHA",
    )
    encounter = SyntheticEncounter(
        encounter_id="SYNTHETIC_ENCOUNTER_ALPHA",
        patient=patient,
        encounter_label="DEMO_ENCOUNTER_SYNTHETIC_REVIEW",
        encounter_date=date(2099, 1, 1),
        findings=(
            SyntheticFinding(
                finding_id="SYNTHETIC_FINDING_CONTEXT",
                title="DEMO_FINDING_CONTEXT_REVIEW",
                summary="EXAMPLE_FINDING_SUMMARY_FOR_SYNTHETIC_WORKFLOW_ONLY",
            ),
            SyntheticFinding(
                finding_id="SYNTHETIC_FINDING_FOLLOWUP",
                title="DEMO_FINDING_FOLLOWUP_PLACEHOLDER",
                summary="EXAMPLE_FINDING_REVIEW_PLACEHOLDER_NOT_CLINICAL_ADVICE",
            ),
        ),
    )
    review = build_clinician_review_note(
        encounter,
        reviewer_label="DEMO_CLINICIAN_REVIEWER",
    )
    return patient, encounter, encounter.findings, review


def build_synthetic_review_scenario_beta():
    """Build an alternate synthetic review scenario."""

    patient = SyntheticPatient(
        synthetic_patient_id="SYNTHETIC_PATIENT_BETA",
        display_label="DEMO_ONLY_PATIENT_BETA",
    )
    encounter = SyntheticEncounter(
        encounter_id="SYNTHETIC_ENCOUNTER_BETA",
        patient=patient,
        encounter_label="DEMO_ENCOUNTER_SYNTHETIC_BOUNDARY_CHECK",
        encounter_date=date(2099, 2, 1),
        findings=(
            SyntheticFinding(
                finding_id="SYNTHETIC_FINDING_BOUNDARY",
                title="DEMO_FINDING_BOUNDARY_VISIBILITY",
                summary="EXAMPLE_FINDING_BOUNDARY_NOTE_FOR_SANDBOX_ONLY",
            ),
        ),
    )
    review = build_clinician_review_note(
        encounter,
        reviewer_label="DEMO_CLINICIAN_REVIEWER",
    )
    return patient, encounter, encounter.findings, review


SCENARIOS = {
    "alpha": build_synthetic_review_scenario_alpha,
    "beta": build_synthetic_review_scenario_beta,
}


def build_scenario(name: str = "alpha"):
    """Build a named synthetic-only scenario for local sandbox use."""

    try:
        return SCENARIOS[name]()
    except KeyError as exc:
        available = ", ".join(sorted(SCENARIOS))
        raise ValueError(f"Unknown synthetic scenario {name!r}. Use one of: {available}.") from exc
