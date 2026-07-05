from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.domain import Appointment, AppointmentSource, AppointmentStatus

BLOCKING_STATUSES = {
    AppointmentStatus.scheduled.value,
    AppointmentStatus.confirmed.value,
    AppointmentStatus.arrived.value,
    AppointmentStatus.in_progress.value,
    AppointmentStatus.waiting_for_result.value,
    AppointmentStatus.follow_up_needed.value,
    AppointmentStatus.rescheduled.value,
}


def calculate_duration_minutes(appointment_date, start_time, end_time) -> int:
    start = datetime.combine(appointment_date, start_time)
    end = datetime.combine(appointment_date, end_time)
    minutes = int((end - start).total_seconds() // 60)
    if minutes <= 0:
        raise HTTPException(status_code=422, detail="Vrijeme završetka mora biti nakon vremena početka")
    return minutes


def validate_status_and_source(status_value: str, source_value: str) -> None:
    if status_value not in {status.value for status in AppointmentStatus}:
        raise HTTPException(status_code=422, detail="Neispravan status termina")
    if source_value not in {source.value for source in AppointmentSource}:
        raise HTTPException(status_code=422, detail="Neispravan izvor termina")


def validate_appointment_payload(
    db: Session,
    appointment_date,
    start_time,
    end_time,
    provider_id: int,
    room_id: int,
    status_value: str,
    source_value: str,
    appointment_id: int | None = None,
    allow_override: bool = False,
) -> int:
    validate_status_and_source(status_value, source_value)
    duration_minutes = calculate_duration_minutes(appointment_date, start_time, end_time)
    if status_value not in BLOCKING_STATUSES:
        return duration_minutes

    base = [
        Appointment.date == appointment_date,
        Appointment.status.in_(BLOCKING_STATUSES),
        Appointment.start_time < end_time,
        Appointment.end_time > start_time,
    ]
    if appointment_id is not None:
        base.append(Appointment.id != appointment_id)

    provider_conflict = db.scalar(select(Appointment.id).where(and_(*base, Appointment.provider_id == provider_id)).limit(1))
    room_conflict = db.scalar(select(Appointment.id).where(and_(*base, Appointment.room_id == room_id)).limit(1))
    if (provider_conflict or room_conflict) and not allow_override:
        detail = []
        if provider_conflict:
            detail.append("liječnik je već zauzet")
        if room_conflict:
            detail.append("soba je već zauzeta")
        raise HTTPException(status_code=409, detail="Preklapanje termina: " + ", ".join(detail))
    return duration_minutes
