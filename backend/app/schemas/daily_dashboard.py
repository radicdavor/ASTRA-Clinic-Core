from datetime import date, datetime, time

from pydantic import BaseModel, Field

class DailyDashboardBlocker(BaseModel):
    id: int
    title: str
    details: str | None = None
    is_clinical: bool = False


class DailyDashboardClinic(BaseModel):
    id: int
    name: str


class DailyDashboardActivity(BaseModel):
    id: int
    sequence: int
    time: time
    service_name: str
    clinician_name: str | None = None
    room_name: str | None = None
    status: str


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
    clinic_id: int | None = None
    clinic_name: str | None = None
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
    reception_warning: bool = False
    reception_warning_details: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)
    activity_count: int = 1
    current_activity_id: int | None = None
    next_activity_id: int | None = None
    activities: list[DailyDashboardActivity] = Field(default_factory=list)


class DailyDashboardResponse(BaseModel):
    date: date
    refreshed_at: datetime
    visible_sections: list[str]
    viewer_role: str
    scope: str
    scope_label: str
    scoped_clinician_id: int | None = None
    can_filter_clinician: bool = False
    available_clinics: list[DailyDashboardClinic] = Field(default_factory=list)
    rows: list[DailyDashboardRow]
