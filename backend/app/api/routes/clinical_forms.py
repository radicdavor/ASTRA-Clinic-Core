from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import ClinicalFormDefinition, ClinicalFormInstance, JourneyActivity, PatientJourney
from app.schemas.clinical_forms import ClinicalFormDataUpdate, ClinicalFormDefinitionOut, ClinicalFormInstanceOut
from app.services.clinical_forms import amend_instance, complete_instance, resolve_instance, sign_instance, update_instance
from app.services.journey_activities import get_activity
from app.services.patient_journeys import add_event


router = APIRouter(prefix="/api", tags=["clinical-forms"])


def journey(db: Session, journey_id: int) -> PatientJourney:
    item = db.get(PatientJourney, journey_id)
    if not item:
        raise HTTPException(404, detail="Tijek pacijenta nije pronađen")
    return item


def instance(db: Session, journey_id: int, activity_id: int, instance_id: int | None = None) -> ClinicalFormInstance:
    get_activity(db, journey_id, activity_id)
    stmt = (
        select(ClinicalFormInstance)
        .options(joinedload(ClinicalFormInstance.form_version))
        .where(ClinicalFormInstance.activity_id == activity_id)
    )
    if instance_id is not None:
        stmt = stmt.where(ClinicalFormInstance.id == instance_id)
    else:
        stmt = stmt.where(ClinicalFormInstance.status.notin_({"amended", "void"})).order_by(ClinicalFormInstance.id.desc()).limit(1)
    item = db.scalar(stmt)
    if not item:
        raise HTTPException(404, detail="Klinički obrazac aktivnosti nije pronađen")
    return item


@router.get("/clinical-forms/definitions", response_model=list[ClinicalFormDefinitionOut])
def definitions(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_forms.read"))):
    return db.scalars(select(ClinicalFormDefinition).where(ClinicalFormDefinition.active.is_(True)).order_by(ClinicalFormDefinition.name)).all()


@router.post("/patient-journeys/{journey_id}/activities/{activity_id}/form/resolve", response_model=ClinicalFormInstanceOut)
def resolve_activity_form(journey_id: int, activity_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("encounter.write"))):
    visit = journey(db, journey_id)
    activity = get_activity(db, journey_id, activity_id)
    item = resolve_instance(db, activity, actor.user_id)
    audit(db, "form_binding_resolved", "ClinicalFormInstance", item.id, f"Obrazac razriješen putem {item.binding_source}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(item), request)
    add_event(db, visit, "form_binding_resolved", "Razriješen klinički obrazac aktivnosti", actor, request, visit.current_stage, visit.current_stage, {"activity_id": activity.id, "form_instance_id": item.id, "binding_source": item.binding_source})
    db.commit()
    return instance(db, journey_id, activity_id, item.id)


@router.get("/patient-journeys/{journey_id}/activities/{activity_id}/form", response_model=ClinicalFormInstanceOut)
def activity_form(journey_id: int, activity_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("encounter.read"))):
    return instance(db, journey_id, activity_id)


@router.patch("/patient-journeys/{journey_id}/activities/{activity_id}/form", response_model=ClinicalFormInstanceOut)
def edit_activity_form(journey_id: int, activity_id: int, payload: ClinicalFormDataUpdate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("encounter.write"))):
    item = instance(db, journey_id, activity_id)
    before = snapshot(item)
    update_instance(db, item, payload.data, actor.user_id)
    audit(db, "form_edited", "ClinicalFormInstance", item.id, "Klinički obrazac je izmijenjen", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request)
    db.commit()
    return instance(db, journey_id, activity_id, item.id)


@router.post("/patient-journeys/{journey_id}/activities/{activity_id}/form/complete", response_model=ClinicalFormInstanceOut)
def complete_activity_form(journey_id: int, activity_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("encounter.complete"))):
    item = instance(db, journey_id, activity_id)
    complete_instance(db, item, actor.user_id)
    audit(db, "form_completed", "ClinicalFormInstance", item.id, "Klinički obrazac je dovršen", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(item), request)
    db.commit()
    return instance(db, journey_id, activity_id, item.id)


@router.post("/patient-journeys/{journey_id}/activities/{activity_id}/form/sign", response_model=ClinicalFormInstanceOut)
def sign_activity_form(journey_id: int, activity_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_forms.sign"))):
    item = instance(db, journey_id, activity_id)
    sign_instance(db, item, actor.user_id)
    audit(db, "form_signed", "ClinicalFormInstance", item.id, "Klinički obrazac je potpisan", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(item), request)
    db.commit()
    return instance(db, journey_id, activity_id, item.id)


@router.post("/patient-journeys/{journey_id}/activities/{activity_id}/form/amend", response_model=ClinicalFormInstanceOut)
def amend_activity_form(journey_id: int, activity_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_forms.sign"))):
    old = instance(db, journey_id, activity_id)
    amended = amend_instance(db, old, actor.user_id)
    audit(db, "form_amended", "ClinicalFormInstance", old.id, "Otvoren je kontrolirani ispravak potpisanog obrasca", actor.user_id, actor.actor_type, actor.api_key_id, snapshot(old), {"amendment_instance_id": amended.id}, request)
    db.commit()
    return instance(db, journey_id, activity_id, amended.id)
