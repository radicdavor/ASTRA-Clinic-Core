from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor
from app.models.domain import Appointment, ClinicalFormInstance, JourneyActivity, PatientJourney, Room
from app.services.appointments import validate_appointment_payload
from app.services.patient_journeys import add_event


TERMINAL_ACTIVITY_STATUSES = {"completed", "not_performed", "cancelled"}
ALLOWED_ACTIVITY_TRANSITIONS = {
    "planned": {"ready", "not_performed", "cancelled"},
    "ready": {"in_progress", "not_performed", "cancelled"},
    "in_progress": {"completed", "not_performed"},
    "completed": set(),
    "not_performed": set(),
    "cancelled": set(),
}


def get_activity(db: Session, journey_id: int, activity_id: int) -> JourneyActivity:
    activity = db.scalar(
        select(JourneyActivity).where(
            JourneyActivity.id == activity_id,
            JourneyActivity.journey_id == journey_id,
        )
    )
    if not activity:
        raise HTTPException(404, detail="Aktivnost dolaska nije pronađena")
    return activity


def create_activity(
    db: Session,
    journey: PatientJourney,
    data: dict,
    actor: Actor,
    request: Request,
) -> JourneyActivity:
    if journey.current_stage in {"completed", "cancelled", "no_show"}:
        raise HTTPException(409, detail="Završenom dolasku nije moguće dodati novu aktivnost")
    if data["date"] != journey.appointment.date:
        raise HTTPException(409, detail="Sve aktivnosti jednog dolaska moraju biti planirane za isti datum")
    duplicate_key = db.scalar(
        select(JourneyActivity.id).where(
            JourneyActivity.journey_id == journey.id,
            JourneyActivity.activity_key == data["activity_key"],
        )
    )
    if duplicate_key:
        raise HTTPException(409, detail="Oznaka aktivnosti već postoji unutar ovog dolaska")

    dependency_id = data.pop("depends_on_activity_id", None)
    if dependency_id is not None:
        dependency = get_activity(db, journey.id, dependency_id)
    else:
        dependency = None

    duration = validate_appointment_payload(
        db,
        data["date"],
        data["start_time"],
        data["end_time"],
        data["provider_id"],
        data["room_id"],
        "scheduled",
        "manual",
        service_id=data["service_id"],
        patient_id=journey.patient_id,
    )
    room = db.get(Room, data["room_id"])
    sequence = (db.scalar(select(func.max(JourneyActivity.sequence)).where(JourneyActivity.journey_id == journey.id)) or 0) + 1
    notes = data.pop("notes", None)
    appointment = Appointment(
        patient_id=journey.patient_id,
        service_id=data["service_id"],
        provider_id=data["provider_id"],
        room_id=data["room_id"],
        episode_id=journey.appointment.episode_id,
        date=data["date"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        duration_minutes=duration,
        status="scheduled",
        source="manual",
        notes=notes,
        created_by=actor.user_id,
    )
    db.add(appointment)
    db.flush()
    activity = JourneyActivity(
        journey_id=journey.id,
        appointment_id=appointment.id,
        service_id=data["service_id"],
        activity_key=data["activity_key"],
        activity_kind=data["activity_kind"],
        specialty_key=data["specialty_key"],
        clinic_id=room.clinic_id if room else None,
        primary_provider_id=data["provider_id"],
        room_id=data["room_id"],
        sequence=sequence,
        depends_on_activity_id=dependency.id if dependency else None,
        required=data["required"],
        planned_start=datetime.combine(data["date"], data["start_time"]),
        planned_end=datetime.combine(data["date"], data["end_time"]),
        created_by=actor.user_id,
    )
    db.add(activity)
    db.flush()
    audit(db, "create", "Appointment", appointment.id, "Termin dodan postojećem dolasku", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(appointment), request)
    audit(db, "activity_created", "JourneyActivity", activity.id, "Aktivnost dodana dolasku", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(activity), request)
    add_event(db, journey, "activity_created", f"Dodana aktivnost {activity.activity_key}", actor, request, journey.current_stage, journey.current_stage, {"activity_id": activity.id, "appointment_id": appointment.id})
    return activity


def transition_activity(
    db: Session,
    journey: PatientJourney,
    activity: JourneyActivity,
    target: str,
    reason: str | None,
    actor: Actor,
    request: Request,
) -> None:
    if target not in ALLOWED_ACTIVITY_TRANSITIONS.get(activity.status, set()):
        raise HTTPException(409, detail=f"Prijelaz aktivnosti {activity.status} → {target} nije dopušten")
    if target == "ready" and activity.form_resolution_status not in {"resolved", "not_required", "legacy"}:
        raise HTTPException(409, detail="Obvezna dokumentacija aktivnosti još nije razriješena")
    if target == "in_progress":
        if journey.check_in_status != "ready":
            raise HTTPException(409, detail="Aktivnost ne može započeti prije dovršenog prijema")
        if not activity.primary_provider_id or not activity.room_id:
            raise HTTPException(409, detail="Prije početka odredite liječnika i prostoriju")
        if activity.depends_on_activity_id:
            dependency = get_activity(db, journey.id, activity.depends_on_activity_id)
            if dependency.status != "completed":
                raise HTTPException(409, detail="Prethodna obvezna aktivnost još nije dovršena")
    if target == "completed":
        form = db.scalar(
            select(ClinicalFormInstance)
            .where(
                ClinicalFormInstance.activity_id == activity.id,
                ClinicalFormInstance.status.notin_({"amended", "void"}),
            )
            .order_by(ClinicalFormInstance.id.desc())
            .limit(1)
        )
        if activity.form_resolution_status != "not_required" and (not form or form.status not in {"completed", "signed"}):
            raise HTTPException(409, detail="Klinički obrazac aktivnosti mora biti dovršen prije završetka aktivnosti")
    if target in {"not_performed", "cancelled"} and not reason:
        raise HTTPException(422, detail="Razlog je obvezan kada aktivnost nije obavljena")

    before = snapshot(activity)
    now = datetime.now(timezone.utc)
    activity.status = target
    if target == "in_progress":
        activity.actual_start = activity.actual_start or now
        activity.started_at = activity.started_at or now
        activity.started_by = actor.user_id
    elif target in TERMINAL_ACTIVITY_STATUSES:
        activity.actual_end = now
        activity.completed_at = now
        activity.completed_by = actor.user_id
        if target != "completed":
            activity.not_performed_reason = reason
    db.flush()
    audit(db, "activity_transition", "JourneyActivity", activity.id, reason or f"Aktivnost: {target}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(activity), request)
    add_event(db, journey, "activity_transition", reason or f"Aktivnost {activity.activity_key}: {target}", actor, request, journey.current_stage, journey.current_stage, {"activity_id": activity.id, "activity_status": target})
