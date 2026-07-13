from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


DEFAULT_REMINDER_SCHEDULE = [
    {"days_before": 2, "type": "appointment_reminder"},
    {"days_before": 1, "type": "preparation_reminder"},
]


class PreparationTemplateCreate(BaseModel):
    template_key: str = Field(min_length=2, max_length=100)
    name: str = Field(min_length=2, max_length=180)
    procedure_type: str = Field(min_length=2, max_length=100)
    version: str = Field(min_length=1, max_length=40)
    patient_instructions: str = Field(min_length=2)
    requirements_json: list[dict] = Field(default_factory=list)
    reminder_schedule_json: list[dict] = Field(
        default_factory=lambda: [dict(item) for item in DEFAULT_REMINDER_SCHEDULE]
    )
    approved: bool = False
class PreparationTemplateOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:int;template_key:str;name:str;procedure_type:str;version:str;patient_instructions:str;requirements_json:list;reminder_schedule_json:list;active:bool;approved_at:datetime|None
class PreparationAssign(BaseModel): template_id:int;channel:str=Field(default="email",pattern="^(email|sms|web_portal|manual)$")
class PreparationOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:int;journey_id:int;template_id:int;status:str;assigned_at:datetime;acknowledged_at:datetime|None;completed_at:datetime|None;requirement_states_json:dict;template:PreparationTemplateOut
class RequirementUpdate(BaseModel): requirement_key:str;state:str=Field(pattern="^(confirmed|not_confirmed|not_applicable|requires_clinician_review|blocked)$")
class FormTemplateCreate(BaseModel):
    template_key: str
    name: str
    version: str
    fields_json: list[dict] = Field(default_factory=list)
    approved: bool = False
class FormTemplateOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:int;template_key:str;name:str;version:str;fields_json:list;active:bool;approved_at:datetime|None
class FormRequest(BaseModel): template_id:int
class FormAnswer(BaseModel): answers_json:dict
class DocumentRequestCreate(BaseModel): document_type:str;title:str;mandatory:bool=True
class CommunicationOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:int;journey_id:int;channel:str;template_key:str;status:str;scheduled_at:datetime|None;sent_at:datetime|None;delivered_at:datetime|None;failure_reason:str|None;correlation_id:str
class ReminderOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:int;journey_id:int;reminder_type:str;channel:str;scheduled_at:datetime;status:str;communication_event_id:int|None
