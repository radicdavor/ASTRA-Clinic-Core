from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.domain import Appointment, ClinicalReadinessSnapshot
from app.services.clinical_readiness_preview import build_clinical_readiness_preview


CLINICAL_READINESS_SNAPSHOT_SCHEMA_VERSION = "clinical-readiness-snapshot-v1"
CLINICAL_READINESS_SNAPSHOT_DISCLAIMER = (
    "Snapshot je zapis Clinical Readiness Preview prikaza. Ne predstavlja clinical approval, "
    "readiness clearance, Outcome Evidence ili odluku da se postupak smije provesti."
)


def _require_reason(reason: str) -> str:
    cleaned = reason.strip()
    if not cleaned:
        raise ValueError("Snapshot reason je obavezan")
    return cleaned


def _require_actor(actor_user_id: int | None) -> int:
    if actor_user_id is None:
        raise ValueError("Actor user id je obavezan za snapshot capture")
    return actor_user_id


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


def capture_clinical_readiness_snapshot(
    db: Session,
    *,
    appointment_id: int,
    actor_user_id: int | None,
    reason: str,
    idempotency_key: str | None = None,
) -> ClinicalReadinessSnapshot:
    """Capture an internal preview snapshot; B14 intentionally exposes no route/UI."""
    del idempotency_key
    snapshot_reason = _require_reason(reason)
    creator_id = _require_actor(actor_user_id)
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise LookupError("Termin nije pronaden")

    preview = build_clinical_readiness_preview(db, appointment)
    if preview.patient_id is None or preview.service_id is None:
        raise ValueError("Termin mora imati pacijenta i uslugu za snapshot capture")

    snapshot = ClinicalReadinessSnapshot(
        appointment_id=preview.appointment_id,
        patient_id=preview.patient_id,
        service_id=preview.service_id,
        created_by_user_id=creator_id,
        schema_version=CLINICAL_READINESS_SNAPSHOT_SCHEMA_VERSION,
        preview_generated_at=preview.generated_at,
        preview_status=preview.status,
        preview_summary=preview.summary,
        template_key=preview.template_key,
        template_label=preview.template_label,
        template_version=preview.template_version,
        template_binding_status=preview.template_binding_status,
        template_binding_warning=preview.template_binding_warning,
        snapshot_reason=snapshot_reason,
        is_preview_snapshot=True,
        items_json=[item.model_dump(mode="json") for item in preview.items],
        limitations_json=list(preview.limitations),
        source_warnings_json=list(preview.source_warnings),
        source_refs_json=_source_refs_from_items(preview.items),
        disclaimer=CLINICAL_READINESS_SNAPSHOT_DISCLAIMER,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
