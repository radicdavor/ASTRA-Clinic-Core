from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import CurrentUserContext, get_scoped_patient, require_active_clinic, require_medical_staff
from app.core.database import get_db
from app.models.domain import Therapy
from app.schemas.therapies import TherapyComplete, TherapyCreate, TherapyOut, TherapyRenew, TherapyStop, TherapyUpdate
from app.services.clinical_scope import authorized_institution_id, get_institution_episode

router = APIRouter(prefix="/api/therapies", tags=["therapies"], dependencies=[Depends(require_medical_staff)])


def therapy_query(institution_id: int):
    return select(Therapy).options(joinedload(Therapy.patient)).where(Therapy.institution_id == institution_id)


def get_therapy(db: Session, therapy_id: int, institution_id: int) -> Therapy:
    item = db.scalar(therapy_query(institution_id).where(Therapy.id == therapy_id))
    if not item:
        raise HTTPException(404, detail="Terapija nije pronadena")
    return item


def audit_scope(context: CurrentUserContext, institution_id: int) -> dict:
    return {"scope_type": "clinic", "clinic_id": context.active_clinic_id, "institution_id": institution_id}


@router.get("", response_model=list[TherapyOut])
def list_therapies(
    patient_id: int | None = None,
    episode_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.read")),
):
    stmt = therapy_query(authorized_institution_id(context)).order_by(Therapy.start_date.desc(), Therapy.id.desc())
    if patient_id:
        stmt = stmt.where(Therapy.patient_id == patient_id)
    if episode_id:
        stmt = stmt.where(Therapy.episode_id == episode_id)
    if status:
        stmt = stmt.where(Therapy.status == status)
    return db.scalars(stmt).unique().all()


@router.post("", response_model=TherapyOut)
def create_therapy(
    payload: TherapyCreate,
    request: Request,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.write")),
):
    get_scoped_patient(db, payload.patient_id, context)
    institution_id = authorized_institution_id(context)
    if payload.episode_id:
        episode = get_institution_episode(db, payload.episode_id, context)
        if episode.patient_id != payload.patient_id:
            raise HTTPException(422, detail="Epizoda ne pripada pacijentu")
    actor = context.actor
    item = Therapy(**payload.model_dump(), institution_id=institution_id, status="active", created_by=actor.user_id)
    db.add(item)
    db.flush()
    audit(db, "create", "Therapy", item.id, "Evidentirana terapija", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(item), request, **audit_scope(context, institution_id))
    db.commit()
    return get_therapy(db, item.id, institution_id)


@router.put("/{therapy_id}", response_model=TherapyOut)
def update_therapy(
    therapy_id: int,
    payload: TherapyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.write")),
):
    institution_id = authorized_institution_id(context)
    item = get_therapy(db, therapy_id, institution_id)
    if item.status != "active":
        raise HTTPException(409, detail="Samo aktivna terapija moze se mijenjati")
    if payload.episode_id:
        episode = get_institution_episode(db, payload.episode_id, context)
        if episode.patient_id != item.patient_id:
            raise HTTPException(422, detail="Epizoda ne pripada pacijentu")
    if payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(422, detail="Datum zavrsetka ne moze biti prije pocetka")
    before = snapshot(item)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    item.status = "completed" if item.end_date and item.end_date < datetime.now(timezone.utc).date() else "active"
    db.flush()
    actor = context.actor
    audit(db, "update", "Therapy", item.id, "Azurirana terapija", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request, **audit_scope(context, institution_id))
    db.commit()
    return get_therapy(db, item.id, institution_id)


@router.post("/{therapy_id}/stop", response_model=TherapyOut)
def stop_therapy(therapy_id: int, payload: TherapyStop, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.write"))):
    institution_id = authorized_institution_id(context)
    item = get_therapy(db, therapy_id, institution_id)
    if item.status == "stopped":
        raise HTTPException(409, detail="Terapija je vec prekinuta")
    before = snapshot(item)
    item.status = "stopped"
    item.end_date = datetime.now(timezone.utc).date()
    item.stopped_at = datetime.now(timezone.utc)
    item.stopped_by = context.actor.user_id
    item.stop_reason = payload.reason
    db.flush()
    actor = context.actor
    audit(db, "stop", "Therapy", item.id, "Prekinuta terapija", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request, **audit_scope(context, institution_id))
    db.commit()
    return get_therapy(db, item.id, institution_id)


@router.post("/{therapy_id}/complete", response_model=TherapyOut)
def complete_therapy(therapy_id: int, payload: TherapyComplete, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.write"))):
    institution_id = authorized_institution_id(context)
    item = get_therapy(db, therapy_id, institution_id)
    if item.status != "active":
        raise HTTPException(409, detail="Samo aktivna terapija moze se zavrsiti")
    before = snapshot(item)
    now = datetime.now(timezone.utc)
    item.status = "completed"
    item.end_date = now.date()
    item.completed_at = now
    item.completed_by = context.actor.user_id
    item.completion_note = payload.note
    db.flush()
    actor = context.actor
    audit(db, "complete", "Therapy", item.id, "Zavrsena terapija", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request, **audit_scope(context, institution_id))
    db.commit()
    return get_therapy(db, item.id, institution_id)


@router.post("/{therapy_id}/renew", response_model=TherapyOut)
def renew_therapy(therapy_id: int, payload: TherapyRenew, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.write"))):
    institution_id = authorized_institution_id(context)
    source = get_therapy(db, therapy_id, institution_id)
    if source.status == "active":
        raise HTTPException(409, detail="Aktivnu terapiju nije potrebno obnoviti")
    if payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(422, detail="Datum zavrsetka ne moze biti prije pocetka")
    actor = context.actor
    item = Therapy(
        patient_id=source.patient_id,
        institution_id=institution_id,
        episode_id=source.episode_id,
        parent_therapy_id=source.id,
        name=source.name,
        instructions=payload.instructions or source.instructions,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="active",
        prescriber=source.prescriber,
        notes=source.notes,
        created_by=actor.user_id,
    )
    db.add(item)
    db.flush()
    audit(db, "renew", "Therapy", item.id, "Obnovljena terapija", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(item), request, **audit_scope(context, institution_id))
    db.commit()
    return get_therapy(db, item.id, institution_id)
