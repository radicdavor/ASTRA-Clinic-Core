from datetime import datetime
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
class EncounterUpdate(BaseModel):
 anamnesis:str|None=Field(default=None,max_length=20000);examination:str|None=Field(default=None,max_length=20000);patient_findings:str|None=Field(default=None,max_length=20000);opinion:str|None=Field(default=None,max_length=20000);procedure_findings:str|None=Field(default=None,max_length=20000);diagnosis:str|None=Field(default=None,max_length=20000);treatment:str|None=Field(default=None,max_length=20000);recommendations:str|None=Field(default=None,max_length=20000);follow_up_plan:str|None=Field(default=None,max_length=20000)
class EncounterOut(EncounterUpdate):
 model_config=ConfigDict(from_attributes=True)
 id:int;journey_id:int;clinical_episode_id:int|None;status:str;opened_by:int|None;opened_at:datetime;completed_by:int|None;completed_at:datetime|None;created_at:datetime;updated_at:datetime
class DiagnosisSuggestionRequest(BaseModel):
 anamnesis:str|None=Field(default=None,max_length=20000);examination:str|None=Field(default=None,max_length=20000);patient_findings:str|None=Field(default=None,max_length=20000);opinion:str|None=Field(default=None,max_length=20000)
class DiagnosisSuggestion(BaseModel):
 code:str=Field(min_length=3,max_length=12);title:str=Field(min_length=2,max_length=240)
class DiagnosisSuggestionsOut(BaseModel):
 diagnoses:list[DiagnosisSuggestion]=Field(max_length=5);provider:Literal["openai"]="openai";model:str;generated_at:datetime;disclaimer:str="AI prijedlog. Dijagnozu i WHO ICD-10 šifru provjerava i potvrđuje liječnik."
