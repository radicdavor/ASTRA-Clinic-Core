from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, ClinicalEpisode, Provider, Room
from app.schemas.common import AppointmentOut, ErrorResponse, ReceptionArrivalRequest, ReceptionSlot

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

router = APIRouter(prefix="/api", tags=["reception"], responses=ERROR_RESPONSES)


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


def ten_minute_reception_slots(appointments: list[Appointment]) -> list[ReceptionSlot]:
    by_start = {appointment.start_time.strftime("%H:%M"): appointment for appointment in appointments}
    slots: list[ReceptionSlot] = []
    current = datetime.combine(date.today(), time(7, 0))
    end = datetime.combine(date.today(), time(21, 0))
    occupied_until: datetime | None = None
    while current <= end:
        label = current.strftime("%H:%M")
        appointment = by_start.get(label)
        if appointment:
            span = max(
                1,
                int(
                    (
                        datetime.combine(date.today(), appointment.end_time)
                        - datetime.combine(date.today(), appointment.start_time)
                    ).total_seconds()
                    // 600
                ),
            )
            occupied_until = datetime.combine(date.today(), appointment.end_time)
            slots.append(ReceptionSlot(time=label, appointment=appointment, span=span, empty=False))
        elif occupied_until and current < occupied_until:
            slots.append(ReceptionSlot(time=label, appointment=None, span=0, empty=False))
        else:
            slots.append(ReceptionSlot(time=label, appointment=None, span=1, empty=True))
        current += timedelta(minutes=10)
    return slots


@router.get("/reception/day", response_model=list[ReceptionSlot])
def reception_day(
    date: date = Query(...),
    clinic_id: int | None = None,
    room_id: int | None = None,
    provider_id: int | None = None,
    service_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.read")),
):
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.service),
            joinedload(Appointment.provider).joinedload(Provider.clinic),
            joinedload(Appointment.room).joinedload(Room.clinic),
        )
        .join(Appointment.room)
        .where(Appointment.date == date)
        .order_by(Appointment.start_time)
    )
    if clinic_id:
        stmt = stmt.where(Room.clinic_id == clinic_id)
    if room_id:
        stmt = stmt.where(Appointment.room_id == room_id)
    if provider_id:
        stmt = stmt.where(Appointment.provider_id == provider_id)
    if service_id:
        stmt = stmt.where(Appointment.service_id == service_id)
    if status:
        stmt = stmt.where(Appointment.status == status)
    return ten_minute_reception_slots(db.scalars(stmt).all())


@router.post("/appointments/{appointment_id}/mark-arrived", response_model=AppointmentOut)
def mark_appointment_arrived(
    appointment_id: int,
    payload: ReceptionArrivalRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    appointment = db.scalar(
        select(Appointment)
        .options(joinedload(Appointment.patient))
        .where(Appointment.id == appointment_id)
    )
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronaden")
    before = snapshot(appointment)
    if payload.patient:
        patient_before = snapshot(appointment.patient)
        patch_model(appointment.patient, payload.patient.model_dump(exclude_unset=True))
        audit(db, "reception_patient_updated", "Patient", appointment.patient_id, "Recepcija je dopunila podatke pacijenta", actor.user_id, actor.actor_type, actor.api_key_id, patient_before, snapshot(appointment.patient), request)
    now = datetime.now(timezone.utc)
    appointment.status = "arrived"
    appointment.arrived_at = now
    if payload.identity_verified:
        appointment.identity_verified_at = now
        appointment.identity_verified_by = actor.user_id
        audit(db, "identity_verified", "Appointment", appointment.id, "Identitet pacijenta je provjeren na prijemu", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(appointment), request)
    db.flush()
    audit(db, "mark_arrived", "Appointment", appointment.id, "Pacijent je oznacen kao pristigao", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(appointment), request)
    db.commit()
    db.refresh(appointment)
    return db.scalar(
        select(Appointment)
        .options(*appointment_load_options())
        .where(Appointment.id == appointment.id)
    )
