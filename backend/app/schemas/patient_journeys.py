from datetime import date, datetime, time
from pydantic import BaseModel, ConfigDict, Field

class JourneyCreate(BaseModel):
    appointment_id:int
    intake_channel:str=Field(pattern="^(web|ai_secretary|manual)$")
    initial_stage:str=Field(default="booked",pattern="^(requested|booked)$")

class JourneyTransition(BaseModel):
    target_stage:str
    reason:str|None=Field(default=None,max_length=1000)

class JourneyStatusUpdate(BaseModel):
    document_status:str|None=None
    preparation_status:str|None=None
    check_in_status:str|None=None
    encounter_status:str|None=None
    consumables_status:str|None=None
    billing_status:str|None=None
    payment_status:str|None=None

class BlockerCreate(BaseModel):
    blocker_key:str=Field(min_length=2,max_length=120)
    category:str=Field(min_length=2,max_length=60)
    title:str=Field(min_length=2,max_length=220)
    details:str|None=Field(default=None,max_length=4000)
    is_clinical:bool=False

class BlockerResolve(BaseModel):
    resolution_note:str=Field(min_length=2,max_length=2000)

class JourneyEventOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int;event_type:str;from_stage:str|None;to_stage:str|None;summary:str;source_channel:str;actor_user_id:int|None;actor_type:str;request_id:str|None;metadata_json:dict|None;created_at:datetime

class JourneyBlockerOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int;blocker_key:str;category:str;title:str;details:str|None;is_clinical:bool;status:str;resolved_at:datetime|None;resolution_note:str|None;created_at:datetime

class JourneyServiceBrief(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int;name:str

class JourneyProviderBrief(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int;full_name:str

class JourneyRoomBrief(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int;name:str

class JourneyAppointmentBrief(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int;service_id:int;provider_id:int;room_id:int;episode_id:int|None;date:date;start_time:time;end_time:time;status:str;source:str
    service:JourneyServiceBrief;provider:JourneyProviderBrief;room:JourneyRoomBrief

class JourneyActivityCreate(BaseModel):
    service_id:int
    provider_id:int
    room_id:int
    date:date
    start_time:time
    end_time:time
    activity_key:str=Field(min_length=2,max_length=120,pattern=r"^[a-z0-9][a-z0-9_-]*$")
    activity_kind:str=Field(default="specialist_consultation",min_length=2,max_length=60)
    specialty_key:str=Field(default="general",min_length=2,max_length=80)
    required:bool=True
    depends_on_activity_id:int|None=None
    notes:str|None=Field(default=None,max_length=2000)

class JourneyActivityStatusUpdate(BaseModel):
    target_status:str=Field(pattern="^(ready|in_progress|completed|not_performed|cancelled)$")
    reason:str|None=Field(default=None,max_length=2000)

class JourneyActivityOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int;journey_id:int;appointment_id:int|None;service_id:int;activity_key:str;activity_kind:str;specialty_key:str;clinic_id:int|None;primary_provider_id:int|None;room_id:int|None;sequence:int;depends_on_activity_id:int|None;required:bool;planned_start:datetime;planned_end:datetime;actual_start:datetime|None;actual_end:datetime|None;status:str;not_performed_reason:str|None;form_resolution_status:str;billing_status:str;consumables_status:str;created_at:datetime;updated_at:datetime

class PatientBrief(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int;first_name:str;last_name:str;date_of_birth:date|None=None;oib:str|None=None

class JourneyOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int;patient_id:int;appointment_id:int;intake_channel:str;current_stage:str;document_status:str;preparation_status:str;check_in_status:str;encounter_status:str;consumables_status:str;billing_status:str;payment_status:str;closed_at:datetime|None;created_at:datetime;updated_at:datetime;patient:PatientBrief;appointment:JourneyAppointmentBrief;activities:list[JourneyActivityOut]=[];events:list[JourneyEventOut]=[];blockers:list[JourneyBlockerOut]=[]
