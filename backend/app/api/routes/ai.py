from datetime import date, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.domain import Appointment, User
from app.schemas.common import AppointmentCreate, PatientCreate
from app.api.routes.core import create_appointment, create_patient

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/patients/create")
def ai_create_patient(payload: PatientCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_patient(payload, db, user)


@router.post("/appointments/create")
def ai_create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload.source = "ai_agent"
    return create_appointment(payload, db, user)


@router.get("/today")
def ai_today(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    appointments = db.scalars(select(Appointment).options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room)).where(Appointment.date == today).order_by(Appointment.start_time)).all()
    return {"date": today, "appointments": appointments}


@router.get("/free-slots")
def free_slots(day: date, provider_id: int, room_id: int | None = None, duration_minutes: int = 30, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    booked = db.scalars(select(Appointment).where(Appointment.date == day, Appointment.provider_id == provider_id)).all()
    cursor = time(8, 0)
    end = time(18, 0)
    slots = []
    while cursor < end:
        slot_start = cursor
        minutes = cursor.hour * 60 + cursor.minute + duration_minutes
        slot_end = time(minutes // 60, minutes % 60)
        overlaps = any(a.start_time < slot_end and a.end_time > slot_start and (room_id is None or a.room_id == room_id) for a in booked)
        if not overlaps and slot_end <= end:
            slots.append({"date": day, "start_time": slot_start, "end_time": slot_end, "provider_id": provider_id, "room_id": room_id})
        cursor = (timedelta(hours=cursor.hour, minutes=cursor.minute) + timedelta(minutes=15))
        total_seconds = cursor.seconds
        cursor = time(total_seconds // 3600, (total_seconds % 3600) // 60)
    return slots
