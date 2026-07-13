from datetime import datetime,timedelta,timezone
from uuid import uuid4
from fastapi import HTTPException,Request
from sqlalchemy.orm import Session
from app.auth.dependencies import Actor
from app.models.domain import CommunicationEvent,JourneyEvent,JourneyPreparation,JourneyReminder,PatientJourney,PreparationPlanTemplate
from app.services.patient_journeys import add_event

class DemoDeliveryProvider:
 """Local/demo boundary. Sending never implies delivery."""
 def send(self,event:CommunicationEvent)->str: return "sent"

def assign_preparation(db:Session,journey:PatientJourney,template:PreparationPlanTemplate,channel:str,actor:Actor,request:Request):
 if not template.active or not template.approved_at: raise HTTPException(422,detail="Plan pripreme mora biti aktivan i ljudski odobren")
 if journey.current_stage in {"completed","cancelled","no_show"}: raise HTTPException(409,detail="Zatvorenom putovanju nije moguće dodijeliti pripremu")
 existing=db.query(JourneyPreparation).filter_by(journey_id=journey.id).one_or_none()
 if existing: raise HTTPException(409,detail="Putovanje već ima dodijeljen plan pripreme")
 states={item.get("key",f"requirement_{index}"):"not_confirmed" for index,item in enumerate(template.requirements_json)}
 assignment=JourneyPreparation(journey_id=journey.id,template_id=template.id,status="assigned",assigned_by=actor.user_id,requirement_states_json=states);db.add(assignment);journey.preparation_status="assigned";db.flush()
 start=datetime.combine(journey.appointment.date,journey.appointment.start_time,tzinfo=timezone.utc)
 schedule=template.reminder_schedule_json or [{"days_before":2,"type":"appointment_reminder"},{"days_before":1,"type":"preparation_reminder"}]
 for item in schedule: db.add(JourneyReminder(journey_id=journey.id,reminder_type=item.get("type","preparation_reminder"),channel=channel,scheduled_at=start-timedelta(days=int(item.get("days_before",1))),status="scheduled"))
 add_event(db,journey,"preparation_assigned",f"Dodijeljen plan pripreme {template.name} v{template.version}",actor,request,journey.current_stage,journey.current_stage,{"template_id":template.id});return assignment

def dispatch_reminder(db:Session,reminder:JourneyReminder,actor:Actor,request:Request):
 if reminder.status not in {"scheduled","failed"}: raise HTTPException(409,detail="Podsjetnik nije spreman za slanje")
 event=CommunicationEvent(journey_id=reminder.journey_id,channel=reminder.channel,template_key=reminder.reminder_type,status="queued",scheduled_at=reminder.scheduled_at,correlation_id=str(uuid4()));db.add(event);db.flush()
 try: event.status=DemoDeliveryProvider().send(event);event.sent_at=datetime.now(timezone.utc);reminder.status="sent"
 except Exception as exc: event.status="failed";event.failure_reason=str(exc);reminder.status="failed"
 reminder.communication_event_id=event.id;add_event(db,reminder.journey,"reminder_dispatched",f"Podsjetnik {reminder.reminder_type}: {reminder.status}",actor,request,reminder.journey.current_stage,reminder.journey.current_stage,{"communication_event_id":event.id});return event
