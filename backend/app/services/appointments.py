from datetime import datetime, time

from fastapi import HTTPException, Request
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor
from app.models.domain import Appointment, AppointmentSource, AppointmentStatus, ClinicalEpisode, Patient, Provider, Room, Service, room_services
from app.services.patient_journeys import create_journey

BLOCKING_STATUSES = {
    AppointmentStatus.scheduled.value,
    AppointmentStatus.confirmed.value,
    AppointmentStatus.arrived.value,
    AppointmentStatus.in_progress.value,
    AppointmentStatus.waiting_for_result.value,
    AppointmentStatus.follow_up_needed.value,
    AppointmentStatus.rescheduled.value,
}

SOURCE_TO_INTAKE={"web_booking":"web","ai_agent":"ai_secretary"}

def create_appointment_with_journey(db:Session,data:dict,actor:Actor,request:Request)->Appointment:
    patient_id=data["patient_id"]
    if not db.get(Patient,patient_id): raise HTTPException(404,detail="Pacijent nije pronađen")
    episode_id=data.get("episode_id")
    if episode_id:
        episode=db.get(ClinicalEpisode,episode_id)
        if not episode: raise HTTPException(404,detail="Klinička epizoda nije pronađena")
        if episode.patient_id!=patient_id: raise HTTPException(422,detail="Klinička epizoda mora pripadati istom pacijentu kao termin")
    data["duration_minutes"]=validate_appointment_payload(db,data["date"],data["start_time"],data["end_time"],data["provider_id"],data["room_id"],data["status"],data["source"],service_id=data["service_id"])
    appointment=Appointment(**data,created_by=actor.user_id);db.add(appointment);db.flush()
    audit(db,"create","Appointment",appointment.id,f"Termin {appointment.date}",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(appointment),request)
    channel=SOURCE_TO_INTAKE.get(appointment.source,"manual")
    journey=create_journey(db,appointment,channel,"booked",actor,request)
    audit(db,"create","PatientJourney",journey.id,"Kanonski tijek pacijenta stvoren uz termin",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(journey),request)
    return appointment


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
    if appointment_date.weekday() == 6:
        raise HTTPException(status_code=422, detail="Nedjelja je neradni dan; unos termina nije dopušten")
    duration_minutes = calculate_duration_minutes(appointment_date, start_time, end_time)
    provider = db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Liječnik nije pronađen")
    if provider.staff_role != "physician":
        raise HTTPException(status_code=422, detail="Termin se može dodijeliti samo liječniku")
    if not provider.active or not provider.available_for_work:
        raise HTTPException(status_code=409, detail="Liječnik trenutačno ne radi")
    weekly = provider.weekly_working_hours or {}
    day_schedule = weekly.get(str(appointment_date.weekday()))
    if day_schedule is not None:
        if not day_schedule.get("enabled"):
            raise HTTPException(status_code=409, detail="Liječnik ne radi odabranog dana")
        provider_start = time.fromisoformat(day_schedule["start"])
        provider_end = time.fromisoformat(day_schedule["end"])
    else:
        provider_start, provider_end = provider.work_start, provider.work_end
    if start_time < provider_start or end_time > provider_end:
        raise HTTPException(status_code=409, detail=f"Termin je izvan radnog vremena liječnika ({provider_start.strftime('%H:%M')}–{provider_end.strftime('%H:%M')})")
    if service_id is not None:
        service = db.get(Service, service_id)
        room = db.get(Room, room_id)
        if not service:
            raise HTTPException(status_code=404, detail="Usluga nije pronadena")
        if not room:
            raise HTTPException(status_code=404, detail="Soba nije pronadena")
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
