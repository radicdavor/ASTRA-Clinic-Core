from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import JourneyCheckIn, JourneyCheckInItem, PatientJourney
from app.schemas.journey_check_in import CheckInItemUpdate, CheckInOut
from app.schemas.patient_journeys import JourneyOut
from app.services.journey_check_in import record_arrival, start_check_in, update_item

router=APIRouter(prefix="/api/patient-journeys",tags=["journey-check-in"])

def journey_query(): return select(PatientJourney).options(joinedload(PatientJourney.appointment),selectinload(PatientJourney.blockers))
def checkin_query(): return select(JourneyCheckIn).options(selectinload(JourneyCheckIn.items))
def get_journey(db,id):
    item=db.scalar(journey_query().where(PatientJourney.id==id))
    if not item: raise HTTPException(404,detail="Tijek pacijenta nije pronađen")
    return item

@router.post("/{journey_id}/arrival",response_model=JourneyOut)
def mark_arrival(journey_id:int,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("checkin.update"))):
    journey=get_journey(db,journey_id);before=snapshot(journey);record_arrival(db,journey,actor,request);audit(db,"patient_arrived","PatientJourney",journey.id,"Pacijent stigao",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(journey),request);db.commit();return get_journey(db,journey.id)

@router.post("/{journey_id}/check-in",response_model=CheckInOut)
def begin(journey_id:int,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("checkin.update"))):
    journey=get_journey(db,journey_id);before=snapshot(journey);item=start_check_in(db,journey,actor,request);audit(db,"checkin_started","PatientJourney",journey.id,"Započeta prijemna provjera",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(journey),request);db.commit();return db.scalar(checkin_query().where(JourneyCheckIn.id==item.id))

@router.get("/{journey_id}/check-in",response_model=CheckInOut)
def detail(journey_id:int,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.read"))):
    item=db.scalar(checkin_query().where(JourneyCheckIn.journey_id==journey_id))
    if not item: raise HTTPException(404,detail="Prijemna provjera nije započeta")
    return item

@router.patch("/{journey_id}/check-in/items/{item_id}",response_model=CheckInOut)
def change_item(journey_id:int,item_id:int,payload:CheckInItemUpdate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("checkin.update"))):
    journey=get_journey(db,journey_id);check_in=db.scalar(checkin_query().where(JourneyCheckIn.journey_id==journey_id));item=db.get(JourneyCheckInItem,item_id)
    if not check_in or not item or item.check_in_id!=check_in.id: raise HTTPException(404,detail="Stavka prijemne provjere nije pronađena")
    before=snapshot(item);update_item(db,journey,check_in,item,payload.state,payload.note,actor,request);audit(db,"checkin_item_changed","PatientJourney",journey.id,item.label,actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(item),request);db.commit();return db.scalar(checkin_query().where(JourneyCheckIn.id==check_in.id))
