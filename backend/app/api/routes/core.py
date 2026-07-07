from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, AuditLog, Clinic, ClinicalDocument, ClinicalEpisode, ClinicalPlan, Invoice, Module, Patient, PatientClinicalSummaryRecord, Provider, Room, Service
from app.schemas.common import AppointmentCreate, AppointmentOut, AppointmentUpdate, ClinicOut, ClinicalDecisionTimelineItem, ClinicalDocumentCreate, ClinicalDocumentOut, ClinicalDocumentUpdate, ClinicalDocumentUpload, ClinicalEpisodeCreate, ClinicalEpisodeOut, ClinicalEpisodeUpdate, ClinicalEvidenceTimelineItem, ClinicalPlanGenerate, ClinicalPlanOut, ClinicalPlanUpdate, ErrorResponse, InvoiceOut, PatientClinicalSummary, PatientClinicalSummaryRecordOut, PatientClinicalSummaryRecordUpdate, PatientCreate, PatientOut, PatientUpdate, ReceptionArrivalRequest, ReceptionSlot, ServiceCreate, ServiceOut
from app.services.appointments import validate_appointment_payload
from app.services.clinical_evidence_timeline import classify_audit_log
from app.services.clinical_documents import extract_document_knowledge, get_document_or_404, initial_ai_extraction_status, initial_document_review_status, mark_document_ai_extraction_edited, mark_document_needs_review, validate_document_links
from app.services.patient_knowledge import GENERIC_OPEN_QUESTION_TEXT, add_knowledge_item, contains_unresolved_language, is_document_awaiting_physician_review, is_official_clinical_document, latest_patient_summary_record, latest_reviewed_document_updated_at, official_patient_documents_statement, summary_record_from_documents, summary_record_is_stale

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


def validate_episode_for_patient(db: Session, episode_id: int | None, patient_id: int) -> ClinicalEpisode | None:
    if episode_id is None:
        return None
    episode = db.get(ClinicalEpisode, episode_id)
    if not episode:
        raise HTTPException(404, detail="Klinička epizoda nije pronađena")
    if episode.patient_id != patient_id:
        raise HTTPException(422, detail="Klinička epizoda mora pripadati istom pacijentu kao termin")
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


@router.get("/clinical-documents", response_model=list[ClinicalDocumentOut])
def list_clinical_documents(
    patient_id: int | None = None,
    document_type: str | None = None,
    source_type: str | None = None,
    physician_reviewed: bool | None = None,
    review_status: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.read")),
):
    stmt = select(ClinicalDocument).options(joinedload(ClinicalDocument.patient)).order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())
    if patient_id:
        stmt = stmt.where(ClinicalDocument.patient_id == patient_id)
    if document_type:
        stmt = stmt.where(ClinicalDocument.document_type == document_type)
    if source_type:
        stmt = stmt.where(ClinicalDocument.source_type == source_type)
    if physician_reviewed is not None:
        stmt = stmt.where(ClinicalDocument.physician_reviewed.is_(physician_reviewed))
    if review_status:
        stmt = stmt.where(ClinicalDocument.review_status == review_status)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(ClinicalDocument.title.ilike(like), ClinicalDocument.origin.ilike(like), ClinicalDocument.institution.ilike(like), ClinicalDocument.raw_text.ilike(like), ClinicalDocument.ai_summary.ilike(like)))
    return db.scalars(stmt).all()


@router.post("/clinical-documents", response_model=ClinicalDocumentOut)
def create_clinical_document(
    payload: ClinicalDocumentCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    validate_document_links(db, payload.patient_id, payload.appointment_id)
    values = payload.model_dump()
    now = datetime.now(timezone.utc)
    initial_ai_status = initial_ai_extraction_status(values)
    document = ClinicalDocument(
        **values,
        review_status=initial_document_review_status(values),
        ai_extraction_status=initial_ai_status,
        ai_extraction_generated_at=now if initial_ai_status != "not_run" else None,
        ai_extraction_updated_at=now if initial_ai_status != "not_run" else None,
        physician_reviewed=False,
    )
    db.add(document)
    db.flush()
    audit(db, "create", "ClinicalDocument", document.id, f"Dodan klinicki dokument: {document.title}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.post("/patients/{patient_id}/clinical-documents", response_model=ClinicalDocumentOut)
def create_patient_clinical_document(
    patient_id: int,
    payload: ClinicalDocumentCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    if payload.patient_id != patient_id:
        raise HTTPException(422, detail="Dokument mora pripadati pacijentu iz rute")
    return create_clinical_document(payload, request, db, actor)


@router.post("/clinical-documents/upload", response_model=ClinicalDocumentOut)
def upload_clinical_document(
    payload: ClinicalDocumentUpload,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    validate_document_links(db, payload.patient_id, payload.appointment_id)
    attachment_path = f"local-placeholder/{payload.attachment_name}" if payload.attachment_name else None
    document = ClinicalDocument(
        patient_id=payload.patient_id,
        title=payload.title,
        source_type=payload.source_type,
        document_type=payload.document_type,
        origin=payload.origin,
        document_date=payload.document_date,
        author=payload.author,
        institution=payload.institution,
        raw_text=payload.raw_text,
        attachment_path=attachment_path,
        appointment_id=payload.appointment_id,
        review_status="draft",
        ai_extraction_status="not_run",
        physician_reviewed=False,
    )
    db.add(document)
    db.flush()
    audit(db, "upload", "ClinicalDocument", document.id, f"Upload placeholder dokumenta: {document.title}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.get("/clinical-documents/search", response_model=list[ClinicalDocumentOut])
def search_clinical_documents(q: str, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_documents.read"))):
    like = f"%{q}%"
    return db.scalars(
        select(ClinicalDocument)
        .options(joinedload(ClinicalDocument.patient))
        .where(or_(ClinicalDocument.title.ilike(like), ClinicalDocument.origin.ilike(like), ClinicalDocument.institution.ilike(like), ClinicalDocument.raw_text.ilike(like), ClinicalDocument.ai_summary.ilike(like)))
        .order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())
        .limit(50)
    ).all()


@router.get("/clinical-documents/{document_id}", response_model=ClinicalDocumentOut)
def get_clinical_document(document_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_documents.read"))):
    return get_document_or_404(db, document_id)


@router.get("/clinical-documents/{document_id}/evidence-timeline", response_model=list[ClinicalEvidenceTimelineItem])
def clinical_document_evidence_timeline(document_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_documents.read"))):
    get_document_or_404(db, document_id)
    logs = db.scalars(select(AuditLog).where(AuditLog.entity_type == "ClinicalDocument", AuditLog.entity_id == document_id).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())).all()
    items: list[ClinicalEvidenceTimelineItem] = []
    for log in logs:
        classification = classify_audit_log(log)
        items.append(
            ClinicalEvidenceTimelineItem(
                id=log.id,
                action=log.action,
                object_type=log.entity_type,
                object_id=log.entity_id,
                message=log.summary,
                actor_type=log.actor_type,
                actor_user_id=log.actor_user_id,
                actor_api_key_id=log.actor_api_key_id,
                created_at=log.created_at,
                clinical_event_category=classification.clinical_event_category,
                clinical_event_label=classification.clinical_event_label,
                knowledge_impact=classification.knowledge_impact,
                is_clinical_evidence_event=classification.is_clinical_evidence_event,
            )
        )
    return items


@router.patch("/clinical-documents/{document_id}", response_model=ClinicalDocumentOut)
def update_clinical_document(
    document_id: int,
    payload: ClinicalDocumentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.review")),
):
    document = get_document_or_404(db, document_id)
    update_data = payload.model_dump(exclude_unset=True)
    validate_document_links(db, update_data.get("patient_id", document.patient_id), update_data.get("appointment_id", document.appointment_id))
    before = snapshot(document)
    patch_model(document, update_data)
    review_reset_fields = {"raw_text", "ai_summary", "key_findings", "recommendations"}
    if review_reset_fields.intersection(update_data):
        now = datetime.now(timezone.utc)
        extraction_fields = {"ai_summary", "key_findings", "recommendations"}
        if extraction_fields.intersection(update_data) or "raw_text" in update_data:
            mark_document_ai_extraction_edited(document, now)
        mark_document_needs_review(document)
    db.flush()
    extraction_fields = {"ai_summary", "key_findings", "recommendations"}
    action = "ai_document_extraction_edited" if extraction_fields.intersection(update_data) else "update"
    summary = "Uredjen AI prijedlog prije lijecnicke potvrde" if action == "ai_document_extraction_edited" else f"Azuriran klinicki dokument: {document.title}"
    audit(db, action, "ClinicalDocument", document.id, summary, actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.post("/clinical-documents/{document_id}/extract", response_model=ClinicalDocumentOut)
def extract_clinical_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.review")),
):
    document = get_document_or_404(db, document_id)
    before = snapshot(document)
    now = datetime.now(timezone.utc)
    patch_model(document, extract_document_knowledge(document))
    document.ai_extraction_status = "generated"
    document.ai_extraction_generated_at = now
    document.ai_extraction_updated_at = now
    document.review_status = "needs_physician_review"
    document.physician_reviewed = False
    document.reviewed_by = None
    document.reviewed_at = None
    db.flush()
    audit(db, "ai_document_extracted", "ClinicalDocument", document.id, "AI placeholder je predlozio strukturirani sazetak dokumenta", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.post("/clinical-documents/{document_id}/review", response_model=ClinicalDocumentOut)
def review_clinical_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    document = get_document_or_404(db, document_id)
    before = snapshot(document)
    now = datetime.now(timezone.utc)
    document.review_status = "reviewed"
    if has_extracted_content(document):
        document.ai_extraction_status = "accepted"
        document.ai_extraction_updated_at = now
    document.physician_reviewed = True
    document.reviewed_by = actor.user_id
    document.reviewed_at = now
    db.flush()
    audit(db, "clinical_document_reviewed", "ClinicalDocument", document.id, "Lijecnik je pregledao klinicki dokument", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.post("/clinical-documents/{document_id}/reject-summary", response_model=ClinicalDocumentOut)
def reject_clinical_document_summary(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    document = get_document_or_404(db, document_id)
    before = snapshot(document)
    document.ai_summary = None
    document.key_findings = []
    document.recommendations = []
    document.ai_extraction_status = "rejected"
    document.ai_extraction_updated_at = datetime.now(timezone.utc)
    document.review_status = "draft"
    document.physician_reviewed = False
    document.reviewed_by = None
    document.reviewed_at = None
    db.flush()
    audit(db, "ai_document_summary_rejected", "ClinicalDocument", document.id, "Lijecnik je odbio AI sazetak dokumenta", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.get("/patients/{patient_id}/clinical-documents", response_model=list[ClinicalDocumentOut])
def patient_clinical_documents(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_documents.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    return db.scalars(select(ClinicalDocument).options(joinedload(ClinicalDocument.patient)).where(ClinicalDocument.patient_id == patient_id).order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())).all()


@router.get("/patients/{patient_id}/clinical-summary", response_model=PatientClinicalSummary)
def patient_clinical_summary(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_documents.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    documents = db.scalars(select(ClinicalDocument).where(ClinicalDocument.patient_id == patient_id).order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())).all()
    reviewed = [document for document in documents if is_official_clinical_document(document)]
    awaiting_review_count = len([document for document in documents if is_document_awaiting_physician_review(document)])
    reviewed_summary = latest_patient_summary_record(db, patient_id, ["reviewed"])
    draft_summary = latest_patient_summary_record(db, patient_id, ["draft_ai", "needs_review", "stale"])
    latest_document_updated_at = latest_reviewed_document_updated_at(reviewed)
    reviewed_summary_is_stale = summary_record_is_stale(reviewed_summary, latest_document_updated_at)
    draft_summary_is_stale = summary_record_is_stale(draft_summary, latest_document_updated_at)
    summary_warning = None
    if reviewed_summary_is_stale:
        summary_warning = "Pregledani sazetak je zastario jer postoje noviji pregledani dokumenti."
    elif draft_summary_is_stale:
        summary_warning = "AI draft sazetka je zastario jer postoje noviji pregledani dokumenti."
    summary = PatientClinicalSummary(
        patient_id=patient_id,
        generated_from_reviewed_documents=len(reviewed),
        awaiting_review_count=awaiting_review_count,
        reviewed_summary=reviewed_summary,
        draft_summary=draft_summary,
        reviewed_summary_is_stale=reviewed_summary_is_stale,
        draft_summary_is_stale=draft_summary_is_stale,
        latest_reviewed_document_updated_at=latest_document_updated_at,
        reviewed_summary_updated_at=reviewed_summary.updated_at if reviewed_summary else None,
        summary_warning=summary_warning,
        known_problems=[],
        completed_procedures=[],
        pathology=[],
        laboratory=[],
        imaging=[],
        current_therapy=[],
        open_questions=[],
        latest_recommendations=[],
    )
    for document in reviewed:
        source_text_blob = " ".join([document.raw_text or "", document.ai_summary or "", " ".join(document.key_findings or [])]).lower()
        for finding in document.key_findings or []:
            lower = finding.lower()
            if document.document_type in {"gastroscopy", "colonoscopy"} or "gastroskop" in lower or "kolonoskop" in lower:
                add_knowledge_item(summary.completed_procedures, finding, document)
            elif document.document_type == "pathology" or "patolog" in lower or "biops" in lower:
                add_knowledge_item(summary.pathology, finding, document)
            elif document.document_type == "laboratory":
                add_knowledge_item(summary.laboratory, finding, document)
            elif document.document_type == "radiology":
                add_knowledge_item(summary.imaging, finding, document)
            elif "terap" in lower or "esomeprazol" in lower or "pantoprazol" in lower:
                add_knowledge_item(summary.current_therapy, finding, document)
            else:
                add_knowledge_item(summary.known_problems, finding, document)
        for recommendation in document.recommendations or []:
            if contains_unresolved_language(recommendation):
                add_knowledge_item(summary.open_questions, recommendation, document, display_kind="open_question", severity="warning", requires_attention=True)
            else:
                add_knowledge_item(summary.latest_recommendations, recommendation, document)
        if document.document_type in {"pathology", "laboratory", "radiology"} and not document.key_findings:
            target = summary.pathology if document.document_type == "pathology" else summary.laboratory if document.document_type == "laboratory" else summary.imaging
            add_knowledge_item(target, document.ai_summary or document.title, document)
        if contains_unresolved_language(source_text_blob):
            add_knowledge_item(summary.open_questions, GENERIC_OPEN_QUESTION_TEXT, document, display_kind="open_question", severity="warning", requires_attention=True)
    return summary


@router.post("/patients/{patient_id}/clinical-summary/generate-draft", response_model=PatientClinicalSummaryRecordOut)
def generate_patient_clinical_summary_draft(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    reviewed = db.scalars(official_patient_documents_statement(patient_id).order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())).all()
    values = summary_record_from_documents(patient_id, reviewed)
    record = PatientClinicalSummaryRecord(**values)
    db.add(record)
    db.flush()
    audit(db, "patient_summary_draft_generated", "PatientClinicalSummary", record.id, "AI placeholder je generirao draft sazetka pacijenta", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(record), request)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/patients/{patient_id}/clinical-summary", response_model=PatientClinicalSummaryRecordOut)
def update_patient_clinical_summary_record(
    patient_id: int,
    payload: PatientClinicalSummaryRecordUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    record = latest_patient_summary_record(db, patient_id, ["draft_ai", "needs_review", "stale", "reviewed"])
    if record is None:
        record = PatientClinicalSummaryRecord(patient_id=patient_id, status="needs_review", generated_by="physician")
        db.add(record)
        db.flush()
    before = snapshot(record)
    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("status") == "reviewed":
        update_data["status"] = "needs_review"
    patch_model(record, update_data)
    edited_fields = {"summary_text", "known_conditions", "key_findings", "open_items", "risks", "last_recommendations", "source_document_ids"}
    if edited_fields.intersection(update_data):
        record.status = "needs_review"
    if record.status == "reviewed":
        record.status = "needs_review"
        record.reviewed_by = None
        record.reviewed_at = None
    db.flush()
    audit(db, "patient_summary_edited", "PatientClinicalSummary", record.id, "Uredjen klinicki sazetak pacijenta prije potvrde", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(record), request)
    db.commit()
    db.refresh(record)
    return record


@router.post("/patients/{patient_id}/clinical-summary/review", response_model=PatientClinicalSummaryRecordOut)
def review_patient_clinical_summary_record(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.review")),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    record = latest_patient_summary_record(db, patient_id, ["draft_ai", "needs_review", "stale"])
    if record is None:
        raise HTTPException(404, detail="Nema draft sazetka za potvrdu")
    reviewed_documents = db.scalars(official_patient_documents_statement(patient_id)).all()
    latest_document_updated_at = latest_reviewed_document_updated_at(reviewed_documents)
    if summary_record_is_stale(record, latest_document_updated_at):
        raise HTTPException(409, detail="Sazetak je zastario jer postoje noviji pregledani dokumenti. Generirajte novi draft prije potvrde.")
    before = snapshot(record)
    record.status = "reviewed"
    record.reviewed_by = actor.user_id
    record.reviewed_at = datetime.now(timezone.utc)
    db.flush()
    audit(db, "patient_summary_reviewed", "PatientClinicalSummary", record.id, "Lijecnik je potvrdio klinicki sazetak pacijenta", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(record), request)
    db.commit()
    db.refresh(record)
    return record


@router.post("/patients", response_model=PatientOut)
def create_patient(
    payload: PatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("patients.write")),
):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    flush_or_conflict(db)
    audit(db, "create", "Patient", patient.id, f"{patient.first_name} {patient.last_name}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(patient), request)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient


@router.get("/patients", response_model=list[PatientOut])
def list_patients(q: str | None = None, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("patients.read"))):
    stmt = select(Patient).order_by(Patient.last_name, Patient.first_name)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Patient.phone.ilike(like), Patient.email.ilike(like), Patient.oib.ilike(like)))
    return db.scalars(stmt).all()


@router.get("/patients/possible-duplicates", response_model=list[PatientOut])
def possible_patient_duplicates(
    first_name: str | None = None,
    last_name: str | None = None,
    date_of_birth: date | None = None,
    phone: str | None = None,
    email: str | None = None,
    oib: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("patients.read")),
):
    conditions = []
    if oib:
        conditions.append(Patient.oib == oib.strip())
    if first_name and last_name:
        name_match = [Patient.first_name.ilike(first_name.strip()), Patient.last_name.ilike(last_name.strip())]
        if date_of_birth:
            conditions.append(and_(*name_match, Patient.date_of_birth == date_of_birth))
        if phone:
            conditions.append(and_(*name_match, Patient.phone == phone.strip()))
        if email:
            conditions.append(and_(*name_match, Patient.email == email.strip()))
        if not date_of_birth and not phone and not email:
            conditions.append(and_(*name_match))
    if not conditions:
        return []
    stmt = select(Patient).where(or_(*conditions)).order_by(Patient.last_name, Patient.first_name).limit(10)
    return db.scalars(stmt).all()


@router.get("/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("patients.read"))):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, detail="Pacijent nije pronađen")
    return patient


@router.get("/patients/{patient_id}/appointments", response_model=list[AppointmentOut])
def patient_appointments(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    return db.scalars(
        select(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room))
        .where(Appointment.patient_id == patient_id)
        .order_by(Appointment.date.desc(), Appointment.start_time.desc())
    ).all()


@router.get("/patients/{patient_id}/episodes", response_model=list[ClinicalEpisodeOut])
def patient_episodes(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("episodes.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    stmt = (
        select(ClinicalEpisode)
        .options(joinedload(ClinicalEpisode.patient), joinedload(ClinicalEpisode.owner_provider))
        .where(ClinicalEpisode.patient_id == patient_id)
        .order_by(ClinicalEpisode.status, ClinicalEpisode.start_date.desc())
    )
    return [episode_with_count(db, episode) for episode in db.scalars(stmt).all()]


@router.get("/patients/{patient_id}/invoices", response_model=list[InvoiceOut])
def patient_invoices(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    return db.scalars(select(Invoice).where(Invoice.patient_id == patient_id).order_by(Invoice.invoice_date.desc(), Invoice.id.desc())).all()


@router.patch("/patients/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("patients.write")),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, detail="Pacijent nije pronađen")
    before = snapshot(patient)
    patch_model(patient, payload.model_dump(exclude_unset=True))
    flush_or_conflict(db)
    audit(db, "update", "Patient", patient.id, "Ažuriran pacijent", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(patient), request)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient


@router.post("/appointments", response_model=AppointmentOut)
def create_appointment(
    payload: AppointmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    data = payload.model_dump()
    validate_episode_for_patient(db, data.get("episode_id"), payload.patient_id)
    data["duration_minutes"] = validate_appointment_payload(db, payload.date, payload.start_time, payload.end_time, payload.provider_id, payload.room_id, payload.status, payload.source, service_id=payload.service_id)
    appointment = Appointment(**data, created_by=actor.user_id)
    db.add(appointment)
    db.flush()
    audit(db, "create", "Appointment", appointment.id, f"Termin {appointment.date}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(appointment), request)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(
    date_from: date | None = None,
    date_to: date | None = None,
    patient: str | None = None,
    service: str | None = None,
    provider_id: int | None = None,
    room_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.read")),
):
    stmt = select(Appointment).options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room), joinedload(Appointment.episode).joinedload(ClinicalEpisode.patient), joinedload(Appointment.episode).joinedload(ClinicalEpisode.owner_provider)).order_by(Appointment.date, Appointment.start_time)
    if date_from:
        stmt = stmt.where(Appointment.date >= date_from)
    if date_to:
        stmt = stmt.where(Appointment.date <= date_to)
    if provider_id:
        stmt = stmt.where(Appointment.provider_id == provider_id)
    if room_id:
        stmt = stmt.where(Appointment.room_id == room_id)
    if status:
        stmt = stmt.where(Appointment.status == status)
    if patient:
        stmt = stmt.join(Appointment.patient).where(or_(Patient.first_name.ilike(f"%{patient}%"), Patient.last_name.ilike(f"%{patient}%")))
    if service:
        stmt = stmt.join(Appointment.service).where(Service.name.ilike(f"%{service}%"))
    return db.scalars(stmt).all()


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    appointment = db.scalar(select(Appointment).options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room), joinedload(Appointment.episode).joinedload(ClinicalEpisode.patient), joinedload(Appointment.episode).joinedload(ClinicalEpisode.owner_provider)).where(Appointment.id == appointment_id))
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    return appointment


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    before = snapshot(appointment)
    update_data = payload.model_dump(exclude_unset=True)
    next_patient_id = update_data.get("patient_id", appointment.patient_id)
    if "episode_id" in update_data:
        validate_episode_for_patient(db, update_data.get("episode_id"), next_patient_id)
    old_episode_id = appointment.episode_id
    patch_model(appointment, update_data)
    appointment.duration_minutes = validate_appointment_payload(db, appointment.date, appointment.start_time, appointment.end_time, appointment.provider_id, appointment.room_id, appointment.status, appointment.source, service_id=appointment.service_id, appointment_id=appointment.id)
    db.flush()
    audit(db, "update", "Appointment", appointment.id, "Ažuriran termin", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(appointment), request)
    if "episode_id" in update_data and old_episode_id != appointment.episode_id:
        action = "link_episode" if appointment.episode_id else "unlink_episode"
        summary = f"Termin povezan s epizodom #{appointment.episode_id}" if appointment.episode_id else "Termin odvojen od kliničke epizode"
        audit(db, action, "Appointment", appointment.id, summary, actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(appointment), request)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.delete("/appointments/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    before = snapshot(appointment)
    db.delete(appointment)
    audit(db, "delete", "Appointment", appointment_id, "Obrisan termin", actor.user_id, actor.actor_type, actor.api_key_id, before, None, request)
    db.commit()
    return {"ok": True}


@router.get("/schedule/day", response_model=list[AppointmentOut])
def day_schedule(date: date = Query(...), db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(
        select(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room), joinedload(Appointment.episode).joinedload(ClinicalEpisode.patient), joinedload(Appointment.episode).joinedload(ClinicalEpisode.owner_provider))
        .where(Appointment.date == date)
        .order_by(Appointment.start_time)
    ).all()


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
    return get_appointment(appointment.id, db, actor)


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
