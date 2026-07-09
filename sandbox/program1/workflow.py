"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from .models import SAFETY_BANNER, SyntheticClinicianReview, SyntheticEncounter


def build_clinician_review_note(
    encounter: SyntheticEncounter,
    *,
    reviewer_label: str,
) -> SyntheticClinicianReview:
    """Build a synthetic review placeholder without diagnosis or treatment."""

    note = (
        "DEMO_REVIEW_NOTE_SYNTHETIC_ONLY_NOT_CLINICAL_ADVICE_"
        f"{len(encounter.findings)}_FINDINGS_ATTACHED"
    )
    return SyntheticClinicianReview(
        review_id="SYNTHETIC_REVIEW_ALPHA",
        encounter=encounter,
        reviewer_label=reviewer_label,
        note=note,
    )


def build_workflow_summary(review: SyntheticClinicianReview) -> dict[str, object]:
    """Return a local-only workflow summary for sandbox display or tests."""

    encounter = review.encounter
    return {
        "safety_banner": SAFETY_BANNER,
        "patient": encounter.patient.display_label,
        "encounter": encounter.encounter_label,
        "findings": [finding.title for finding in encounter.findings],
        "review_note": review.note,
        "sandbox_only": True,
        "clinical_use_authorized": False,
        "real_patient_data_allowed": False,
        "phi_pii_allowed": False,
        "external_integrations_enabled": False,
        "appointment_mutation_enabled": False,
        "patient_messaging_enabled": False,
        "approval_override_enabled": False,
    }
