"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import re


SAFETY_BANNER = (
    "Synthetic-only. Non-production. No real patient data. "
    "No PHI/PII. Not for clinical use."
)

_DISALLOWED_PATTERNS = [
    re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),  # US SSN-like
    re.compile(r"\d{10,12}"),  # phone, OIB, MRN-like long identifiers
    re.compile(r"\b[A-Z]{2,5}[- ]?\d{4,}\b"),  # MRN-like tokens
    re.compile(r"@"),
]


class SyntheticDataError(ValueError):
    """Raised when sandbox data does not satisfy synthetic-only boundaries."""


def require_synthetic_text(value: str, field_name: str) -> str:
    """Validate a string used by the local synthetic sandbox."""

    if not value or not value.strip():
        raise SyntheticDataError(f"{field_name} must be populated with synthetic text.")
    normalized = value.strip()
    if not (
        normalized.startswith("SYNTHETIC_")
        or normalized.startswith("DEMO_")
        or normalized.startswith("EXAMPLE_")
    ):
        raise SyntheticDataError(
            f"{field_name} must start with SYNTHETIC_, DEMO_, or EXAMPLE_."
        )
    for pattern in _DISALLOWED_PATTERNS:
        if pattern.search(normalized):
            raise SyntheticDataError(
                f"{field_name} contains a real-identifier-like pattern."
            )
    return normalized


@dataclass(frozen=True)
class SyntheticPatient:
    """Synthetic-only patient placeholder for local sandbox workflow practice."""

    synthetic_patient_id: str
    display_label: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "synthetic_patient_id",
            require_synthetic_text(self.synthetic_patient_id, "synthetic_patient_id"),
        )
        object.__setattr__(
            self,
            "display_label",
            require_synthetic_text(self.display_label, "display_label"),
        )


@dataclass(frozen=True)
class SyntheticFinding:
    """Synthetic-only finding placeholder; not diagnosis or treatment."""

    finding_id: str
    title: str
    summary: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "finding_id", require_synthetic_text(self.finding_id, "finding_id")
        )
        object.__setattr__(self, "title", require_synthetic_text(self.title, "title"))
        object.__setattr__(
            self, "summary", require_synthetic_text(self.summary, "summary")
        )


@dataclass(frozen=True)
class SyntheticEncounter:
    """Synthetic-only encounter placeholder; no appointment mutation is possible."""

    encounter_id: str
    patient: SyntheticPatient
    encounter_label: str
    encounter_date: date
    findings: tuple[SyntheticFinding, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "encounter_id",
            require_synthetic_text(self.encounter_id, "encounter_id"),
        )
        object.__setattr__(
            self,
            "encounter_label",
            require_synthetic_text(self.encounter_label, "encounter_label"),
        )
        if not isinstance(self.patient, SyntheticPatient):
            raise SyntheticDataError("patient must be a SyntheticPatient.")
        if not isinstance(self.findings, tuple):
            object.__setattr__(self, "findings", tuple(self.findings))


@dataclass(frozen=True)
class SyntheticClinicianReview:
    """Synthetic-only clinician review placeholder; not clinical advice."""

    review_id: str
    encounter: SyntheticEncounter
    reviewer_label: str
    note: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "review_id", require_synthetic_text(self.review_id, "review_id")
        )
        object.__setattr__(
            self,
            "reviewer_label",
            require_synthetic_text(self.reviewer_label, "reviewer_label"),
        )
        object.__setattr__(self, "note", require_synthetic_text(self.note, "note"))
        if not isinstance(self.encounter, SyntheticEncounter):
            raise SyntheticDataError("encounter must be a SyntheticEncounter.")
