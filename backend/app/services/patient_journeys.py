from datetime import datetime, timezone
from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.dependencies import Actor
from app.models.domain import Appointment, JourneyBlocker, JourneyEvent, PatientJourney

INTAKE_CHANNELS={"web","ai_secretary","manual"}
STAGES={"requested","booked","awaiting_forms","awaiting_documents","preparation_in_progress","ready_for_arrival","arrived","check_in_review","ready_for_clinician","in_encounter","procedure_completed","awaiting_billing","awaiting_payment","completed","cancelled","no_show","blocked"}
TERMINAL_STAGES={"completed","cancelled","no_show"}
ALLOWED_TRANSITIONS={
 "requested":{"booked","cancelled","blocked"},"booked":{"awaiting_forms","awaiting_documents","preparation_in_progress","ready_for_arrival","cancelled","no_show","blocked"},
 "awaiting_forms":{"awaiting_documents","preparation_in_progress","ready_for_arrival","cancelled","blocked"},"awaiting_documents":{"preparation_in_progress","ready_for_arrival","cancelled","blocked"},
 "preparation_in_progress":{"ready_for_arrival","cancelled","blocked"},"ready_for_arrival":{"arrived","cancelled","no_show","blocked"},"arrived":{"check_in_review","cancelled","blocked"},
 "check_in_review":{"ready_for_clinician","cancelled","blocked"},"ready_for_clinician":{"in_encounter","cancelled","blocked"},"in_encounter":{"procedure_completed","cancelled","blocked"},
 "procedure_completed":{"awaiting_billing","blocked"},"awaiting_billing":{"awaiting_payment","blocked"},"awaiting_payment":{"completed","blocked"},"blocked":STAGES-TERMINAL_STAGES-{"blocked"},
 "completed":set(),"cancelled":set(),"no_show":set(),
}
STATUS_VALUES={
 "document_status":{"not_requested","requested","partial","complete","review_required","blocked"},
 "preparation_status":{"not_assigned","assigned","acknowledged","in_progress","complete","review_required","blocked"},
 "check_in_status":{"not_arrived","arrived","in_review","ready","blocked"},
 "encounter_status":{"not_started","in_progress","completed","aborted"},
 "consumables_status":{"not_ready","pending","confirmed","not_applicable"},
 "billing_status":{"not_ready","ready","invoice_created","adjustment_required","closed"},
 "payment_status":{"not_due","unpaid","partially_paid","paid","refunded","cancelled","deferred"},
}

def add_event(db:Session,journey:PatientJourney,event_type:str,summary:str,actor:Actor,request:Request,from_stage:str|None=None,to_stage:str|None=None,metadata:dict|None=None):
 db.add(JourneyEvent(journey_id=journey.id,event_type=event_type,from_stage=from_stage,to_stage=to_stage,summary=summary,source_channel=journey.intake_channel,actor_user_id=actor.user_id,actor_type=actor.actor_type,request_id=getattr(request.state,"request_id",None),metadata_json=metadata))

def create_journey(db:Session,appointment:Appointment,intake_channel:str,initial_stage:str,actor:Actor,request:Request)->PatientJourney:
 if intake_channel not in INTAKE_CHANNELS: raise HTTPException(422,detail="Dopušteni intake kanali su web, ai_secretary i manual")
 if initial_stage not in {"requested","booked"}: raise HTTPException(422,detail="Početna faza mora biti requested ili booked")
 existing=db.scalar(select(PatientJourney).where(PatientJourney.appointment_id==appointment.id))
 if existing: raise HTTPException(409,detail="Termin već ima kanonsko putovanje pacijenta")
 journey=PatientJourney(patient_id=appointment.patient_id,appointment_id=appointment.id,intake_channel=intake_channel,current_stage=initial_stage,created_by=actor.user_id,updated_by=actor.user_id)
 db.add(journey);db.flush();add_event(db,journey,"journey_created",f"Putovanje pacijenta stvoreno iz kanala {intake_channel}",actor,request,None,initial_stage)
 return journey

def update_substatuses(db:Session,journey:PatientJourney,updates:dict,actor:Actor,request:Request):
 if journey.current_stage in TERMINAL_STAGES: raise HTTPException(409,detail="Zatvoreno putovanje više se ne može mijenjati")
 before={}
 for field,value in updates.items():
  if field not in STATUS_VALUES or value not in STATUS_VALUES[field]: raise HTTPException(422,detail=f"Neispravan status: {field}={value}")
  before[field]=getattr(journey,field);setattr(journey,field,value)
 journey.updated_by=actor.user_id;db.flush();add_event(db,journey,"substatus_updated","Ažurirani podstatusi putovanja",actor,request,journey.current_stage,journey.current_stage,{"before":before,"after":updates})

def transition(db:Session,journey:PatientJourney,target:str,actor:Actor,request:Request,reason:str|None=None):
 if target not in STAGES: raise HTTPException(422,detail="Nepoznata faza putovanja")
 if target not in ALLOWED_TRANSITIONS.get(journey.current_stage,set()): raise HTTPException(409,detail=f"Prijelaz {journey.current_stage} → {target} nije dopušten")
 open_blockers=[item for item in journey.blockers if item.status=="open"]
 if target in {"ready_for_clinician","in_encounter","completed"} and open_blockers: raise HTTPException(409,detail="Otvoreni blokatori moraju biti riješeni prije ovog prijelaza")
 if target=="ready_for_clinician" and journey.check_in_status!="ready": raise HTTPException(409,detail="Check-in mora biti spreman za liječnika")
 if target=="in_encounter" and journey.check_in_status!="ready": raise HTTPException(409,detail="Pregled ne može započeti prije dovršenog check-ina")
 if target=="procedure_completed" and journey.encounter_status!="completed": raise HTTPException(409,detail="Klinički susret mora biti dovršen")
 if target=="awaiting_payment" and journey.billing_status!="invoice_created": raise HTTPException(409,detail="Račun mora biti izrađen prije naplate")
 if target=="completed":
  if journey.encounter_status!="completed" or journey.consumables_status not in {"confirmed","not_applicable"} or journey.billing_status!="closed" or journey.payment_status not in {"paid","refunded","cancelled","deferred"}: raise HTTPException(409,detail="Susret, potrošni materijal, račun i plaćanje moraju biti razriješeni")
 before=journey.current_stage;journey.current_stage=target;journey.updated_by=actor.user_id
 if target=="arrived": journey.check_in_status="arrived"
 elif target=="check_in_review": journey.check_in_status="in_review"
 elif target=="in_encounter": journey.encounter_status="in_progress"
 elif target in TERMINAL_STAGES: journey.closed_at=datetime.now(timezone.utc)
 db.flush();add_event(db,journey,"stage_transition",reason or f"Prijelaz {before} → {target}",actor,request,before,target)

def add_blocker(db:Session,journey:PatientJourney,data:dict,actor:Actor,request:Request)->JourneyBlocker:
 if journey.current_stage in TERMINAL_STAGES: raise HTTPException(409,detail="Zatvorenom putovanju nije moguće dodati blokator")
 item=JourneyBlocker(journey_id=journey.id,created_by=actor.user_id,**data);db.add(item);db.flush();add_event(db,journey,"blocker_added",f"Dodan blokator: {item.title}",actor,request,journey.current_stage,journey.current_stage,{"blocker_id":item.id,"clinical":item.is_clinical});return item

def resolve_blocker(db:Session,journey:PatientJourney,item:JourneyBlocker,note:str,actor:Actor,request:Request):
 if item.status!="open": raise HTTPException(409,detail="Blokator je već riješen")
 item.status="resolved";item.resolved_by=actor.user_id;item.resolved_at=datetime.now(timezone.utc);item.resolution_note=note;db.flush();add_event(db,journey,"blocker_resolved",f"Riješen blokator: {item.title}",actor,request,journey.current_stage,journey.current_stage,{"blocker_id":item.id})
