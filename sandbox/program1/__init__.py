"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from .sample_data import build_sample_workflow
from .workflow import build_clinician_review_note, build_workflow_summary

__all__ = [
    "build_clinician_review_note",
    "build_sample_workflow",
    "build_workflow_summary",
]
