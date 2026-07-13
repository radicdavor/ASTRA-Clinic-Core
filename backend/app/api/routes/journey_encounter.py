from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy import select
from sqlalchemy.orm import Session,joinedload,selectinload
from app.audit.service import audit,snapshot
from app.auth.dependencies import Actor,require_permission
from app.core.database import get_db
from app.models.domain import JourneyEncounter,PatientJourney
from app.schemas.journey_encounter import EncounterOut,EncounterUpdate
from app.services.patient_journeys import transition
router=APIRouter(prefix="/api/patient-journeys",tags=["journey-encounter"])
def get_journey(db,id):
 item=db.scalar(select(PatientJourney).options(joinedload(PatientJourney.appointment),selectinload(PatientJourney.blockers)).where(PatientJourney.id==id))
 if not item: raise HTTPException(404,detail="Tijek pacijenta nije pronađen")
 return item
def get_encounter(db,jid):
 item=db.scalar(select(JourneyEncounter).where(JourneyEncounter.journey_id==jid))
 if not item: raise HTTPException(404,detail="Klinički susret nije otvoren")
 return item
@router.post("/{journey_id}/encounter",response_model=EncounterOut)
def open_encounter(journey_id:int,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("encounter.write"))):
 journey=get_journey(db,journey_id)
 if db.scalar(select(JourneyEncounter).where(JourneyEncounter.journey_id==journey.id)): raise HTTPException(409,detail="Klinički susret je već otvoren")
 transition(db,journey,"in_encounter",actor,request,"Liječnik otvorio klinički susret");item=JourneyEncounter(journey_id=journey.id,clinical_episode_id=journey.appointment.episode_id,opened_by=actor.user_id);db.add(item);db.flush();audit(db,"encounter_opened","JourneyEncounter",item.id,"Otvoren klinički susret",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();db.refresh(item);return item
@router.get("/{journey_id}/encounter",response_model=EncounterOut)
def encounter_detail(journey_id:int,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("encounter.read"))): return get_encounter(db,journey_id)
@router.patch("/{journey_id}/encounter",response_model=EncounterOut)
def update_encounter(journey_id:int,payload:EncounterUpdate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("encounter.write"))):
 item=get_encounter(db,journey_id)
 if item.status!="in_progress": raise HTTPException(409,detail="Dovršeni susret nije moguće mijenjati")
 before=snapshot(item)
 for key,value in payload.model_dump(exclude_unset=True).items(): setattr(item,key,value)
 audit(db,"encounter_updated","JourneyEncounter",item.id,"Ažurirana bilješka kliničkog susreta",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(item),request);db.commit();db.refresh(item);return item
@router.post("/{journey_id}/encounter/complete",response_model=EncounterOut)
def complete_encounter(journey_id:int,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("encounter.complete"))):
 journey=get_journey(db,journey_id);item=get_encounter(db,journey_id)
 if item.status!="in_progress": raise HTTPException(409,detail="Klinički susret je već dovršen")
 if not any((item.anamnesis,item.examination,item.procedure_findings,item.diagnosis,item.recommendations)): raise HTTPException(422,detail="Prije završetka upišite nalaz kliničkog susreta")
 item.status="completed";item.completed_by=actor.user_id;item.completed_at=datetime.now(timezone.utc);journey.encounter_status="completed";transition(db,journey,"procedure_completed",actor,request,"Liječnik dovršio postupak");audit(db,"encounter_completed","JourneyEncounter",item.id,"Dovršen klinički susret",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();db.refresh(item);return item
