"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

import re

from .display import render_safety_banner
from .models import SAFETY_BANNER


_IDENTIFIER_LIKE_PATTERNS = (
    re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),
    re.compile(r"\d{10,12}"),
    re.compile(r"\b[A-Z]{2,5}[- ]?\d{4,}\b"),
    re.compile(r"@"),
)

FEEDBACK_INPUT_WARNING = (
    "Do not enter real patient data, PHI, PII, clinical instructions, "
    "or patient-identifying information. This local check is not complete "
    "PHI detection."
)


def looks_identifier_like(text: str) -> bool:
    """Return whether local feedback has an obvious identifier-like pattern."""

    return any(pattern.search(text) for pattern in _IDENTIFIER_LIKE_PATTERNS)


def build_feedback_input_preview(text: str | None = None) -> dict[str, object]:
    """Build a local synthetic feedback preview without persistence or transmission."""

    entered_feedback = (text or "").strip()
    empty_feedback = entered_feedback == ""
    identifier_warning = bool(entered_feedback and looks_identifier_like(entered_feedback))
    return {
        "safety_banner": SAFETY_BANNER,
        "feedback_type": "Local synthetic design feedback",
        "entered_feedback": entered_feedback,
        "empty_feedback": empty_feedback,
        "warning": FEEDBACK_INPUT_WARNING,
        "identifier_warning": identifier_warning,
        "interpretation": (
            "This feedback is displayed only as a local sandbox preview. "
            "It is not stored, not transmitted, not sent to a patient, "
            "not converted into a clinical task, and not used for patient care."
        ),
        "synthetic_only": True,
        "non_production": True,
        "clinical_use_authorized": False,
        "real_patient_data_allowed": False,
        "phi_pii_allowed": False,
        "persisted": False,
        "sent_externally": False,
        "clinical_task_created": False,
        "patient_message_created": False,
        "appointment_mutation_performed": False,
        "workflow_enforced": False,
        "clinical_writeback_performed": False,
        "approval_override_created": False,
        "go_live_authorized": False,
    }


def render_feedback_input_preview(preview: dict[str, object]) -> str:
    """Render a local-only feedback input preview."""

    lines = [
        "Program 1 Synthetic Sandbox Feedback Preview",
        render_safety_banner().split("\n", 1)[1],
        "",
        "Feedback type:",
        str(preview["feedback_type"]),
        "",
        "Safety warning:",
        str(preview["warning"]),
        "",
        "Entered feedback:",
    ]
    if preview["empty_feedback"]:
        lines.append("No feedback text was entered. No data was stored or transmitted.")
    else:
        lines.append(f'"{preview["entered_feedback"]}"')
    if preview["identifier_warning"]:
        lines.extend(
            [
                "",
                "Local warning:",
                (
                    "The feedback text contains an obvious identifier-like pattern. "
                    "Do not use real patient data, PHI, PII, clinical instructions, "
                    "or patient-identifying information in this sandbox."
                ),
            ]
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            str(preview["interpretation"]),
            "",
            "Safety confirmations:",
            f"- Persisted: {'yes' if preview['persisted'] else 'no'}",
            f"- Sent externally: {'yes' if preview['sent_externally'] else 'no'}",
            f"- Clinical task created: {'yes' if preview['clinical_task_created'] else 'no'}",
            f"- Patient message created: {'yes' if preview['patient_message_created'] else 'no'}",
            (
                "- Appointment changed: "
                f"{'yes' if preview['appointment_mutation_performed'] else 'no'}"
            ),
            f"- Workflow enforced: {'yes' if preview['workflow_enforced'] else 'no'}",
            (
                "- Clinical writeback performed: "
                f"{'yes' if preview['clinical_writeback_performed'] else 'no'}"
            ),
            (
                "- Approval/override created: "
                f"{'yes' if preview['approval_override_created'] else 'no'}"
            ),
            f"- Go-live authorized: {'yes' if preview['go_live_authorized'] else 'no'}",
        ]
    )
    return "\n".join(lines)
