from datetime import date, time, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, Patient
from app.schemas.common import AppointmentCreate, AppointmentOut, ErrorResponse, PatientCreate, PatientOut
from app.services.appointments import BLOCKING_STATUSES, create_appointment_with_journey

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api/ai", tags=["ai"], responses=ERROR_RESPONSES)


@router.post("/patients/create", response_model=PatientOut)
def ai_create_patient(payload: PatientCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("ai.patients.create"))):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.flush()
    audit(db, "create", "Patient", patient.id, "AI kreirao pacijenta", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(patient), request)
    db.commit()
    db.refresh(patient)
    return patient


@router.post("/appointments/create", response_model=AppointmentOut)
def ai_create_appointment(payload: AppointmentCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("ai.appointments.create"))):
    data = payload.model_dump()
    data["source"] = "ai_agent"
    appointment = create_appointment_with_journey(db,data,actor,request)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/today")
def ai_today(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("ai.free_slots.read"))):
    today = date.today()
    appointments = db.scalars(select(Appointment).options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room)).where(Appointment.date == today).order_by(Appointment.start_time)).all()
    return {"date": today, "appointments": appointments}


@router.get("/free-slots")
def free_slots(
    day: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    provider_id: int | None = None,
    room_id: int | None = None,
    service_id: int | None = None,
    duration_minutes: int = 30,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("ai.free_slots.read")),
):
    start_day = date_from or day or date.today()
    end_day = date_to or start_day
    if service_id:
        from app.models.domain import Service

        service = db.get(Service, service_id)
        if service:
            duration_minutes = service.duration_minutes

    slots = []
    current_day = start_day
    while current_day <= end_day:
        query = select(Appointment).where(Appointment.date == current_day, Appointment.status.in_(BLOCKING_STATUSES))
        if provider_id:
            query = query.where(Appointment.provider_id == provider_id)
        if room_id:
            query = query.where(Appointment.room_id == room_id)
        booked = db.scalars(query).all()
        cursor = time(8, 0)
        end = time(18, 0)
        while cursor < end:
            slot_start = cursor
            minutes = cursor.hour * 60 + cursor.minute + duration_minutes
            slot_end = time(minutes // 60, minutes % 60)
            overlaps = any(a.start_time < slot_end and a.end_time > slot_start for a in booked)
            if not overlaps and slot_end <= end:
                slots.append({"date": current_day, "start_time": slot_start, "end_time": slot_end, "provider_id": provider_id, "room_id": room_id})
            cursor_delta = timedelta(hours=cursor.hour, minutes=cursor.minute) + timedelta(minutes=15)
            cursor = time(cursor_delta.seconds // 3600, (cursor_delta.seconds % 3600) // 60)
        current_day += timedelta(days=1)
    return slots
