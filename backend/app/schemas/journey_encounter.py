from datetime import datetime
from pydantic import BaseModel,ConfigDict,Field
class EncounterUpdate(BaseModel):
 anamnesis:str|None=Field(default=None,max_length=20000);examination:str|None=Field(default=None,max_length=20000);procedure_findings:str|None=Field(default=None,max_length=20000);diagnosis:str|None=Field(default=None,max_length=20000);treatment:str|None=Field(default=None,max_length=20000);recommendations:str|None=Field(default=None,max_length=20000);follow_up_plan:str|None=Field(default=None,max_length=20000)
class EncounterOut(EncounterUpdate):
 model_config=ConfigDict(from_attributes=True)
 id:int;journey_id:int;clinical_episode_id:int|None;status:str;opened_by:int|None;opened_at:datetime;completed_by:int|None;completed_at:datetime|None;created_at:datetime;updated_at:datetime
