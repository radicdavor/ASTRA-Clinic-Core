from fastapi import APIRouter,Depends,Request
from sqlalchemy.orm import Session
from app.auth.dependencies import Actor,require_permission
from app.core.database import get_db
from app.schemas.common import AppointmentCreate,AppointmentOut
from app.services.appointments import create_appointment_with_journey

router=APIRouter(prefix="/api/intake",tags=["intake"])

@router.post("/web/appointments",response_model=AppointmentOut)
def web_booking(payload:AppointmentCreate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("journey.create"))):
    data=payload.model_dump();data["source"]="web_booking"
    appointment=create_appointment_with_journey(db,data,actor,request);db.commit();db.refresh(appointment);return appointment
