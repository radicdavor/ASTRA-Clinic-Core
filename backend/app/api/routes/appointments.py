from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, ClinicalEpisode, ClinicalReadinessReviewAcknowledgment, ClinicalReadinessSnapshot, Patient, Service
from app.schemas.common import AppointmentCreate, AppointmentOut, AppointmentUpdate, ClinicalReadinessAcknowledgmentDetailResponse, ClinicalReadinessAcknowledgmentListResponse, ClinicalReadinessAcknowledgmentReadItem, ClinicalReadinessPreviewResponse, ClinicalReadinessSnapshotCaptureRequest, ClinicalReadinessSnapshotDetailResponse, ClinicalReadinessSnapshotHistoryItem, ClinicalReadinessSnapshotHistoryResponse, ClinicalReadinessSnapshotResponse, ClinicalReadinessSnapshotSupersedeRequest, ClinicalReadinessSnapshotSupersedeResponse, ErrorResponse
from app.services.appointments import validate_appointment_payload
from app.services.clinical_readiness_preview import build_clinical_readiness_preview
from app.services.clinical_readiness_acknowledgments import get_clinical_readiness_review_acknowledgment, list_clinical_readiness_review_acknowledgments
from app.services.clinical_readiness_snapshots import SnapshotIdempotencyConflict, capture_clinical_readiness_snapshot, supersede_clinical_readiness_snapshot

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}
SNAPSHOT_HISTORY_WARNING = "Snapshot history prikazuje spremljene preview zapise. Ne predstavlja clinical approval, readiness clearance, Outcome Evidence ili odluku da se postupak smije provesti."
SNAPSHOT_DETAIL_WARNING = "Snapshot detail prikazuje spremljeni preview payload. Ne predstavlja clinical approval, readiness clearance, Outcome Evidence ili odluku da se postupak smije provesti."
SNAPSHOT_SUPERSESSION_WARNING = "Supersession sprema novi preview snapshot i oznacava prethodni kao zamijenjen. Ne predstavlja clinical approval, readiness clearance, Outcome Evidence ili odluku da se postupak smije provesti."
ACKNOWLEDGMENT_READ_WARNING = "Acknowledgment read prikazuje da je covjek pregledao advisory signal. Ne predstavlja clinical approval, readiness clearance, override, Outcome Evidence ili dozvolu za postupak."

router = APIRouter(prefix="/api", tags=["appointments"], responses=ERROR_RESPONSES)


def patch_model(obj, data: dict) -> None:
    for key, value in data.items():
        setattr(obj, key, value)


def appointment_load_options():
    return (
        joinedload(Appointment.patient),
        joinedload(Appointment.service),
        joinedload(Appointment.provider),
        joinedload(Appointment.room),
        joinedload(Appointment.episode).joinedload(ClinicalEpisode.patient),
        joinedload(Appointment.episode).joinedload(ClinicalEpisode.owner_provider),
    )


def get_appointment_or_404(db: Session, appointment_id: int) -> Appointment:
    appointment = db.scalar(
        select(Appointment)
        .options(*appointment_load_options())
        .where(Appointment.id == appointment_id)
    )
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronaden")
    return appointment


def snapshot_response(snapshot_obj: ClinicalReadinessSnapshot) -> ClinicalReadinessSnapshotResponse:
    return ClinicalReadinessSnapshotResponse(
        id=snapshot_obj.id,
        appointment_id=snapshot_obj.appointment_id,
        patient_id=snapshot_obj.patient_id,
        service_id=snapshot_obj.service_id,
        created_at=snapshot_obj.created_at,
        created_by_user_id=snapshot_obj.created_by_user_id,
        schema_version=snapshot_obj.schema_version,
        preview_generated_at=snapshot_obj.preview_generated_at,
        preview_status=snapshot_obj.preview_status,
        template_key=snapshot_obj.template_key,
        template_label=snapshot_obj.template_label,
        template_version=snapshot_obj.template_version,
        template_binding_status=snapshot_obj.template_binding_status,
        snapshot_reason=snapshot_obj.snapshot_reason,
        is_preview_snapshot=snapshot_obj.is_preview_snapshot,
        disclaimer=snapshot_obj.disclaimer,
        items=snapshot_obj.items_json or [],
        limitations=snapshot_obj.limitations_json or [],
        source_warnings=snapshot_obj.source_warnings_json or [],
        source_refs=snapshot_obj.source_refs_json or [],
    )


def snapshot_history_item(snapshot_obj: ClinicalReadinessSnapshot) -> ClinicalReadinessSnapshotHistoryItem:
    return ClinicalReadinessSnapshotHistoryItem(
        id=snapshot_obj.id,
        appointment_id=snapshot_obj.appointment_id,
        patient_id=snapshot_obj.patient_id,
        service_id=snapshot_obj.service_id,
        created_at=snapshot_obj.created_at,
        created_by_user_id=snapshot_obj.created_by_user_id,
        schema_version=snapshot_obj.schema_version,
        preview_generated_at=snapshot_obj.preview_generated_at,
        preview_status=snapshot_obj.preview_status,
        template_key=snapshot_obj.template_key,
        template_label=snapshot_obj.template_label,
        template_version=snapshot_obj.template_version,
        template_binding_status=snapshot_obj.template_binding_status,
        snapshot_reason=snapshot_obj.snapshot_reason,
        is_preview_snapshot=snapshot_obj.is_preview_snapshot,
        disclaimer=snapshot_obj.disclaimer,
        item_count=len(snapshot_obj.items_json or []),
        limitation_count=len(snapshot_obj.limitations_json or []),
        source_warning_count=len(snapshot_obj.source_warnings_json or []),
        superseded_by_snapshot_id=snapshot_obj.superseded_by_snapshot_id,
        superseded_at=snapshot_obj.superseded_at,
        superseded_reason=snapshot_obj.superseded_reason,
    )


def snapshot_detail_response(snapshot_obj: ClinicalReadinessSnapshot) -> ClinicalReadinessSnapshotDetailResponse:
    return ClinicalReadinessSnapshotDetailResponse(
        id=snapshot_obj.id,
        appointment_id=snapshot_obj.appointment_id,
        patient_id=snapshot_obj.patient_id,
        service_id=snapshot_obj.service_id,
        created_at=snapshot_obj.created_at,
        created_by_user_id=snapshot_obj.created_by_user_id,
        schema_version=snapshot_obj.schema_version,
        preview_generated_at=snapshot_obj.preview_generated_at,
        preview_status=snapshot_obj.preview_status,
        preview_summary=snapshot_obj.preview_summary,
        template_key=snapshot_obj.template_key,
        template_label=snapshot_obj.template_label,
        template_version=snapshot_obj.template_version,
        template_binding_status=snapshot_obj.template_binding_status,
        template_binding_warning=snapshot_obj.template_binding_warning,
        snapshot_reason=snapshot_obj.snapshot_reason,
        is_preview_snapshot=snapshot_obj.is_preview_snapshot,
        disclaimer=snapshot_obj.disclaimer,
        items=snapshot_obj.items_json or [],
        limitations=snapshot_obj.limitations_json or [],
        source_warnings=snapshot_obj.source_warnings_json or [],
        source_refs=snapshot_obj.source_refs_json or [],
        superseded_by_snapshot_id=snapshot_obj.superseded_by_snapshot_id,
        superseded_at=snapshot_obj.superseded_at,
        superseded_reason=snapshot_obj.superseded_reason,
        warning=SNAPSHOT_DETAIL_WARNING,
    )


def acknowledgment_key(acknowledgment: ClinicalReadinessReviewAcknowledgment) -> str:
    return f"ack-{acknowledgment.id}"


def acknowledgment_read_item(acknowledgment: ClinicalReadinessReviewAcknowledgment) -> ClinicalReadinessAcknowledgmentReadItem:
    return ClinicalReadinessAcknowledgmentReadItem(
        id=acknowledgment.id,
        acknowledgment_key=acknowledgment_key(acknowledgment),
        appointment_id=acknowledgment.appointment_id,
        patient_id=acknowledgment.patient_id,
        advisory_signal_key=acknowledgment.advisory_signal_key,
        snapshot_id=acknowledgment.snapshot_id,
        actor_user_id=acknowledgment.actor_user_id,
        actor_role=acknowledgment.actor_role,
        reason=acknowledgment.reason,
        limitations=acknowledgment.limitations_json or [],
        schema_version=acknowledgment.schema_version,
        created_at=acknowledgment.created_at,
        safe_disclaimer=acknowledgment.not_decision_disclaimer,
        is_decision=acknowledgment.is_decision,
        is_clearance=acknowledgment.is_clearance,
        is_override=acknowledgment.is_override,
    )


def validate_episode_for_patient(db: Session, episode_id: int | None, patient_id: int) -> ClinicalEpisode | None:
    if episode_id is None:
        return None
    episode = db.get(ClinicalEpisode, episode_id)
    if not episode:
        raise HTTPException(404, detail="Klinicka epizoda nije pronadena")
    if episode.patient_id != patient_id:
        raise HTTPException(422, detail="Klinicka epizoda mora pripadati istom pacijentu kao termin")
    return episode


@router.post("/appointments", response_model=AppointmentOut)
def create_appointment(
    payload: AppointmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    data = payload.model_dump()
    validate_episode_for_patient(db, data.get("episode_id"), payload.patient_id)
    data["duration_minutes"] = validate_appointment_payload(
        db,
        payload.date,
        payload.start_time,
        payload.end_time,
        payload.provider_id,
        payload.room_id,
        payload.status,
        payload.source,
        service_id=payload.service_id,
    )
    appointment = Appointment(**data, created_by=actor.user_id)
    db.add(appointment)
    db.flush()
    audit(db, "create", "Appointment", appointment.id, f"Termin {appointment.date}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(appointment), request)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(
    date_from: date | None = None,
    date_to: date | None = None,
    patient: str | None = None,
    service: str | None = None,
    provider_id: int | None = None,
    room_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.read")),
):
    stmt = select(Appointment).options(*appointment_load_options()).order_by(Appointment.date, Appointment.start_time)
    if date_from:
        stmt = stmt.where(Appointment.date >= date_from)
    if date_to:
        stmt = stmt.where(Appointment.date <= date_to)
    if provider_id:
        stmt = stmt.where(Appointment.provider_id == provider_id)
    if room_id:
        stmt = stmt.where(Appointment.room_id == room_id)
    if status:
        stmt = stmt.where(Appointment.status == status)
    if patient:
        stmt = stmt.join(Appointment.patient).where(or_(Patient.first_name.ilike(f"%{patient}%"), Patient.last_name.ilike(f"%{patient}%")))
    if service:
        stmt = stmt.join(Appointment.service).where(Service.name.ilike(f"%{service}%"))
    return db.scalars(stmt).all()


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.read")),
):
    return get_appointment_or_404(db, appointment_id)


@router.get("/appointments/{appointment_id}/clinical-readiness-preview", response_model=ClinicalReadinessPreviewResponse)
def get_appointment_clinical_readiness_preview(
    appointment_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.read")),
):
    """Demo/pilot read-only preview; not enforcement, production decision, medical-device decision or AI clearance."""
    appointment = get_appointment_or_404(db, appointment_id)
    return build_clinical_readiness_preview(db, appointment)


@router.post("/appointments/{appointment_id}/clinical-readiness-snapshots", response_model=ClinicalReadinessSnapshotResponse)
def capture_appointment_clinical_readiness_snapshot(
    appointment_id: int,
    payload: ClinicalReadinessSnapshotCaptureRequest,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_readiness.snapshots.write")),
):
    """Explicit preview snapshot capture; not clinical approval, override, task or outcome evidence."""
    if actor.actor_type != "user" or actor.user_id is None:
        raise HTTPException(403, detail="Snapshot capture zahtijeva prijavljenog korisnika")
    try:
        snapshot_obj = capture_clinical_readiness_snapshot(
            db,
            appointment_id=appointment_id,
            actor_user_id=actor.user_id,
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
        )
    except LookupError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except SnapshotIdempotencyConflict as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    return snapshot_response(snapshot_obj)


@router.get("/appointments/{appointment_id}/clinical-readiness-snapshots", response_model=ClinicalReadinessSnapshotHistoryResponse)
def appointment_clinical_readiness_snapshot_history(
    appointment_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_readiness.snapshots.read")),
):
    """Read-only preview snapshot history; not clinical approval, override, task or outcome evidence."""
    get_appointment_or_404(db, appointment_id)
    snapshots = db.scalars(
        select(ClinicalReadinessSnapshot)
        .where(ClinicalReadinessSnapshot.appointment_id == appointment_id)
        .order_by(ClinicalReadinessSnapshot.created_at.desc(), ClinicalReadinessSnapshot.id.desc())
    ).all()
    items = [snapshot_history_item(snapshot_obj) for snapshot_obj in snapshots]
    return ClinicalReadinessSnapshotHistoryResponse(
        appointment_id=appointment_id,
        snapshots=items,
        count=len(items),
        is_preview_history=True,
        warning=SNAPSHOT_HISTORY_WARNING,
    )


@router.get("/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}", response_model=ClinicalReadinessSnapshotDetailResponse)
def appointment_clinical_readiness_snapshot_detail(
    appointment_id: int,
    snapshot_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_readiness.snapshots.read")),
):
    """Read-only copied preview snapshot payload; not clinical approval, override, task or outcome evidence."""
    get_appointment_or_404(db, appointment_id)
    snapshot_obj = db.scalar(
        select(ClinicalReadinessSnapshot)
        .where(
            ClinicalReadinessSnapshot.id == snapshot_id,
            ClinicalReadinessSnapshot.appointment_id == appointment_id,
        )
    )
    if not snapshot_obj:
        raise HTTPException(404, detail="Snapshot nije pronaden")
    return snapshot_detail_response(snapshot_obj)


@router.get("/appointments/{appointment_id}/clinical-readiness/acknowledgments", response_model=ClinicalReadinessAcknowledgmentListResponse)
def appointment_clinical_readiness_acknowledgments(
    appointment_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_readiness.acknowledgments.read")),
):
    """Read-only human review acknowledgment list; not clinical approval, override, task or outcome evidence."""
    if actor.actor_type != "user" or actor.user_id is None:
        raise HTTPException(403, detail="Acknowledgment read zahtijeva prijavljenog korisnika")
    get_appointment_or_404(db, appointment_id)
    acknowledgments = list_clinical_readiness_review_acknowledgments(db, appointment_id=appointment_id)
    items = [acknowledgment_read_item(acknowledgment) for acknowledgment in acknowledgments]
    return ClinicalReadinessAcknowledgmentListResponse(
        appointment_id=appointment_id,
        acknowledgments=items,
        count=len(items),
        is_read_only=True,
        warning=ACKNOWLEDGMENT_READ_WARNING,
    )


@router.get("/appointments/{appointment_id}/clinical-readiness/acknowledgments/{acknowledgment_id}", response_model=ClinicalReadinessAcknowledgmentDetailResponse)
def appointment_clinical_readiness_acknowledgment_detail(
    appointment_id: int,
    acknowledgment_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_readiness.acknowledgments.read")),
):
    """Read-only human review acknowledgment detail; not clinical approval, override, task or outcome evidence."""
    if actor.actor_type != "user" or actor.user_id is None:
        raise HTTPException(403, detail="Acknowledgment read zahtijeva prijavljenog korisnika")
    get_appointment_or_404(db, appointment_id)
    acknowledgment = get_clinical_readiness_review_acknowledgment(
        db,
        appointment_id=appointment_id,
        acknowledgment_id=acknowledgment_id,
    )
    if acknowledgment is None:
        raise HTTPException(404, detail="Acknowledgment nije pronaden")
    return ClinicalReadinessAcknowledgmentDetailResponse(
        **acknowledgment_read_item(acknowledgment).model_dump(),
        warning=ACKNOWLEDGMENT_READ_WARNING,
    )


@router.post("/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}/supersede", response_model=ClinicalReadinessSnapshotSupersedeResponse)
def supersede_appointment_clinical_readiness_snapshot(
    appointment_id: int,
    snapshot_id: int,
    payload: ClinicalReadinessSnapshotSupersedeRequest,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_readiness.snapshots.supersede")),
):
    """Supersede an immutable preview snapshot; not clinical approval, override, task or outcome evidence."""
    if actor.actor_type != "user" or actor.user_id is None:
        raise HTTPException(403, detail="Snapshot supersession zahtijeva prijavljenog korisnika")
    try:
        new_snapshot = supersede_clinical_readiness_snapshot(
            db,
            appointment_id=appointment_id,
            old_snapshot_id=snapshot_id,
            actor_user_id=actor.user_id,
            reason=payload.reason,
        )
    except LookupError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except ValueError as exc:
        message = str(exc)
        status_code = 409 if "vec" in message.lower() else 422
        raise HTTPException(status_code, detail=message) from exc

    old_snapshot = db.get(ClinicalReadinessSnapshot, snapshot_id)
    if old_snapshot is None or old_snapshot.superseded_at is None or old_snapshot.superseded_reason is None:
        raise HTTPException(500, detail="Supersession metadata nije dostupna")
    return ClinicalReadinessSnapshotSupersedeResponse(
        old_snapshot_id=snapshot_id,
        new_snapshot=snapshot_response(new_snapshot),
        superseded_at=old_snapshot.superseded_at,
        superseded_reason=old_snapshot.superseded_reason,
        warning=SNAPSHOT_SUPERSESSION_WARNING,
    )


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronaden")
    before = snapshot(appointment)
    update_data = payload.model_dump(exclude_unset=True)
    next_patient_id = update_data.get("patient_id", appointment.patient_id)
    if "episode_id" in update_data:
        validate_episode_for_patient(db, update_data.get("episode_id"), next_patient_id)
    old_episode_id = appointment.episode_id
    patch_model(appointment, update_data)
    appointment.duration_minutes = validate_appointment_payload(
        db,
        appointment.date,
        appointment.start_time,
        appointment.end_time,
        appointment.provider_id,
        appointment.room_id,
        appointment.status,
        appointment.source,
        service_id=appointment.service_id,
        appointment_id=appointment.id,
    )
    db.flush()
    audit(db, "update", "Appointment", appointment.id, "Azuriran termin", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(appointment), request)
    if "episode_id" in update_data and old_episode_id != appointment.episode_id:
        action = "link_episode" if appointment.episode_id else "unlink_episode"
        summary = f"Termin povezan s epizodom #{appointment.episode_id}" if appointment.episode_id else "Termin odvojen od klinicke epizode"
        audit(db, action, "Appointment", appointment.id, summary, actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(appointment), request)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.delete("/appointments/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronaden")
    before = snapshot(appointment)
    db.delete(appointment)
    audit(db, "delete", "Appointment", appointment_id, "Obrisan termin", actor.user_id, actor.actor_type, actor.api_key_id, before, None, request)
    db.commit()
    return {"ok": True}


@router.get("/schedule/day", response_model=list[AppointmentOut])
def day_schedule(
    date: date = Query(...),
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.read")),
):
    return db.scalars(
        select(Appointment)
        .options(*appointment_load_options())
        .where(Appointment.date == date)
        .order_by(Appointment.start_time)
    ).all()
