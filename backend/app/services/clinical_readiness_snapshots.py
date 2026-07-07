from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit
from app.models.domain import Appointment, ClinicalReadinessSnapshot
from app.services.clinical_readiness_preview import build_clinical_readiness_preview


CLINICAL_READINESS_SNAPSHOT_SCHEMA_VERSION = "clinical-readiness-snapshot-v1"
CLINICAL_READINESS_SNAPSHOT_DISCLAIMER = (
    "Snapshot je zapis Clinical Readiness Preview prikaza. Ne predstavlja clinical approval, "
    "readiness clearance, Outcome Evidence ili odluku da se postupak smije provesti."
)
CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT = "clinical_readiness_snapshot_captured"
CLINICAL_READINESS_SNAPSHOT_SUPERSEDED_EVENT = "clinical_readiness_snapshot_superseded"


class SnapshotIdempotencyConflict(ValueError):
    pass


def _require_reason(reason: str) -> str:
    cleaned = reason.strip()
    if not cleaned:
        raise ValueError("Snapshot reason je obavezan")
    return cleaned


def _require_actor(actor_user_id: int | None) -> int:
    if actor_user_id is None:
        raise ValueError("Actor user id je obavezan za snapshot capture")
    return actor_user_id


def _normalize_idempotency_key(idempotency_key: str | None) -> str | None:
    if idempotency_key is None:
        return None
    cleaned = idempotency_key.strip()
    return cleaned or None


def _idempotency_fingerprint(*, appointment_id: int, actor_user_id: int, reason: str) -> str:
    payload = {
        "appointment_id": appointment_id,
        "actor_user_id": actor_user_id,
        "reason": reason,
        "schema_version": CLINICAL_READINESS_SNAPSHOT_SCHEMA_VERSION,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_refs_from_items(items: list) -> list[dict]:
    refs: list[dict] = []
    for item in items:
        if item.source_ref or item.source_label:
            refs.append(
                {
                    "item_key": item.key,
                    "source_type": item.source_type,
                    "source_ref": item.source_ref,
                    "source_label": item.source_label,
                }
            )
    return refs


def _audit_payload(snapshot: ClinicalReadinessSnapshot) -> dict:
    items = snapshot.items_json or []
    return {
        "snapshot_id": snapshot.id,
        "appointment_id": snapshot.appointment_id,
        "patient_id": snapshot.patient_id,
        "service_id": snapshot.service_id,
        "service_name": snapshot.service.name if snapshot.service else None,
        "created_by_user_id": snapshot.created_by_user_id,
        "capture_reason": snapshot.snapshot_reason,
        "schema_version": snapshot.schema_version,
        "preview_generated_at": snapshot.preview_generated_at.isoformat(),
        "preview_status": snapshot.preview_status,
        "preview_summary": snapshot.preview_summary,
        "template_key": snapshot.template_key,
        "template_label": snapshot.template_label,
        "template_version": snapshot.template_version,
        "template_binding_status": snapshot.template_binding_status,
        "item_count": len(items),
        "blocking_item_count": sum(1 for item in items if item.get("blocking")),
        "limitation_count": len(snapshot.limitations_json or []),
        "source_warning_count": len(snapshot.source_warnings_json or []),
        "is_preview_snapshot": snapshot.is_preview_snapshot,
        "disclaimer": snapshot.disclaimer,
    }


def _supersession_audit_payload(
    *,
    old_snapshot: ClinicalReadinessSnapshot,
    new_snapshot: ClinicalReadinessSnapshot,
    actor_user_id: int,
    reason: str,
) -> dict:
    return {
        "old_snapshot_id": old_snapshot.id,
        "new_snapshot_id": new_snapshot.id,
        "appointment_id": old_snapshot.appointment_id,
        "patient_id": old_snapshot.patient_id,
        "service_id": old_snapshot.service_id,
        "service_name": old_snapshot.service.name if old_snapshot.service else None,
        "superseded_by_user_id": actor_user_id,
        "supersede_reason": reason,
        "old_template_key": old_snapshot.template_key,
        "old_template_label": old_snapshot.template_label,
        "old_template_version": old_snapshot.template_version,
        "new_template_key": new_snapshot.template_key,
        "new_template_label": new_snapshot.template_label,
        "new_template_version": new_snapshot.template_version,
        "old_preview_status": old_snapshot.preview_status,
        "old_preview_summary": old_snapshot.preview_summary,
        "new_preview_status": new_snapshot.preview_status,
        "new_preview_summary": new_snapshot.preview_summary,
        "old_created_at": old_snapshot.created_at.isoformat() if old_snapshot.created_at else None,
        "new_created_at": new_snapshot.created_at.isoformat() if new_snapshot.created_at else None,
        "is_preview_snapshot": new_snapshot.is_preview_snapshot,
    }


def _capture_clinical_readiness_snapshot_without_commit(
    db: Session,
    *,
    appointment_id: int,
    actor_user_id: int,
    reason: str,
    idempotency_key: str | None = None,
    write_capture_audit: bool = True,
) -> ClinicalReadinessSnapshot:
    """Build and persist a preview snapshot inside the caller-owned transaction."""
    normalized_idempotency_key = _normalize_idempotency_key(idempotency_key)
    idempotency_fingerprint = (
        _idempotency_fingerprint(appointment_id=appointment_id, actor_user_id=actor_user_id, reason=reason)
        if normalized_idempotency_key
        else None
    )
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise LookupError("Termin nije pronaden")

    if normalized_idempotency_key:
        existing_snapshot = db.scalar(
            select(ClinicalReadinessSnapshot).where(
                ClinicalReadinessSnapshot.appointment_id == appointment_id,
                ClinicalReadinessSnapshot.created_by_user_id == actor_user_id,
                ClinicalReadinessSnapshot.idempotency_key == normalized_idempotency_key,
            )
        )
        if existing_snapshot:
            if existing_snapshot.idempotency_fingerprint == idempotency_fingerprint:
                return existing_snapshot
            raise SnapshotIdempotencyConflict("Idempotency key je vec iskoristen za drugi snapshot capture")

    preview = build_clinical_readiness_preview(db, appointment)
    if preview.patient_id is None or preview.service_id is None:
        raise ValueError("Termin mora imati pacijenta i uslugu za snapshot capture")

    snapshot = ClinicalReadinessSnapshot(
        appointment_id=preview.appointment_id,
        patient_id=preview.patient_id,
        service_id=preview.service_id,
        created_by_user_id=actor_user_id,
        schema_version=CLINICAL_READINESS_SNAPSHOT_SCHEMA_VERSION,
        preview_generated_at=preview.generated_at,
        preview_status=preview.status,
        preview_summary=preview.summary,
        template_key=preview.template_key,
        template_label=preview.template_label,
        template_version=preview.template_version,
        template_binding_status=preview.template_binding_status,
        template_binding_warning=preview.template_binding_warning,
        snapshot_reason=reason,
        is_preview_snapshot=True,
        items_json=[item.model_dump(mode="json") for item in preview.items],
        limitations_json=list(preview.limitations),
        source_warnings_json=list(preview.source_warnings),
        source_refs_json=_source_refs_from_items(preview.items),
        disclaimer=CLINICAL_READINESS_SNAPSHOT_DISCLAIMER,
        idempotency_key=normalized_idempotency_key,
        idempotency_fingerprint=idempotency_fingerprint,
    )
    db.add(snapshot)
    db.flush()

    if write_capture_audit:
        payload = _audit_payload(snapshot)
        audit(
            db,
            CLINICAL_READINESS_SNAPSHOT_CAPTURED_EVENT,
            "ClinicalReadinessSnapshot",
            snapshot.id,
            "Spremljen Clinical Readiness Snapshot preview prikaza",
            actor_user_id=actor_user_id,
            after_json=payload,
        )
    return snapshot


def capture_clinical_readiness_snapshot(
    db: Session,
    *,
    appointment_id: int,
    actor_user_id: int | None,
    reason: str,
    idempotency_key: str | None = None,
) -> ClinicalReadinessSnapshot:
    """Capture an internal preview snapshot; B14 intentionally exposes no route/UI."""
    snapshot_reason = _require_reason(reason)
    creator_id = _require_actor(actor_user_id)

    try:
        snapshot = _capture_clinical_readiness_snapshot_without_commit(
            db,
            appointment_id=appointment_id,
            actor_user_id=creator_id,
            reason=snapshot_reason,
            idempotency_key=idempotency_key,
            write_capture_audit=True,
        )
        db.commit()
        db.refresh(snapshot)
        return snapshot
    except Exception:
        db.rollback()
        raise


def supersede_clinical_readiness_snapshot(
    db: Session,
    *,
    appointment_id: int,
    old_snapshot_id: int,
    actor_user_id: int | None,
    reason: str,
) -> ClinicalReadinessSnapshot:
    """Create a new preview snapshot and mark the old snapshot as superseded atomically."""
    cleaned_reason = _require_reason(reason)
    superseded_by_user_id = _require_actor(actor_user_id)
    old_snapshot = db.get(ClinicalReadinessSnapshot, old_snapshot_id)
    if not old_snapshot:
        raise LookupError("Snapshot nije pronaden")
    if old_snapshot.appointment_id != appointment_id:
        raise LookupError("Snapshot nije pronaden za ovaj termin")
    if old_snapshot.superseded_by_snapshot_id is not None:
        raise ValueError("Snapshot je vec oznacen kao zamijenjen")

    try:
        new_snapshot = _capture_clinical_readiness_snapshot_without_commit(
            db,
            appointment_id=appointment_id,
            actor_user_id=superseded_by_user_id,
            reason=f"Supersession: {cleaned_reason}",
            idempotency_key=None,
            write_capture_audit=False,
        )
        old_snapshot.superseded_by_snapshot_id = new_snapshot.id
        old_snapshot.superseded_at = datetime.now(UTC)
        old_snapshot.superseded_reason = cleaned_reason
        db.flush()

        payload = _supersession_audit_payload(
            old_snapshot=old_snapshot,
            new_snapshot=new_snapshot,
            actor_user_id=superseded_by_user_id,
            reason=cleaned_reason,
        )
        audit(
            db,
            CLINICAL_READINESS_SNAPSHOT_SUPERSEDED_EVENT,
            "ClinicalReadinessSnapshot",
            old_snapshot.id,
            "Clinical Readiness Snapshot zamijenjen novim preview zapisom",
            actor_user_id=superseded_by_user_id,
            after_json=payload,
        )
        db.commit()
        db.refresh(new_snapshot)
        return new_snapshot
    except Exception:
        db.rollback()
        raise
