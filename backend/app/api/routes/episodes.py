from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import CurrentUserContext, get_scoped_patient, require_active_clinic
from app.core.database import get_db
from app.models.domain import Appointment, AuditLog, Clinic, ClinicalEpisode, ClinicalPlan, Provider
from app.schemas.common import AppointmentOut, ClinicalDecisionTimelineItem, ClinicalEpisodeCreate, ClinicalEpisodeOut, ClinicalEpisodeUpdate, ClinicalPlanGenerate, ClinicalPlanOut, ClinicalPlanUpdate, ErrorResponse
from app.services.clinical_scope import authorized_institution_id, get_institution_clinical_plan, get_institution_episode, institution_episode_statement, provider_belongs_to_institution

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api", tags=["episodes"], responses=ERROR_RESPONSES)


def patch_model(obj, data: dict) -> None:
    for key, value in data.items():
        setattr(obj, key, value)


def flush_or_conflict(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail="Zapis s istim jedinstvenim identifikatorom vec postoji") from exc


def scalar_count(db: Session, stmt) -> int:
    return int(db.scalar(stmt) or 0)


def get_episode_or_404(db: Session, episode_id: int, context: CurrentUserContext) -> ClinicalEpisode:
    return get_institution_episode(db, episode_id, context)


def get_plan_or_404(db: Session, plan_id: int, context: CurrentUserContext) -> ClinicalPlan:
    return get_institution_clinical_plan(db, plan_id, context)


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
    data.appointment_count = scalar_count(
        db,
        select(func.count(Appointment.id))
        .join(Clinic, Clinic.id == Appointment.clinic_id)
        .where(Appointment.episode_id == episode.id, Clinic.institution_id == episode.institution_id),
    )
    return data


@router.get("/episodes", response_model=list[ClinicalEpisodeOut])
def list_episodes(
    patient_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("episodes.read")),
):
    stmt = institution_episode_statement(context).order_by(ClinicalEpisode.start_date.desc(), ClinicalEpisode.id.desc())
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
    context: CurrentUserContext = Depends(require_active_clinic("episodes.write")),
):
    get_scoped_patient(db, payload.patient_id, context)
    actor = context.actor
    provider = db.get(Provider, payload.owner_provider_id) if payload.owner_provider_id else None
    if payload.owner_provider_id and (provider is None or not provider_belongs_to_institution(db, provider.clinic_id, context)):
        raise HTTPException(404, detail="Liječnik nije pronađen")
    episode = ClinicalEpisode(
        **payload.model_dump(),
        institution_id=authorized_institution_id(context),
        created_by=actor.user_id,
    )
    db.add(episode)
    db.flush()
    audit(db, "create", "ClinicalEpisode", episode.id, f"Kreirana epizoda: {episode.title}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(episode), request)
    db.commit()
    db.refresh(episode)
    return episode_with_count(db, get_episode_or_404(db, episode.id, context))


@router.get("/episodes/{episode_id}", response_model=ClinicalEpisodeOut)
def get_episode(episode_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("episodes.read"))):
    return episode_with_count(db, get_episode_or_404(db, episode_id, context))


@router.patch("/episodes/{episode_id}", response_model=ClinicalEpisodeOut)
def update_episode(
    episode_id: int,
    payload: ClinicalEpisodeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("episodes.write")),
):
    actor = context.actor
    episode = get_episode_or_404(db, episode_id, context)
    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("owner_provider_id"):
        provider = db.get(Provider, update_data["owner_provider_id"])
        if provider is None or not provider_belongs_to_institution(db, provider.clinic_id, context):
            raise HTTPException(404, detail="Liječnik nije pronađen")
    before = snapshot(episode)
    patch_model(episode, update_data)
    db.flush()
    audit(db, "update", "ClinicalEpisode", episode.id, f"Ažurirana epizoda: {episode.title}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(episode), request)
    db.commit()
    db.refresh(episode)
    return episode_with_count(db, get_episode_or_404(db, episode.id, context))


@router.post("/episodes/{episode_id}/close", response_model=ClinicalEpisodeOut)
def close_episode(
    episode_id: int,
    request: Request,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("episodes.write")),
):
    actor = context.actor
    episode = get_episode_or_404(db, episode_id, context)
    before = snapshot(episode)
    episode.status = "completed"
    if episode.end_date is None:
        episode.end_date = date.today()
    db.flush()
    audit(db, "close", "ClinicalEpisode", episode.id, f"Zatvorena epizoda: {episode.title}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(episode), request)
    db.commit()
    db.refresh(episode)
    return episode_with_count(db, get_episode_or_404(db, episode.id, context))


@router.get("/episodes/{episode_id}/appointments", response_model=list[AppointmentOut])
def episode_appointments(episode_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("appointments.read"))):
    episode = get_episode_or_404(db, episode_id, context)
    return db.scalars(
        select(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room), joinedload(Appointment.episode).joinedload(ClinicalEpisode.patient), joinedload(Appointment.episode).joinedload(ClinicalEpisode.owner_provider))
        .join(Clinic, Clinic.id == Appointment.clinic_id)
        .where(Appointment.episode_id == episode_id, Clinic.institution_id == episode.institution_id)
        .order_by(Appointment.date.desc(), Appointment.start_time.desc())
    ).all()


@router.get("/episodes/{episode_id}/clinical-plans", response_model=list[ClinicalPlanOut])
def episode_clinical_plans(episode_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_plans.read"))):
    get_episode_or_404(db, episode_id, context)
    return db.scalars(select(ClinicalPlan).where(ClinicalPlan.episode_id == episode_id).order_by(ClinicalPlan.created_at.desc(), ClinicalPlan.id.desc())).all()


@router.get("/episodes/{episode_id}/clinical-plans/active", response_model=ClinicalPlanOut | None)
def episode_active_clinical_plan(episode_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_plans.read"))):
    get_episode_or_404(db, episode_id, context)
    return active_plan_for_episode(db, episode_id)


@router.post("/episodes/{episode_id}/clinical-plans/generate", response_model=ClinicalPlanOut)
def generate_clinical_plan(
    episode_id: int,
    payload: ClinicalPlanGenerate,
    request: Request,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("clinical_plans.write")),
):
    actor = context.actor
    episode = get_episode_or_404(db, episode_id, context)
    if payload.appointment_id:
        appointment = db.scalar(
            select(Appointment)
            .join(Clinic, Clinic.id == Appointment.clinic_id)
            .where(
                Appointment.id == payload.appointment_id,
                Appointment.episode_id == episode.id,
                Clinic.institution_id == episode.institution_id,
            )
        )
        if not appointment:
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
    context: CurrentUserContext = Depends(require_active_clinic("clinical_plans.write")),
):
    actor = context.actor
    plan = get_plan_or_404(db, plan_id, context)
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
    context: CurrentUserContext = Depends(require_active_clinic("clinical_plans.write")),
):
    actor = context.actor
    plan = get_plan_or_404(db, plan_id, context)
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
    context: CurrentUserContext = Depends(require_active_clinic("clinical_plans.write")),
):
    actor = context.actor
    plan = get_plan_or_404(db, plan_id, context)
    if plan.physician_confirmed and plan.status == "active":
        return plan
    if plan.physician_confirmed:
        raise HTTPException(422, detail="Arhivirani potvrdeni plan se ne moze ponovno potvrditi")
    if plan.status == "cancelled":
        raise HTTPException(422, detail="Odbijeni plan se ne moze potvrditi")
    if plan.status not in {"draft", "waiting"}:
        raise HTTPException(422, detail="Samo prijedlog plana koji ceka odluku moze biti potvrden")
    episode = get_episode_or_404(db, plan.episode_id, context)
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
def episode_clinical_timeline(episode_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_plans.read"))):
    get_episode_or_404(db, episode_id, context)
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


