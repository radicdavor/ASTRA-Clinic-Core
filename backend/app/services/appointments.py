from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.domain import Appointment, AppointmentSource, AppointmentStatus, Provider, Room, Service, room_services

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
    service_id: int | None = None,
    appointment_id: int | None = None,
    allow_override: bool = False,
) -> int:
    validate_status_and_source(status_value, source_value)
    duration_minutes = calculate_duration_minutes(appointment_date, start_time, end_time)
    if service_id is not None:
        service = db.get(Service, service_id)
        room = db.get(Room, room_id)
        provider = db.get(Provider, provider_id)
        if not service:
            raise HTTPException(status_code=404, detail="Usluga nije pronadena")
        if not room:
            raise HTTPException(status_code=404, detail="Soba nije pronadena")
        if not provider:
            raise HTTPException(status_code=404, detail="Lijecnik nije pronaden")
        allowed = db.scalar(select(room_services.c.room_id).where(room_services.c.room_id == room_id, room_services.c.service_id == service_id).limit(1))
        room_has_service_rules = db.scalar(select(room_services.c.service_id).where(room_services.c.room_id == room_id).limit(1))
        if room_has_service_rules and not allowed:
            raise HTTPException(status_code=409, detail="Usluga nije dopustena u odabranoj sobi")
        if room.clinic_id and provider.clinic_id and room.clinic_id != provider.clinic_id:
            raise HTTPException(status_code=409, detail="Lijecnik i soba nisu u istoj klinici")
        if service.duration_minutes and service.duration_minutes != duration_minutes:
            raise HTTPException(status_code=409, detail="Trajanje termina ne odgovara trajanju usluge")
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
