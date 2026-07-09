"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from .scenarios import build_synthetic_review_scenario_alpha


def build_sample_patient():
    """Create the local sandbox synthetic patient placeholder."""

    patient, _encounter, _findings, _review = build_synthetic_review_scenario_alpha()
    return patient


def build_sample_encounter():
    """Create the local sandbox synthetic encounter placeholder."""

    _patient, encounter, _findings, _review = build_synthetic_review_scenario_alpha()
    return encounter


def build_sample_workflow():
    """Create the local sandbox patient, encounter, findings, and review."""

    return build_synthetic_review_scenario_alpha()
