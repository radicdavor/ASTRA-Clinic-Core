"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from datetime import date

from .models import SyntheticEncounter, SyntheticFinding, SyntheticPatient
from .workflow import build_clinician_review_note


def build_sample_patient() -> SyntheticPatient:
    """Create the local sandbox synthetic patient placeholder."""

    return SyntheticPatient(
        synthetic_patient_id="SYNTHETIC_PATIENT_ALPHA",
        display_label="DEMO_ONLY_PATIENT_ALPHA",
    )


def build_sample_encounter() -> SyntheticEncounter:
    """Create the local sandbox synthetic encounter placeholder."""

    patient = build_sample_patient()
    findings = (
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
    )
    return SyntheticEncounter(
        encounter_id="SYNTHETIC_ENCOUNTER_ALPHA",
        patient=patient,
        encounter_label="DEMO_ENCOUNTER_SYNTHETIC_REVIEW",
        encounter_date=date(2099, 1, 1),
        findings=findings,
    )


def build_sample_workflow():
    """Create the local sandbox patient, encounter, findings, and review."""

    encounter = build_sample_encounter()
    review = build_clinician_review_note(
        encounter,
        reviewer_label="DEMO_CLINICIAN_REVIEWER",
    )
    return encounter.patient, encounter, encounter.findings, review
