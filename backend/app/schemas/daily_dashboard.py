from datetime import date, datetime, time

from pydantic import BaseModel, Field

class DailyDashboardBlocker(BaseModel):
    id: int
    title: str
    details: str | None = None
    is_clinical: bool = False


class DailyDashboardRow(BaseModel):
    journey_id: int
    appointment_id: int
    time: time
    patient_id: int
    patient_name: str
    patient_date_of_birth: date | None
    service_id: int
    service_name: str
    clinician_id: int
    clinician_name: str
    room_id: int
    room_name: str
    intake_channel: str
    workflow_stage: str
    document_status: str
    preparation_status: str
    arrival_status: str
    check_in_status: str
    encounter_status: str
    consumables_status: str
    billing_status: str
    payment_status: str
    blocker_status: str
    blocker_labels: list[str] = Field(default_factory=list)
    blockers: list[DailyDashboardBlocker] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)


class DailyDashboardResponse(BaseModel):
    date: date
    refreshed_at: datetime
    visible_sections: list[str]
    rows: list[DailyDashboardRow]
