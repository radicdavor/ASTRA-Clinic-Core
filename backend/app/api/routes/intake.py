from fastapi import APIRouter,Depends,Request
from sqlalchemy.orm import Session
from app.auth.dependencies import CurrentUserContext,require_active_clinic
from app.core.database import get_db
from app.schemas.common import AppointmentCreate,AppointmentOut
from app.services.appointments import create_appointment_with_journey

router=APIRouter(prefix="/api/intake",tags=["intake"])

@router.post("/web/appointments",response_model=AppointmentOut)
def web_booking(payload:AppointmentCreate,request:Request,db:Session=Depends(get_db),context:CurrentUserContext=Depends(require_active_clinic("journey.create"))):
    data=payload.model_dump();data["source"]="web_booking"
    data["clinic_id"]=context.active_clinic_id
    appointment=create_appointment_with_journey(db,data,context.actor,request);db.commit();db.refresh(appointment);return appointment
