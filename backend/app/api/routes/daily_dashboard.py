from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, Patient, PatientJourney
from app.schemas.daily_dashboard import DailyDashboardResponse, DailyDashboardRow


router = APIRouter(prefix="/api/dashboard", tags=["daily-dashboard"])


@router.get("/day", response_model=DailyDashboardResponse)
def daily_dashboard(
    selected_date: date,
    clinician_id: int | None = None,
    room_id: int | None = None,
    service_id: int | None = None,
    status: str | None = None,
    blocker: bool | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("journey.read")),
):
    stmt = (
        select(PatientJourney)
        .join(PatientJourney.appointment)
        .join(PatientJourney.patient)
        .options(
            joinedload(PatientJourney.patient),
            joinedload(PatientJourney.appointment).joinedload(Appointment.service),
            joinedload(PatientJourney.appointment).joinedload(Appointment.provider),
            joinedload(PatientJourney.appointment).joinedload(Appointment.room),
            selectinload(PatientJourney.blockers),
        )
        .where(Appointment.date == selected_date)
        .order_by(Appointment.start_time, Patient.last_name, Patient.first_name)
    )
    if clinician_id:
        stmt = stmt.where(Appointment.provider_id == clinician_id)
    if room_id:
        stmt = stmt.where(Appointment.room_id == room_id)
    if service_id:
        stmt = stmt.where(Appointment.service_id == service_id)
    if status:
        stmt = stmt.where(PatientJourney.current_stage == status)
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(Patient.first_name.ilike(term), Patient.last_name.ilike(term)))
    journeys = db.scalars(stmt).unique().all()
    rows = []
    for journey in journeys:
        open_blockers = [item for item in journey.blockers if item.status == "open"]
        if blocker is True and not open_blockers:
            continue
        if blocker is False and open_blockers:
            continue
        appointment = journey.appointment
        allowed_actions = []
        if "checkin.update" in actor.permissions and journey.current_stage == "ready_for_arrival":
            allowed_actions.append("mark_arrived")
        if "checkin.update" in actor.permissions and journey.current_stage in {"arrived", "check_in_review"}:
            allowed_actions.append("open_check_in")
        if "encounter.read" in actor.permissions and journey.current_stage in {"ready_for_clinician", "in_encounter"}:
            allowed_actions.append("open_encounter")
        rows.append(DailyDashboardRow(
            journey_id=journey.id, appointment_id=appointment.id, time=appointment.start_time,
            patient_id=journey.patient_id,
            patient_name=f"{journey.patient.first_name} {journey.patient.last_name}".strip(),
            patient_date_of_birth=journey.patient.date_of_birth,
            service_id=appointment.service_id, service_name=appointment.service.name,
            clinician_id=appointment.provider_id, clinician_name=appointment.provider.full_name,
            room_id=appointment.room_id, room_name=appointment.room.name,
            intake_channel=journey.intake_channel, workflow_stage=journey.current_stage,
            document_status=journey.document_status, preparation_status=journey.preparation_status,
            arrival_status="arrived" if appointment.arrived_at else "not_arrived",
            check_in_status=journey.check_in_status, encounter_status=journey.encounter_status,
            consumables_status=journey.consumables_status, billing_status=journey.billing_status,
            payment_status=journey.payment_status,
            blocker_status="blocked" if open_blockers else "clear",
            blocker_labels=[item.title for item in open_blockers],
            blockers=[{"id": item.id, "title": item.title, "details": item.details, "is_clinical": item.is_clinical} for item in open_blockers],
            allowed_actions=allowed_actions,
        ))
    sections = ["operations", "documents", "preparation", "check_in"]
    if "encounter.read" in actor.permissions:
        sections.extend(["clinical", "encounter"])
    if "billing.read" in actor.permissions:
        sections.extend(["billing", "payment"])
    return DailyDashboardResponse(date=selected_date, refreshed_at=datetime.now(timezone.utc), visible_sections=sections, rows=rows)
