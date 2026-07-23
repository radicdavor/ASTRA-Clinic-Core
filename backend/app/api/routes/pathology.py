from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.audit.service import audit, snapshot
from app.auth.dependencies import CurrentUserContext, require_active_clinic, require_medical_staff
from app.core.database import get_db
from app.models.domain import PathologyCase, PatientJourney, ProcedureIntervention
from app.schemas.pathology import InterventionCreate, InterventionOut, PathologyCaseCreate, PathologyCaseOut, PathologyCommunicationDecision, PathologyStatusUpdate, ReportLinkCreate
from app.services.journey_activities import get_activity
from app.services.pathology import create_case, decide_communication, link_result, review_result, transition_case
from app.services.patient_journeys import add_event


router = APIRouter(prefix="/api", tags=["pathology"], dependencies=[Depends(require_medical_staff)])


def visit(db: Session, journey_id: int, clinic_id: int) -> PatientJourney:
    item = db.scalar(select(PatientJourney).where(PatientJourney.id == journey_id, PatientJourney.clinic_id == clinic_id))
    if not item:
        raise HTTPException(404, detail="Tijek pacijenta nije pronađen")
    return item


def pathology_case(db: Session, case_id: int, clinic_id: int) -> PathologyCase:
    item = db.scalar(select(PathologyCase).options(selectinload(PathologyCase.specimens)).join(PatientJourney, PatientJourney.id == PathologyCase.journey_id).where(PathologyCase.id == case_id, PatientJourney.clinic_id == clinic_id))
    if not item:
        raise HTTPException(404, detail="Patološki slučaj nije pronađen")
    return item


@router.get("/patient-journeys/{journey_id}/activities/{activity_id}/interventions", response_model=list[InterventionOut])
def interventions(journey_id: int, activity_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("procedure_interventions.read"))):
    visit(db, journey_id, context.active_clinic_id)
    get_activity(db, journey_id, activity_id)
    return db.scalars(select(ProcedureIntervention).where(ProcedureIntervention.activity_id == activity_id).order_by(ProcedureIntervention.id)).all()


@router.post("/patient-journeys/{journey_id}/activities/{activity_id}/interventions", response_model=InterventionOut, status_code=201)
def add_intervention(journey_id: int, activity_id: int, payload: InterventionCreate, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("procedure_interventions.write"))):
    actor = context.actor; journey = visit(db, journey_id, context.active_clinic_id); activity = get_activity(db, journey_id, activity_id)
    item = ProcedureIntervention(activity_id=activity.id, created_by=actor.user_id, **payload.model_dump())
    db.add(item); db.flush()
    audit(db, "intervention_created", "ProcedureIntervention", item.id, f"Evidentirana intervencija: {item.intervention_type}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(item), request)
    add_event(db, journey, "intervention_created", f"Evidentirana intervencija: {item.intervention_type}", actor, request, journey.current_stage, journey.current_stage, {"activity_id": activity.id, "intervention_id": item.id})
    db.commit(); db.refresh(item); return item


@router.post("/patient-journeys/{journey_id}/activities/{activity_id}/pathology-case", response_model=PathologyCaseOut)
def add_pathology_case(journey_id: int, activity_id: int, payload: PathologyCaseCreate, response: Response, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("pathology_cases.update"))):
    actor = context.actor; journey = visit(db, journey_id, context.active_clinic_id); activity = get_activity(db, journey_id, activity_id)
    item, created = create_case(db, journey, activity, payload.model_dump(), actor, request)
    response.status_code = 201 if created else 200
    db.commit(); return pathology_case(db, item.id, context.active_clinic_id)


@router.get("/pathology-cases/{case_id}", response_model=PathologyCaseOut)
def get_case(case_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("pathology_cases.read"))):
    return pathology_case(db, case_id, context.active_clinic_id)


@router.post("/pathology-cases/{case_id}/result-link", response_model=PathologyCaseOut)
def add_result_link(case_id: int, payload: ReportLinkCreate, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("pathology_results.receive"))):
    actor=context.actor;item = pathology_case(db, case_id, context.active_clinic_id); link_result(db, item, payload.clinical_document_id, actor, request); db.commit(); return pathology_case(db, item.id, context.active_clinic_id)


@router.get("/patient-journeys/{journey_id}/pathology-cases", response_model=list[PathologyCaseOut])
def visit_pathology_cases(journey_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("pathology_cases.read"))):
    visit(db, journey_id, context.active_clinic_id)
    return db.scalars(select(PathologyCase).options(selectinload(PathologyCase.specimens)).where(PathologyCase.journey_id == journey_id).order_by(PathologyCase.id)).all()


@router.post("/pathology-cases/{case_id}/transition", response_model=PathologyCaseOut)
def change_status(case_id: int, payload: PathologyStatusUpdate, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("pathology_cases.update"))):
    actor=context.actor;item = pathology_case(db, case_id, context.active_clinic_id); transition_case(db, item, payload.target_status, payload.external_case_number, payload.reason, actor, request); db.commit(); return pathology_case(db, item.id, context.active_clinic_id)


@router.post("/pathology-cases/{case_id}/review", response_model=PathologyCaseOut)
def review(case_id: int, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("pathology_results.review"))):
    actor=context.actor;item = pathology_case(db, case_id, context.active_clinic_id); review_result(db, item, actor, request); db.commit(); return pathology_case(db, item.id, context.active_clinic_id)


@router.post("/pathology-cases/{case_id}/communication-decision", response_model=PathologyCaseOut)
def communication_decision(case_id: int, payload: PathologyCommunicationDecision, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("pathology_communication.decide"))):
    actor=context.actor;item = pathology_case(db, case_id, context.active_clinic_id)
    decide_communication(db, item, payload.disposition, payload.note, payload.contact_attempts, actor, request)
    db.commit()
    return pathology_case(db, item.id, context.active_clinic_id)
