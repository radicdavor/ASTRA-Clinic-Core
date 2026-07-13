from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator

class TherapyCreate(BaseModel):
    patient_id: int
    episode_id: int | None = None
    name: str = Field(min_length=2, max_length=180)
    instructions: str = Field(min_length=2, max_length=2000)
    start_date: date
    end_date: date | None = None
    prescriber: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=4000)
    @model_validator(mode="after")
    def dates_valid(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("Datum završetka ne može biti prije početka")
        return self

class TherapyUpdate(BaseModel):
    episode_id: int | None = None
    name: str = Field(min_length=2, max_length=180)
    instructions: str = Field(min_length=2, max_length=2000)
    start_date: date
    end_date: date | None = None
    prescriber: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=4000)

class TherapyStop(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)

class TherapyComplete(BaseModel):
    note: str | None = Field(default=None, max_length=1000)

class TherapyRenew(BaseModel):
    start_date: date
    end_date: date | None = None
    instructions: str | None = Field(default=None, min_length=2, max_length=2000)

class PatientBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; first_name: str; last_name: str; date_of_birth: date | None = None

class TherapyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; patient_id: int; episode_id: int | None; parent_therapy_id: int | None; name: str; instructions: str; start_date: date; end_date: date | None; status: str; prescriber: str | None; notes: str | None; stopped_at: datetime | None; stop_reason: str | None; completed_at: datetime | None; completion_note: str | None; created_at: datetime; patient: PatientBrief
