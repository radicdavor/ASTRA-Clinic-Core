from datetime import date, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import TenantActorContext, get_patient_for_clinic, require_tenant_clinic
from app.core.database import get_db
from app.models.domain import Appointment, PatientIdentityReconciliationRequest, Room
from app.schemas.common import AITodayOut, AppointmentCreate, AppointmentOperationalOut, ErrorResponse, PatientCreate, PatientIdentityReconciliationStatusOut, PatientIdentityReviewRequired, PatientOut
from app.api.routes.patient_identity_reconciliation import requester_item, requester_out
from app.services.appointments import BLOCKING_STATUSES, create_appointment_with_journey, resolve_appointment_episode_reference
from app.services.patient_identity_reconciliation import create_patient_or_reconciliation

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api/ai", tags=["ai"], responses=ERROR_RESPONSES)


@router.post("/patients/create", response_model=PatientOut | PatientIdentityReviewRequired)
def ai_create_patient(payload: PatientCreate, request: Request, response: Response, db: Session = Depends(get_db), context: TenantActorContext = Depends(require_tenant_clinic("ai.patients.create"))):
    result = create_patient_or_reconciliation(db, payload, context.clinic_id, context.institution_id, context.actor, request)
    if isinstance(result, PatientIdentityReconciliationRequest):
        response.status_code = status.HTTP_202_ACCEPTED
        return PatientIdentityReviewRequired(request_id=result.id, status=result.status)
    return result


@router.get("/patient-identity-reconciliations/{request_id}", response_model=PatientIdentityReconciliationStatusOut)
def ai_reconciliation_status(request_id: str, request: Request, db: Session = Depends(get_db), context: TenantActorContext = Depends(require_tenant_clinic("ai.patients.create"))):
    item = requester_item(db, request_id, context.clinic_id)
    audit(db, "patient_identity.status_viewed", "PatientIdentityReconciliationRequest", None, "Otvoren status zahtjeva za pregled identiteta", context.actor.user_id, context.actor.actor_type, context.actor.api_key_id, None, {"request_id": item.id, "status": item.status}, request, scope_type="clinic", clinic_id=context.clinic_id, institution_id=context.institution_id)
    db.commit()
    return requester_out(item)


@router.post("/appointments/create", response_model=AppointmentOperationalOut)
def ai_create_appointment(payload: AppointmentCreate, request: Request, db: Session = Depends(get_db), context: TenantActorContext = Depends(require_tenant_clinic("ai.appointments.create"))):
    actor = context.actor
    data = payload.model_dump()
    get_patient_for_clinic(db, data["patient_id"], context.clinic_id)
    room = db.scalar(select(Room).where(Room.id == data["room_id"], Room.clinic_id == context.clinic_id))
    if room is None:
        raise HTTPException(404, detail="Prostorija nije pronađena")
    resolve_appointment_episode_reference(
        db,
        episode_id=data.get("episode_id"),
        patient_id=data["patient_id"],
        institution_id=context.institution_id,
    )
    data["clinic_id"] = context.clinic_id
    data["source"] = "ai_agent"
    appointment = create_appointment_with_journey(db,data,actor,request)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/today", response_model=AITodayOut)
def ai_today(db: Session = Depends(get_db), context: TenantActorContext = Depends(require_tenant_clinic("ai.free_slots.read"))):
    today = date.today()
    appointments = db.scalars(select(Appointment).options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room)).where(Appointment.date == today, Appointment.clinic_id == context.clinic_id).order_by(Appointment.start_time)).all()
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
    context: TenantActorContext = Depends(require_tenant_clinic("ai.free_slots.read")),
):
    start_day = date_from or day or date.today()
    end_day = date_to or start_day
    if service_id:
        from app.models.domain import Service

        service = db.get(Service, service_id)
        if service:
            duration_minutes = service.duration_minutes
    if room_id is not None and db.scalar(select(Room.id).where(Room.id == room_id, Room.clinic_id == context.clinic_id)) is None:
        raise HTTPException(404, detail="Prostorija nije pronađena")

    slots = []
    current_day = start_day
    while current_day <= end_day:
        query = select(Appointment).where(Appointment.date == current_day, Appointment.clinic_id == context.clinic_id, Appointment.status.in_(BLOCKING_STATUSES))
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
