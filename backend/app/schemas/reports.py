from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SignedReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    form_instance_id: int
    form_version_id: int
    clinical_document_id: int
    activity_id: int
    journey_id: int
    patient_id: int
    document_type: str
    title: str
    structured_data_json: dict
    rendered_content: str
    version_number: int
    signer_user_id: int
    signer_name: str
    signed_at: datetime
    supersedes_report_id: int | None
    superseded_at: datetime | None
    content_hash: str
    hash_algorithm: str


class ReportDeliveryRequest(BaseModel):
    report_ids: list[int] = Field(min_length=1)
    recipient: str = Field(min_length=5, max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    channel: str = Field(default="email", pattern="^email$")
    acknowledge_superseded: bool = False
    recipient_source: str = Field(default="patient_verified", pattern="^(patient_verified|alternate)$")
    alternate_recipient_reason: str | None = Field(default=None, max_length=1000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)


class ReportDeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: int
    channel: str
    recipient: str
    status: str
    provider_mode: str
    initiated_by: int
    approved_by: int
    queued_at: datetime
    sent_at: datetime | None
    delivered_at: datetime | None
    failure_reason: str | None
    correlation_id: str
    recipient_source: str
    alternate_recipient_reason: str | None


class ReportPrintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: int
    printed_by: int
    printed_at: datetime
    request_id: str | None


class VisitDocumentOut(BaseModel):
    report: SignedReportOut
    print_count: int
    latest_delivery: ReportDeliveryOut | None
