from datetime import date
from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy import select
from sqlalchemy.orm import Session,joinedload,selectinload
from app.audit.service import audit,snapshot
from app.auth.dependencies import Actor,require_permission
from app.core.database import get_db
from app.models.domain import Appointment,JourneyBlocker,PatientJourney
from app.schemas.patient_journeys import BlockerCreate,BlockerResolve,JourneyBlockerOut,JourneyCreate,JourneyOut,JourneyStatusUpdate,JourneyTransition
from app.services.patient_journeys import add_blocker,create_journey,resolve_blocker,transition,update_substatuses

router=APIRouter(prefix="/api/patient-journeys",tags=["patient-journeys"])

def query():
 return select(PatientJourney).options(
  joinedload(PatientJourney.patient),
  joinedload(PatientJourney.appointment).joinedload(Appointment.service),
  joinedload(PatientJourney.appointment).joinedload(Appointment.provider),
  joinedload(PatientJourney.appointment).joinedload(Appointment.room),
  selectinload(PatientJourney.events),
  selectinload(PatientJourney.blockers),
 )
def get_journey(db:Session,journey_id:int):
 item=db.scalar(query().where(PatientJourney.id==journey_id))
 if not item: raise HTTPException(404,detail="Tijek pacijenta nije pronađen")
 return item

@router.get("",response_model=list[JourneyOut])
def list_journeys(day:date|None=None,patient_id:int|None=None,stage:str|None=None,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.read"))):
 stmt=query().join(Appointment,Appointment.id==PatientJourney.appointment_id).order_by(Appointment.date.desc(),Appointment.start_time)
 if day: stmt=stmt.where(Appointment.date==day)
 if patient_id: stmt=stmt.where(PatientJourney.patient_id==patient_id)
 if stage: stmt=stmt.where(PatientJourney.current_stage==stage)
 return db.scalars(stmt).unique().all()

@router.get("/{journey_id}",response_model=JourneyOut)
def journey_detail(journey_id:int,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.read"))): return get_journey(db,journey_id)

@router.post("",response_model=JourneyOut)
def create(payload:JourneyCreate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.create"))):
 appointment=db.get(Appointment,payload.appointment_id)
 if not appointment: raise HTTPException(404,detail="Termin nije pronađen")
 item=create_journey(db,appointment,payload.intake_channel,payload.initial_stage,actor,request);audit(db,"create","PatientJourney",item.id,"Stvoren kanonski tijek pacijenta",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();return get_journey(db,item.id)

@router.post("/{journey_id}/transition",response_model=JourneyOut)
def change_stage(journey_id:int,payload:JourneyTransition,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.transition"))):
 item=get_journey(db,journey_id);before=snapshot(item);transition(db,item,payload.target_stage,actor,request,payload.reason);audit(db,"transition","PatientJourney",item.id,payload.reason or "Promjena faze tijeka pacijenta",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(item),request);db.commit();return get_journey(db,item.id)

@router.patch("/{journey_id}/statuses",response_model=JourneyOut)
def change_statuses(journey_id:int,payload:JourneyStatusUpdate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.transition"))):
 item=get_journey(db,journey_id);updates=payload.model_dump(exclude_none=True)
 if not updates: raise HTTPException(422,detail="Nije poslana nijedna promjena")
 before=snapshot(item);update_substatuses(db,item,updates,actor,request);audit(db,"status_update","PatientJourney",item.id,"Ažurirani podstatusi tijeka pacijenta",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(item),request);db.commit();return get_journey(db,item.id)

@router.post("/{journey_id}/blockers",response_model=JourneyBlockerOut)
def create_blocker(journey_id:int,payload:BlockerCreate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.transition"))):
 journey=get_journey(db,journey_id);item=add_blocker(db,journey,payload.model_dump(),actor,request);audit(db,"blocker_add","PatientJourney",journey.id,item.title,actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();db.refresh(item);return item

@router.post("/{journey_id}/blockers/{blocker_id}/resolve",response_model=JourneyBlockerOut)
def close_blocker(journey_id:int,blocker_id:int,payload:BlockerResolve,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.transition"))):
 journey=get_journey(db,journey_id);item=db.get(JourneyBlocker,blocker_id)
 if not item or item.journey_id!=journey.id: raise HTTPException(404,detail="Blokator nije pronađen")
 before=snapshot(item);resolve_blocker(db,journey,item,payload.resolution_note,actor,request);audit(db,"blocker_resolve","PatientJourney",journey.id,item.title,actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(item),request);db.commit();db.refresh(item);return item
