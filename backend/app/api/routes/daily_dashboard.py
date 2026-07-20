from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, Clinic, JourneyActivity, JourneyCheckIn, Patient, PatientJourney, Provider, Room
from app.schemas.daily_dashboard import DailyDashboardResponse, DailyDashboardRow


router = APIRouter(prefix="/api/dashboard", tags=["daily-dashboard"])


@router.get("/day", response_model=DailyDashboardResponse)
def daily_dashboard(
    selected_date: date,
    clinician_id: int | None = None,
    clinic_id: int | None = None,
    room_id: int | None = None,
    service_id: int | None = None,
    status: str | None = None,
    blocker: bool | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("journey.read")),
):
    role_name = actor.user.role.name if actor.user else "api_key"
    normalized_role = role_name.removeprefix("demo_")
    is_admin = normalized_role == "admin"
    scoped_provider = None
    if normalized_role == "physician":
        scoped_provider = db.scalar(
            select(Provider).where(Provider.email.ilike(actor.user.email), Provider.active.is_(True))
        )
        if scoped_provider is None:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Korisnički račun liječnika nije povezan s osobljem. Administrator treba uskladiti službeni e-mail.",
            )
        if clinician_id is not None and clinician_id != scoped_provider.id:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Liječnik može otvoriti samo vlastiti dnevni raspored")
        clinician_id = scoped_provider.id

    clinic_stmt = (
        select(Clinic.id, Clinic.name)
        .join(JourneyActivity, JourneyActivity.clinic_id == Clinic.id)
        .join(PatientJourney, PatientJourney.id == JourneyActivity.journey_id)
        .join(Appointment, Appointment.id == PatientJourney.appointment_id)
        .where(Appointment.date == selected_date)
        .distinct()
        .order_by(Clinic.name)
    )
    if clinician_id:
        clinic_stmt = clinic_stmt.where(JourneyActivity.primary_provider_id == clinician_id)
    available_clinics = [{"id": item.id, "name": item.name} for item in db.execute(clinic_stmt).all()]

    stmt = (
        select(PatientJourney)
        .join(PatientJourney.appointment)
        .join(PatientJourney.patient)
        .options(
            joinedload(PatientJourney.patient),
            joinedload(PatientJourney.appointment).joinedload(Appointment.service),
            joinedload(PatientJourney.appointment).joinedload(Appointment.provider),
            joinedload(PatientJourney.appointment).joinedload(Appointment.room).joinedload(Room.clinic),
            selectinload(PatientJourney.blockers),
            selectinload(PatientJourney.activities).joinedload(JourneyActivity.service),
            selectinload(PatientJourney.activities).joinedload(JourneyActivity.primary_provider),
            selectinload(PatientJourney.activities).joinedload(JourneyActivity.room),
        )
        .where(Appointment.date == selected_date)
        .order_by(Appointment.start_time, Patient.last_name, Patient.first_name)
    )
    if clinician_id:
        stmt = stmt.where(PatientJourney.activities.any(JourneyActivity.primary_provider_id == clinician_id))
    if clinic_id:
        stmt = stmt.where(PatientJourney.activities.any(JourneyActivity.clinic_id == clinic_id))
    if room_id:
        stmt = stmt.where(PatientJourney.activities.any(JourneyActivity.room_id == room_id))
    if service_id:
        stmt = stmt.where(PatientJourney.activities.any(JourneyActivity.service_id == service_id))
    if status:
        stmt = stmt.where(PatientJourney.current_stage == status)
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(Patient.first_name.ilike(term), Patient.last_name.ilike(term)))
    journeys = db.scalars(stmt).unique().all()
    journey_ids = [item.id for item in journeys]
    check_ins = db.scalars(
        select(JourneyCheckIn).options(selectinload(JourneyCheckIn.items)).where(JourneyCheckIn.journey_id.in_(journey_ids))
    ).all() if journey_ids else []
    reception_warnings = {
        check_in.journey_id: [
            item.note for item in check_in.items
            if item.note and item.state in {"requires_clinician_review", "blocked"}
        ]
        for check_in in check_ins
    }
    rows = []
    for journey in journeys:
        open_blockers = [item for item in journey.blockers if item.status == "open"]
        warning_details = reception_warnings.get(journey.id, [])
        has_problem_signal = bool(open_blockers or warning_details)
        if blocker is True and not has_problem_signal:
            continue
        if blocker is False and has_problem_signal:
            continue
        appointment = journey.appointment
        activities = sorted(journey.activities, key=lambda item: item.sequence)
        current_activity = next((item for item in activities if item.status == "in_progress"), None) or next((item for item in activities if item.status == "ready"), None)
        remaining = [item for item in activities if item.status not in {"completed", "not_performed", "cancelled"}]
        if current_activity is None and remaining:
            current_activity = remaining[0]
        next_activity = next((item for item in remaining if current_activity and item.sequence > current_activity.sequence), None)
        allowed_actions = []
        if "checkin.update" in actor.permissions and journey.current_stage in {"booked", "awaiting_forms", "awaiting_documents", "preparation_in_progress", "ready_for_arrival", "arrived", "check_in_review"}:
            allowed_actions.append("open_check_in")
        if "encounter.read" in actor.permissions and journey.current_stage in {"ready_for_clinician", "in_encounter"}:
            allowed_actions.append("open_encounter")
        if "consumables.record" in actor.permissions and journey.current_stage == "procedure_completed":
            allowed_actions.append("record_consumables")
        if "billing.write" in actor.permissions and journey.current_stage == "awaiting_billing":
            allowed_actions.append("prepare_billing")
        if "billing.read" in actor.permissions and journey.current_stage == "awaiting_payment":
            allowed_actions.append("open_payment")
        rows.append(DailyDashboardRow(
            journey_id=journey.id, appointment_id=appointment.id, time=appointment.start_time,
            patient_id=journey.patient_id,
            patient_name=f"{journey.patient.first_name} {journey.patient.last_name}".strip(),
            patient_date_of_birth=journey.patient.date_of_birth,
            service_id=appointment.service_id, service_name=appointment.service.name,
            clinician_id=appointment.provider_id, clinician_name=appointment.provider.full_name,
            room_id=appointment.room_id, room_name=appointment.room.name,
            clinic_id=appointment.room.clinic_id,
            clinic_name=appointment.room.clinic.name if appointment.room.clinic else None,
            intake_channel=journey.intake_channel, workflow_stage=journey.current_stage,
            document_status=journey.document_status, preparation_status=journey.preparation_status,
            arrival_status="arrived" if appointment.arrived_at else "not_arrived",
            check_in_status=journey.check_in_status, encounter_status=journey.encounter_status,
            consumables_status=journey.consumables_status, billing_status=journey.billing_status,
            payment_status=journey.payment_status,
            blocker_status="blocked" if open_blockers else "clear",
            blocker_labels=[item.title for item in open_blockers],
            blockers=[{"id": item.id, "title": item.title, "details": item.details, "is_clinical": item.is_clinical} for item in open_blockers],
            reception_warning=bool(warning_details),
            reception_warning_details=warning_details,
            allowed_actions=allowed_actions,
            activity_count=len(activities),
            current_activity_id=current_activity.id if current_activity else None,
            next_activity_id=next_activity.id if next_activity else None,
            activities=[{
                "id": item.id,
                "sequence": item.sequence,
                "time": item.planned_start.time(),
                "end_time": item.planned_end.time(),
                "service_name": item.service.name,
                "clinician_name": item.primary_provider.full_name if item.primary_provider else None,
                "room_name": item.room.name if item.room else None,
                "status": item.status,
            } for item in activities],
        ))
    sections = ["operations", "documents", "preparation", "check_in"]
    if "encounter.read" in actor.permissions:
        sections.extend(["clinical", "encounter"])
    if "billing.read" in actor.permissions:
        sections.extend(["billing", "payment"])
    if scoped_provider:
        scope = "own_clinician"
        scope_label = scoped_provider.full_name
    elif is_admin:
        scope = "all"
        scope_label = "Svi liječnici"
    else:
        scope = "operational"
        scope_label = "Operativni pregled"
    return DailyDashboardResponse(
        date=selected_date,
        refreshed_at=datetime.now(timezone.utc),
        visible_sections=sections,
        viewer_role=normalized_role,
        scope=scope,
        scope_label=scope_label,
        scoped_clinician_id=scoped_provider.id if scoped_provider else None,
        can_filter_clinician=is_admin,
        available_clinics=available_clinics,
        rows=rows,
    )
