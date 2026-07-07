from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, ClinicalEpisode, Patient, Service
from app.schemas.common import AppointmentCreate, AppointmentOut, AppointmentUpdate, ErrorResponse
from app.services.appointments import validate_appointment_payload

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

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
