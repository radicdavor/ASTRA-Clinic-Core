from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class LabTestCreate(BaseModel):
    test_name: str = Field(min_length=2, max_length=180)
    unit: str | None = Field(default=None, max_length=60)
    reference_low: Decimal | None = None
    reference_high: Decimal | None = None
    @model_validator(mode="after")
    def range_valid(self):
        if self.reference_low is not None and self.reference_high is not None and self.reference_low > self.reference_high:
            raise ValueError("Donja referentna vrijednost mora biti manja od gornje")
        return self

class LabOrderCreate(BaseModel):
    patient_id: int
    episode_id: int | None = None
    appointment_id: int | None = None
    template_id: int | None = None
    external_laboratory: str | None = Field(default=None, max_length=180)
    ordered_at: date
    notes: str | None = None
    tests: list[LabTestCreate] = []

class LabTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; name: str; condition: str; category: str; description: str | None; tests: list[dict]; active: bool

class LabResultUpdate(BaseModel):
    id: int
    value: Decimal | None = None
    text_value: str | None = Field(default=None, max_length=240)
    unit: str | None = Field(default=None, max_length=60)
    reference_low: Decimal | None = None
    reference_high: Decimal | None = None
    @model_validator(mode="after")
    def range_valid(self):
        if self.reference_low is not None and self.reference_high is not None and self.reference_low > self.reference_high:
            raise ValueError("Donja referentna vrijednost mora biti manja od gornje")
        return self

class LabResultsUpdate(BaseModel):
    results: list[LabResultUpdate] = Field(min_length=1)
    collected: bool = False

class LabReview(BaseModel):
    conclusion: str = Field(min_length=2)

class LabCancel(BaseModel):
    reason: str = Field(min_length=3, max_length=500)

class LabHistoryItem(BaseModel):
    order_id: int
    ordered_at: date
    test_name: str
    value: Decimal | None
    text_value: str | None
    unit: str | None
    flag: str

class LabCollection(BaseModel):
    specimen_type: str = Field(pattern="^(blood|urine|stool|other)$")

class PatientBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; first_name: str; last_name: str; date_of_birth: date | None = None

class LabResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; test_name: str; value: Decimal | None; text_value: str | None; unit: str | None; reference_low: Decimal | None; reference_high: Decimal | None; flag: str; resulted_at: datetime | None

class LabOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; patient_id: int; episode_id: int | None; appointment_id: int | None; template_id: int | None; external_laboratory: str | None; status: str; ordered_at: date; specimen_type: str; collected_at: datetime | None; collected_by: int | None; dispatched_at: datetime | None; dispatched_by: int | None; external_received_at: datetime | None; notes: str | None; review_conclusion: str | None; reviewed_by: int | None; reviewed_at: datetime | None; cancelled_at: datetime | None; cancelled_by: int | None; cancellation_reason: str | None; created_at: datetime; patient: PatientBrief; results: list[LabResultOut]
