from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InterventionCreate(BaseModel):
    intervention_type: str = Field(pattern="^(biopsy|polypectomy|injection|clip_placement|dilation|hemostasis|foreign_body_removal|other)$")
    anatomical_site: str | None = Field(default=None, max_length=220)
    description: str | None = Field(default=None, max_length=4000)
    technique: str | None = Field(default=None, max_length=220)
    device: str | None = Field(default=None, max_length=220)
    size: str | None = Field(default=None, max_length=80)
    count: int = Field(default=1, ge=1)
    retrieval_status: str | None = Field(default=None, max_length=60)
    complication: str | None = Field(default=None, max_length=4000)


class InterventionOut(InterventionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    activity_id: int
    created_by: int | None
    created_at: datetime


class SpecimenCreate(BaseModel):
    specimen_label: str = Field(min_length=2, max_length=160)
    anatomical_site: str = Field(min_length=2, max_length=220)
    specimen_type: str = Field(min_length=2, max_length=100)
    source_intervention_id: int
    container: str | None = Field(default=None, max_length=120)
    fixation: str | None = Field(default=None, max_length=120)
    collection_time: datetime
    notes: str | None = Field(default=None, max_length=2000)


class PathologyCaseCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=160)
    external_lab: str | None = Field(default=None, max_length=220)
    specimens: list[SpecimenCreate] = Field(min_length=1)


class SpecimenOut(SpecimenCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: int


class ReportLinkCreate(BaseModel):
    clinical_document_id: int


class PathologyStatusUpdate(BaseModel):
    target_status: str = Field(pattern="^(sent_to_lab|received_by_lab|awaiting_result|patient_notification_ready|patient_notified|closed|cancelled)$")
    external_case_number: str | None = Field(default=None, max_length=160)
    reason: str | None = Field(default=None, max_length=2000)


class PathologyCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    journey_id: int
    source_activity_id: int
    status: str
    external_lab: str | None
    external_case_number: str | None
    collected_at: datetime | None
    sent_at: datetime | None
    lab_received_at: datetime | None
    result_received_at: datetime | None
    reviewed_at: datetime | None
    reviewed_by: int | None
    patient_notified_at: datetime | None
    closed_at: datetime | None
    specimens: list[SpecimenOut]
