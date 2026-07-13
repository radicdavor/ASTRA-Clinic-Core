from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy import select
from sqlalchemy.orm import Session,joinedload
from app.audit.service import audit,snapshot
from app.auth.dependencies import Actor,require_permission
from app.core.database import get_db
from app.models.domain import DocumentRequest,JourneyForm,JourneyPreparation,JourneyReminder,PatientFormTemplate,PatientJourney,PreparationPlanTemplate
from app.schemas.journey_preparation import CommunicationOut,DocumentRequestCreate,FormAnswer,FormRequest,FormTemplateCreate,FormTemplateOut,PreparationAssign,PreparationOut,PreparationTemplateCreate,PreparationTemplateOut,ReminderOut,RequirementUpdate
from app.services.journey_preparation import assign_preparation,dispatch_reminder

router=APIRouter(prefix="/api",tags=["journey-preparation"])
def journey(db,id):
 item=db.scalar(select(PatientJourney).options(joinedload(PatientJourney.appointment)).where(PatientJourney.id==id))
 if not item: raise HTTPException(404,detail="Tijek pacijenta nije pronađen")
 return item

@router.get("/preparation-templates",response_model=list[PreparationTemplateOut])
def templates(db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.read"))): return db.scalars(select(PreparationPlanTemplate).where(PreparationPlanTemplate.active.is_(True)).order_by(PreparationPlanTemplate.name)).all()
@router.post("/preparation-templates",response_model=PreparationTemplateOut)
def create_template(payload:PreparationTemplateCreate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("preparation.review"))):
 data=payload.model_dump(exclude={"approved"});item=PreparationPlanTemplate(**data,approved_by=actor.user_id if payload.approved else None,approved_at=datetime.now(timezone.utc) if payload.approved else None);db.add(item);db.flush();audit(db,"create","PreparationPlanTemplate",item.id,item.name,actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();db.refresh(item);return item
@router.post("/patient-journeys/{journey_id}/preparation",response_model=PreparationOut)
def assign(journey_id:int,payload:PreparationAssign,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("preparation.assign"))):
 j=journey(db,journey_id);template=db.get(PreparationPlanTemplate,payload.template_id)
 if not template: raise HTTPException(404,detail="Plan pripreme nije pronađen")
 item=assign_preparation(db,j,template,payload.channel,actor,request);audit(db,"assign","PatientJourney",j.id,"Dodijeljena priprema",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();return db.scalar(select(JourneyPreparation).options(joinedload(JourneyPreparation.template)).where(JourneyPreparation.id==item.id))
@router.patch("/patient-journeys/{journey_id}/preparation/requirements",response_model=PreparationOut)
def requirement(journey_id:int,payload:RequirementUpdate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("preparation.review"))):
 j=journey(db,journey_id);item=db.scalar(select(JourneyPreparation).options(joinedload(JourneyPreparation.template)).where(JourneyPreparation.journey_id==j.id))
 if not item: raise HTTPException(404,detail="Priprema nije dodijeljena")
 if payload.requirement_key not in item.requirement_states_json: raise HTTPException(404,detail="Stavka pripreme nije pronađena")
 states=dict(item.requirement_states_json);states[payload.requirement_key]=payload.state;item.requirement_states_json=states
 if payload.state in {"blocked","requires_clinician_review"}: item.status="review_required";j.preparation_status="review_required"
 elif states and all(value in {"confirmed","not_applicable"} for value in states.values()): item.status="complete";item.completed_at=datetime.now(timezone.utc);j.preparation_status="complete"
 else: item.status="in_progress";j.preparation_status="in_progress"
 audit(db,"preparation_review","PatientJourney",j.id,f"Stavka pripreme: {payload.requirement_key}",actor.user_id,actor.actor_type,actor.api_key_id,None,{"state":payload.state},request);db.commit();return item
@router.get("/patient-journeys/{journey_id}/reminders",response_model=list[ReminderOut])
def reminders(journey_id:int,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.read"))): return db.scalars(select(JourneyReminder).where(JourneyReminder.journey_id==journey_id).order_by(JourneyReminder.scheduled_at)).all()
@router.post("/patient-journeys/{journey_id}/reminders/{reminder_id}/dispatch",response_model=CommunicationOut)
def dispatch(journey_id:int,reminder_id:int,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("preparation.assign"))):
 reminder=db.scalar(select(JourneyReminder).options(joinedload(JourneyReminder.journey)).where(JourneyReminder.id==reminder_id,JourneyReminder.journey_id==journey_id))
 if not reminder: raise HTTPException(404,detail="Podsjetnik nije pronađen")
 event=dispatch_reminder(db,reminder,actor,request);audit(db,"reminder_dispatch","PatientJourney",journey_id,f"Podsjetnik {reminder.status}",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(event),request);db.commit();db.refresh(event);return event
@router.post("/form-templates",response_model=FormTemplateOut)
def create_form_template(payload:FormTemplateCreate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("preparation.review"))):
 item=PatientFormTemplate(**payload.model_dump(exclude={"approved"}),approved_by=actor.user_id if payload.approved else None,approved_at=datetime.now(timezone.utc) if payload.approved else None);db.add(item);db.flush();audit(db,"create","PatientFormTemplate",item.id,item.name,actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();db.refresh(item);return item
@router.post("/patient-journeys/{journey_id}/forms")
def request_form(journey_id:int,payload:FormRequest,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("preparation.assign"))):
 j=journey(db,journey_id);template=db.get(PatientFormTemplate,payload.template_id)
 if not template or not template.active or not template.approved_at: raise HTTPException(422,detail="Obrazac mora biti aktivan i odobren")
 item=JourneyForm(journey_id=j.id,template_id=template.id,status="requested");db.add(item);j.current_stage="awaiting_forms";db.flush();audit(db,"form_request","PatientJourney",j.id,template.name,actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();return {"id":item.id,"status":item.status}
@router.put("/patient-journeys/{journey_id}/forms/{form_id}")
def answer_form(journey_id:int,form_id:int,payload:FormAnswer,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.transition"))):
 item=db.get(JourneyForm,form_id)
 if not item or item.journey_id!=journey_id: raise HTTPException(404,detail="Obrazac nije pronađen")
 item.answers_json=payload.answers_json;item.status="completed";item.completed_at=datetime.now(timezone.utc);audit(db,"form_complete","PatientJourney",journey_id,"Obrazac ispunjen; čeka pregled",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();return {"id":item.id,"status":item.status}
@router.post("/patient-journeys/{journey_id}/document-requests")
def request_document(journey_id:int,payload:DocumentRequestCreate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("documents.request"))):
 j=journey(db,journey_id);item=DocumentRequest(journey_id=j.id,requested_by=actor.user_id,**payload.model_dump());db.add(item);j.document_status="requested";db.flush();audit(db,"document_request","PatientJourney",j.id,item.title,actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();return {"id":item.id,"status":item.status}
