from __future__ import annotations

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit
from app.models.domain import (
    Appointment,
    ClinicalReadinessReviewAcknowledgment,
    ClinicalReadinessSnapshot,
    User,
)
from app.services.clinical_readiness_preview import build_clinical_readiness_preview


CLINICAL_READINESS_ACKNOWLEDGED_EVENT = "clinical_readiness_acknowledged"
CLINICAL_READINESS_ACKNOWLEDGMENT_READ_DENIED_EVENT = "clinical_readiness_acknowledgment_read_denied"
CLINICAL_READINESS_ACKNOWLEDGMENT_SCHEMA_VERSION = "acknowledgment.v1"
CLINICAL_READINESS_ACKNOWLEDGMENT_LIMITATION = (
    "Acknowledgment je zapis ljudskog pregleda advisory signala; nije clinical approval, "
    "readiness clearance, override, Outcome Evidence ili dozvola za postupak."
)
CLINICAL_READINESS_ACKNOWLEDGMENT_NOT_DECISION = (
    "Acknowledgment je zapis ljudskog pregleda signala, nije klinicka odluka."
)
_FORBIDDEN_ACTOR_ROLES = {"api_key", "system", "system_job", "ai_agent"}


def _clean_required(value: str, message: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(message)
    return cleaned


def _require_actor(actor_user_id: int | None, actor_role: str) -> tuple[int, str]:
    if actor_user_id is None:
        raise ValueError("Actor user id je obavezan")
    cleaned_role = _clean_required(actor_role, "Actor role je obavezan")
    if cleaned_role.lower() in _FORBIDDEN_ACTOR_ROLES:
        raise PermissionError("Acknowledgment zahtijeva prijavljenog korisnika")
    return actor_user_id, cleaned_role


def _audit_payload(acknowledgment: ClinicalReadinessReviewAcknowledgment) -> dict:
    return {
        "acknowledgment_id": acknowledgment.id,
        "appointment_id": acknowledgment.appointment_id,
        "patient_id": acknowledgment.patient_id,
        "snapshot_id": acknowledgment.snapshot_id,
        "advisory_signal_key": acknowledgment.advisory_signal_key,
        "actor_user_id": acknowledgment.actor_user_id,
        "actor_role": acknowledgment.actor_role,
        "reason": acknowledgment.reason,
        "limitations": acknowledgment.limitations_json or [],
        "schema_version": acknowledgment.schema_version,
        "is_decision": acknowledgment.is_decision,
        "is_clearance": acknowledgment.is_clearance,
        "is_override": acknowledgment.is_override,
    }


def record_acknowledgment_read_denied_audit(
    db: Session,
    *,
    denial_category: str,
    access_type: str,
    route: str,
    actor_type: str,
    actor_user_id: int | None = None,
    actor_api_key_id: int | None = None,
    actor_role: str | None = None,
    appointment_id: int | None = None,
    patient_id: int | None = None,
    acknowledgment_id: int | None = None,
    request: Request | None = None,
) -> None:
    """Record privacy-minimized denied-read access audit without clinical payload."""
    payload = {
        "event_name": CLINICAL_READINESS_ACKNOWLEDGMENT_READ_DENIED_EVENT,
        "access_type": access_type,
        "denial_category": denial_category,
        "route": route,
        "result": "denied",
        "actor_type": actor_type,
        "actor_user_id": actor_user_id,
        "actor_api_key_id": actor_api_key_id,
        "actor_role": actor_role,
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "acknowledgment_id": acknowledgment_id,
    }
    audit(
        db,
        CLINICAL_READINESS_ACKNOWLEDGMENT_READ_DENIED_EVENT,
        "ClinicalReadinessReviewAcknowledgment",
        acknowledgment_id,
        "Acknowledgment read access denied",
        actor_user_id=actor_user_id,
        actor_type=actor_type,
        actor_api_key_id=actor_api_key_id,
        after_json=payload,
        request=request,
    )


def create_clinical_readiness_review_acknowledgment(
    db: Session,
    *,
    appointment_id: int,
    patient_id: int,
    advisory_signal_key: str,
    actor_user_id: int | None,
    actor_role: str,
    reason: str,
    snapshot_id: int | None = None,
) -> ClinicalReadinessReviewAcknowledgment:
    """Create an internal-only human review acknowledgment without workflow side effects."""
    cleaned_reason = _clean_required(reason, "Razlog pregleda signala je obavezan")
    cleaned_signal_key = _clean_required(advisory_signal_key, "Advisory signal key je obavezan")
    user_id, cleaned_actor_role = _require_actor(actor_user_id, actor_role)

    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise LookupError("Termin nije pronaden")
    if appointment.patient_id != patient_id:
        raise ValueError("Termin ne pripada navedenom pacijentu")

    actor = db.get(User, user_id)
    if not actor:
        raise LookupError("Actor user nije pronaden")

    preview = build_clinical_readiness_preview(db, appointment)
    preview_signal_keys = {item.key for item in preview.items}
    if cleaned_signal_key not in preview_signal_keys:
        raise ValueError("Advisory signal nije prepoznat u ovom kontekstu")

    if snapshot_id is not None:
        snapshot = db.get(ClinicalReadinessSnapshot, snapshot_id)
        if not snapshot:
            raise LookupError("Snapshot nije pronaden")
        if snapshot.appointment_id != appointment_id:
            raise ValueError("Snapshot ne pripada ovom terminu")
        if snapshot.patient_id != patient_id:
            raise ValueError("Snapshot ne pripada navedenom pacijentu")

    acknowledgment = ClinicalReadinessReviewAcknowledgment(
        appointment_id=appointment_id,
        patient_id=patient_id,
        snapshot_id=snapshot_id,
        advisory_signal_key=cleaned_signal_key,
        actor_user_id=user_id,
        actor_role=cleaned_actor_role,
        reason=cleaned_reason,
        limitations_json=[CLINICAL_READINESS_ACKNOWLEDGMENT_LIMITATION],
        schema_version=CLINICAL_READINESS_ACKNOWLEDGMENT_SCHEMA_VERSION,
        not_decision_disclaimer=CLINICAL_READINESS_ACKNOWLEDGMENT_NOT_DECISION,
        is_decision=False,
        is_clearance=False,
        is_override=False,
    )

    try:
        db.add(acknowledgment)
        db.flush()
        audit(
            db,
            CLINICAL_READINESS_ACKNOWLEDGED_EVENT,
            "ClinicalReadinessReviewAcknowledgment",
            acknowledgment.id,
            "Human review acknowledgment zapisan za advisory signal",
            actor_user_id=user_id,
            after_json=_audit_payload(acknowledgment),
        )
        db.commit()
        db.refresh(acknowledgment)
        return acknowledgment
    except Exception:
        db.rollback()
        raise


def list_clinical_readiness_review_acknowledgments(
    db: Session,
    *,
    appointment_id: int,
) -> list[ClinicalReadinessReviewAcknowledgment]:
    """Read acknowledgment rows for one appointment without audit or workflow side effects."""
    return list(
        db.scalars(
            select(ClinicalReadinessReviewAcknowledgment)
            .where(ClinicalReadinessReviewAcknowledgment.appointment_id == appointment_id)
            .order_by(
                ClinicalReadinessReviewAcknowledgment.created_at.desc(),
                ClinicalReadinessReviewAcknowledgment.id.desc(),
            )
        )
    )


def get_clinical_readiness_review_acknowledgment(
    db: Session,
    *,
    appointment_id: int,
    acknowledgment_id: int,
) -> ClinicalReadinessReviewAcknowledgment | None:
    """Read one appointment-scoped acknowledgment without audit or workflow side effects."""
    return db.scalar(
        select(ClinicalReadinessReviewAcknowledgment).where(
            ClinicalReadinessReviewAcknowledgment.id == acknowledgment_id,
            ClinicalReadinessReviewAcknowledgment.appointment_id == appointment_id,
        )
    )
