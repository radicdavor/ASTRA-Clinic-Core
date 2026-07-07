from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, AuditLog, Clinic, ClinicalEpisode, ClinicalPlan, Module, Patient, Provider, Room, Service
from app.schemas.common import AppointmentOut, ClinicOut, ClinicalDecisionTimelineItem, ClinicalEpisodeCreate, ClinicalEpisodeOut, ClinicalEpisodeUpdate, ClinicalPlanGenerate, ClinicalPlanOut, ClinicalPlanUpdate, ErrorResponse, ReceptionArrivalRequest, ReceptionSlot, ServiceCreate, ServiceOut

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api", tags=["clinic"], responses=ERROR_RESPONSES)


def patch_model(obj, data: dict) -> None:
    for key, value in data.items():
        setattr(obj, key, value)


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail="Zapis s istim jedinstvenim identifikatorom vec postoji") from exc


def flush_or_conflict(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail="Zapis s istim jedinstvenim identifikatorom vec postoji") from exc


def scalar_count(db: Session, stmt) -> int:
    return int(db.scalar(stmt) or 0)


def get_episode_or_404(db: Session, episode_id: int) -> ClinicalEpisode:
    episode = db.scalar(
        select(ClinicalEpisode)
        .options(joinedload(ClinicalEpisode.patient), joinedload(ClinicalEpisode.owner_provider))
        .where(ClinicalEpisode.id == episode_id)
    )
    if not episode:
        raise HTTPException(404, detail="Klinička epizoda nije pronađena")
    return episode


def get_plan_or_404(db: Session, plan_id: int) -> ClinicalPlan:
    plan = db.get(ClinicalPlan, plan_id)
    if not plan:
        raise HTTPException(404, detail="Klinicki plan nije pronaden")
    return plan


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
            span = max(1, int((datetime.combine(date.today(), appointment.end_time) - datetime.combine(date.today(), appointment.start_time)).total_seconds() // 600))
            occupied_until = datetime.combine(date.today(), appointment.end_time)
            slots.append(ReceptionSlot(time=label, appointment=appointment, span=span, empty=False))
        elif occupied_until and current < occupied_until:
            slots.append(ReceptionSlot(time=label, appointment=None, span=0, empty=False))
        else:
            slots.append(ReceptionSlot(time=label, appointment=None, span=1, empty=True))
        current += timedelta(minutes=10)
    return slots


def active_plan_for_episode(db: Session, episode_id: int) -> ClinicalPlan | None:
    return db.scalar(select(ClinicalPlan).where(ClinicalPlan.episode_id == episode_id, ClinicalPlan.status == "active", ClinicalPlan.physician_confirmed.is_(True)).order_by(ClinicalPlan.confirmed_at.desc(), ClinicalPlan.id.desc()))


def pending_plan_for_episode(db: Session, episode_id: int) -> ClinicalPlan | None:
    return db.scalar(select(ClinicalPlan).where(ClinicalPlan.episode_id == episode_id, ClinicalPlan.physician_confirmed.is_(False), ClinicalPlan.status.in_(["draft", "waiting"])).order_by(ClinicalPlan.created_at.desc(), ClinicalPlan.id.desc()))


def propose_plan(payload: ClinicalPlanGenerate, episode: ClinicalEpisode) -> dict:
    text = " ".join([payload.procedure_type or "", payload.findings or "", payload.physician_conclusion or "", payload.episode_goal or "", episode.summary or "", episode.clinical_notes or ""]).lower()
    confidence = Decimal("0.91")
    if payload.pathology_ordered or "patolog" in text or "ph" in text or "biops" in text:
        next_action = "wait_for_pathology"
        proposed_status = "waiting"
        due_date = date.today() + timedelta(days=14)
        priority = "important"
        rationale = "AI prijedlog: nalaz/patologija je oznacena kao otvorena stavka. Lijecnik mora pregledati nalaz prije odluke."
        suggested_follow_up = "Nakon dolaska patologije pregledati rezultat i odrediti daljnji interval pracenja."
    elif "kontrol" in text or "follow" in text:
        next_action = "follow_up_visit"
        proposed_status = "active"
        due_date = date.today() + timedelta(days=30)
        priority = "routine"
        rationale = "AI prijedlog: zakazati kontrolni pregled prema zakljucku lijecnika."
        suggested_follow_up = "Kontrolni pregled prema dogovoru lijecnika i pacijenta."
    elif "ponov" in text or "repeat" in text or "endoskop" in text:
        next_action = "repeat_endoscopy"
        proposed_status = "active"
        due_date = date.today() + timedelta(days=90)
        priority = "important"
        rationale = "AI prijedlog: tekst upucuje na ponavljanje endoskopskog postupka."
        suggested_follow_up = "Planirati ponavljanje postupka nakon lijecnicke provjere indikacije."
    elif "zavr" in text or "uredan" in text:
        next_action = "episode_completed"
        proposed_status = "completed"
        due_date = None
        priority = "routine"
        rationale = "AI prijedlog: zakljucak djeluje zavrsno, ali epizodu smije zatvoriti samo lijecnik potvrdom plana."
        suggested_follow_up = "Nema automatske kontrole bez potvrde lijecnika."
    else:
        next_action = "follow_up_visit"
        proposed_status = "active"
        due_date = date.today() + timedelta(days=30)
        priority = "routine"
        rationale = "AI prijedlog: nema dovoljno specificnog konteksta za precizniji plan. Manual review recommended."
        suggested_follow_up = "Rucno odrediti daljnji korak."
        confidence = Decimal("0.58")
    if not payload.physician_conclusion and not payload.findings:
        confidence = min(confidence, Decimal("0.55"))
        rationale = f"{rationale} Manual review recommended."
    return {
        "source": "ai_suggestion",
        "status": "draft",
        "proposed_episode_status": proposed_status,
        "next_action": next_action,
        "due_date": due_date,
        "priority": priority,
        "rationale": rationale,
        "suggested_follow_up": suggested_follow_up,
        "physician_conclusion": payload.physician_conclusion,
        "ai_confidence": confidence,
        "physician_confirmed": False,
    }


def episode_with_count(db: Session, episode: ClinicalEpisode) -> ClinicalEpisodeOut:
    data = ClinicalEpisodeOut.model_validate(episode)
    data.appointment_count = scalar_count(db, select(func.count(Appointment.id)).where(Appointment.episode_id == episode.id))
    return data


@router.get("/episodes", response_model=list[ClinicalEpisodeOut])
def list_episodes(
    patient_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("episodes.read")),
):
    stmt = select(ClinicalEpisode).options(joinedload(ClinicalEpisode.patient), joinedload(ClinicalEpisode.owner_provider)).order_by(ClinicalEpisode.start_date.desc(), ClinicalEpisode.id.desc())
    if patient_id:
        stmt = stmt.where(ClinicalEpisode.patient_id == patient_id)
    if status:
        stmt = stmt.where(ClinicalEpisode.status == status)
    return [episode_with_count(db, episode) for episode in db.scalars(stmt).all()]


@router.post("/episodes", response_model=ClinicalEpisodeOut)
def create_episode(
    payload: ClinicalEpisodeCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("episodes.write")),
):
    if not db.get(Patient, payload.patient_id):
        raise HTTPException(404, detail="Pacijent nije pronađen")
    if payload.owner_provider_id and not db.get(Provider, payload.owner_provider_id):
        raise HTTPException(404, detail="Liječnik nije pronađen")
    episode = ClinicalEpisode(**payload.model_dump(), created_by=actor.user_id)
    db.add(episode)
    db.flush()
    audit(db, "create", "ClinicalEpisode", episode.id, f"Kreirana epizoda: {episode.title}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(episode), request)
    db.commit()
    db.refresh(episode)
    return episode_with_count(db, get_episode_or_404(db, episode.id))


@router.get("/episodes/{episode_id}", response_model=ClinicalEpisodeOut)
def get_episode(episode_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("episodes.read"))):
    return episode_with_count(db, get_episode_or_404(db, episode_id))


@router.patch("/episodes/{episode_id}", response_model=ClinicalEpisodeOut)
def update_episode(
    episode_id: int,
    payload: ClinicalEpisodeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("episodes.write")),
):
    episode = get_episode_or_404(db, episode_id)
    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("owner_provider_id") and not db.get(Provider, update_data["owner_provider_id"]):
        raise HTTPException(404, detail="Liječnik nije pronađen")
    before = snapshot(episode)
    patch_model(episode, update_data)
    db.flush()
    audit(db, "update", "ClinicalEpisode", episode.id, f"Ažurirana epizoda: {episode.title}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(episode), request)
    db.commit()
    db.refresh(episode)
    return episode_with_count(db, get_episode_or_404(db, episode.id))


@router.post("/episodes/{episode_id}/close", response_model=ClinicalEpisodeOut)
def close_episode(
    episode_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("episodes.write")),
):
    episode = get_episode_or_404(db, episode_id)
    before = snapshot(episode)
    episode.status = "completed"
    if episode.end_date is None:
        episode.end_date = date.today()
    db.flush()
    audit(db, "close", "ClinicalEpisode", episode.id, f"Zatvorena epizoda: {episode.title}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(episode), request)
    db.commit()
    db.refresh(episode)
    return episode_with_count(db, get_episode_or_404(db, episode.id))


@router.get("/episodes/{episode_id}/appointments", response_model=list[AppointmentOut])
def episode_appointments(episode_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    get_episode_or_404(db, episode_id)
    return db.scalars(
        select(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room), joinedload(Appointment.episode).joinedload(ClinicalEpisode.patient), joinedload(Appointment.episode).joinedload(ClinicalEpisode.owner_provider))
        .where(Appointment.episode_id == episode_id)
        .order_by(Appointment.date.desc(), Appointment.start_time.desc())
    ).all()


@router.get("/episodes/{episode_id}/clinical-plans", response_model=list[ClinicalPlanOut])
def episode_clinical_plans(episode_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_plans.read"))):
    get_episode_or_404(db, episode_id)
    return db.scalars(select(ClinicalPlan).where(ClinicalPlan.episode_id == episode_id).order_by(ClinicalPlan.created_at.desc(), ClinicalPlan.id.desc())).all()


@router.get("/episodes/{episode_id}/clinical-plans/active", response_model=ClinicalPlanOut | None)
def episode_active_clinical_plan(episode_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_plans.read"))):
    get_episode_or_404(db, episode_id)
    return active_plan_for_episode(db, episode_id)


@router.post("/episodes/{episode_id}/clinical-plans/generate", response_model=ClinicalPlanOut)
def generate_clinical_plan(
    episode_id: int,
    payload: ClinicalPlanGenerate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_plans.write")),
):
    episode = get_episode_or_404(db, episode_id)
    if payload.appointment_id:
        appointment = db.get(Appointment, payload.appointment_id)
        if not appointment or appointment.episode_id != episode.id:
            raise HTTPException(422, detail="Termin mora pripadati istoj epizodi")
    pending_plans = db.scalars(
        select(ClinicalPlan).where(
            ClinicalPlan.episode_id == episode.id,
            ClinicalPlan.physician_confirmed.is_(False),
            ClinicalPlan.status.in_(["draft", "waiting"]),
        )
    ).all()
    for pending in pending_plans:
        before = snapshot(pending)
        pending.status = "cancelled"
        db.flush()
        audit(db, "ai_plan_superseded", "ClinicalPlan", pending.id, "Stariji AI prijedlog plana je zamijenjen novim prijedlogom", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(pending), request)
    plan = ClinicalPlan(episode_id=episode.id, **propose_plan(payload, episode))
    db.add(plan)
    db.flush()
    audit(db, "ai_plan_generated", "ClinicalPlan", plan.id, f"AI prijedlog plana za epizodu #{episode.id}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(plan), request)
    db.commit()
    db.refresh(plan)
    return plan


@router.patch("/clinical-plans/{plan_id}", response_model=ClinicalPlanOut)
def edit_clinical_plan(
    plan_id: int,
    payload: ClinicalPlanUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_plans.write")),
):
    plan = get_plan_or_404(db, plan_id)
    if plan.physician_confirmed:
        raise HTTPException(422, detail="Potvrdeni plan se ne ureduje. Kreirajte novi prijedlog plana.")
    before = snapshot(plan)
    patch_model(plan, payload.model_dump(exclude_unset=True))
    plan.source = "physician"
    db.flush()
    audit(db, "ai_plan_edited", "ClinicalPlan", plan.id, "Lijecnik je uredio AI prijedlog plana", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(plan), request)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/clinical-plans/{plan_id}/reject", response_model=ClinicalPlanOut)
def reject_clinical_plan(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_plans.write")),
):
    plan = get_plan_or_404(db, plan_id)
    if plan.physician_confirmed:
        raise HTTPException(422, detail="Potvrdeni plan se ne moze odbiti")
    if plan.status not in {"draft", "waiting"}:
        raise HTTPException(422, detail="Samo aktivni prijedlog koji ceka odluku moze biti odbijen")
    before = snapshot(plan)
    plan.status = "cancelled"
    db.flush()
    audit(db, "ai_plan_rejected", "ClinicalPlan", plan.id, "AI prijedlog plana je odbijen", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(plan), request)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/clinical-plans/{plan_id}/confirm", response_model=ClinicalPlanOut)
def confirm_clinical_plan(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_plans.write")),
):
    plan = get_plan_or_404(db, plan_id)
    if plan.physician_confirmed and plan.status == "active":
        return plan
    if plan.physician_confirmed:
        raise HTTPException(422, detail="Arhivirani potvrdeni plan se ne moze ponovno potvrditi")
    if plan.status == "cancelled":
        raise HTTPException(422, detail="Odbijeni plan se ne moze potvrditi")
    if plan.status not in {"draft", "waiting"}:
        raise HTTPException(422, detail="Samo prijedlog plana koji ceka odluku moze biti potvrden")
    episode = get_episode_or_404(db, plan.episode_id)
    plan_before = snapshot(plan)
    episode_before = snapshot(episode)
    previous_active = active_plan_for_episode(db, episode.id)
    if previous_active and previous_active.id != plan.id:
        previous_before = snapshot(previous_active)
        previous_active.status = "archived"
        db.flush()
        audit(db, "clinical_plan_archived", "ClinicalPlan", previous_active.id, "Prethodni aktivni klinicki plan je arhiviran", actor.user_id, actor.actor_type, actor.api_key_id, previous_before, snapshot(previous_active), request)
    plan.status = "active"
    plan.physician_confirmed = True
    plan.confirmed_by = actor.user_id
    plan.confirmed_at = datetime.now(timezone.utc)
    if plan.proposed_episode_status:
        episode.status = plan.proposed_episode_status
        if episode.status == "completed" and episode.end_date is None:
            episode.end_date = date.today()
    episode.priority = plan.priority
    flush_or_conflict(db)
    audit(db, "ai_plan_confirmed", "ClinicalPlan", plan.id, "Lijecnik je potvrdio klinicki plan", actor.user_id, actor.actor_type, actor.api_key_id, plan_before, snapshot(plan), request)
    audit(db, "update", "ClinicalEpisode", episode.id, "Epizoda azurirana potvrdenim klinickim planom", actor.user_id, actor.actor_type, actor.api_key_id, episode_before, snapshot(episode), request)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/episodes/{episode_id}/clinical-timeline", response_model=list[ClinicalDecisionTimelineItem])
def episode_clinical_timeline(episode_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_plans.read"))):
    get_episode_or_404(db, episode_id)
    plan_ids = db.scalars(select(ClinicalPlan.id).where(ClinicalPlan.episode_id == episode_id)).all()
    conditions = [and_(AuditLog.entity_type == "ClinicalEpisode", AuditLog.entity_id == episode_id)]
    if plan_ids:
        conditions.append(and_(AuditLog.entity_type == "ClinicalPlan", AuditLog.entity_id.in_(plan_ids)))
    logs = db.scalars(select(AuditLog).where(or_(*conditions)).order_by(AuditLog.created_at.desc()).limit(100)).all()
    labels = {
        "ai_plan_generated": "AI predlozio plan",
        "ai_plan_edited": "Lijecnik uredio prijedlog",
        "ai_plan_rejected": "Lijecnik odbio prijedlog",
        "ai_plan_confirmed": "Lijecnik potvrdio plan",
        "clinical_plan_archived": "Plan arhiviran",
        "ai_plan_superseded": "AI prijedlog zamijenjen",
        "update": "Epizoda azurirana",
        "close": "Epizoda zatvorena",
        "create": "Epizoda kreirana",
    }
    return [
        ClinicalDecisionTimelineItem(id=log.id, action=log.action, label=labels.get(log.action, log.action), summary=log.summary, source="AI Suggested" if log.action == "ai_plan_generated" else "Human Confirmed" if log.action == "ai_plan_confirmed" else log.actor_type, created_at=log.created_at)
        for log in logs
    ]


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
        .options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider).joinedload(Provider.clinic), joinedload(Appointment.room).joinedload(Room.clinic))
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
    appointment = db.scalar(select(Appointment).options(joinedload(Appointment.patient)).where(Appointment.id == appointment_id))
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
        .options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room))
        .where(Appointment.id == appointment.id)
    )


@router.get("/search")
def search(q: str, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("patients.read"))):
    like = f"%{q}%"
    return {
        "patients": db.scalars(select(Patient).where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Patient.oib.ilike(like))).limit(10)).all(),
        "services": db.scalars(select(Service).where(Service.name.ilike(like)).limit(10)).all(),
        "appointments": db.scalars(select(Appointment).join(Appointment.patient).join(Appointment.service).where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Service.name.ilike(like), Appointment.status.ilike(like))).limit(10)).all(),
    }


@router.get("/services", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.read"))):
    return db.scalars(select(Service).order_by(Service.name)).all()


@router.get("/clinics", response_model=list[ClinicOut])
def list_clinics(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Clinic).where(Clinic.active.is_(True)).order_by(Clinic.name)).all()


@router.post("/services", response_model=ServiceOut)
def create_service(payload: ServiceCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.write"))):
    service = Service(**payload.model_dump())
    db.add(service)
    db.flush()
    audit(db, "create", "Service", service.id, service.name, actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(service), request)
    db.commit()
    db.refresh(service)
    return service


@router.get("/modules")
def list_modules(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("modules.read"))):
    return db.scalars(select(Module).order_by(Module.name)).all()


@router.get("/providers")
def list_providers(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Provider).order_by(Provider.full_name)).all()


@router.get("/rooms")
def list_rooms(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Room).order_by(Room.name)).all()


@router.get("/audit-log")
def audit_log(
    entity_type: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    actor_type: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("audit.read")),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor_type:
        stmt = stmt.where(AuditLog.actor_type == actor_type)
    return db.scalars(stmt).all()
