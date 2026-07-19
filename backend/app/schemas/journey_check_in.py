from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class CheckInItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; item_key: str; category: str; label: str; state: str; requires_clinician: bool; note: str | None; position: int

class CheckInOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; journey_id: int; status: str; arrived_at: datetime | None; completed_at: datetime | None; items: list[CheckInItemOut]

class CheckInItemUpdate(BaseModel):
    state: str = Field(pattern="^(confirmed|not_confirmed|not_applicable|requires_clinician_review|blocked)$")
    note: str | None = Field(default=None, max_length=2000)

class ReceptionCheckInItemResult(BaseModel):
    item_key: str = Field(min_length=2, max_length=100)
    note: str | None = Field(default=None, max_length=2000)

class ReceptionCheckInComplete(BaseModel):
    items: list[ReceptionCheckInItemResult] = Field(default_factory=list)
