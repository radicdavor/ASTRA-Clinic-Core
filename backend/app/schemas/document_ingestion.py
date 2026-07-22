from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DocumentIngestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    journey_id: int | None
    clinical_episode_id: int | None
    title: str
    document_type: str
    upload_channel: str | None
    original_filename: str | None
    mime_type: str | None
    checksum_sha256: str | None
    file_size_bytes: int | None
    lifecycle_status: str
    ocr_text: str | None
    extraction_confidence: Decimal | None
    classification_confidence: Decimal | None
    received_at: datetime | None
    review_status: str
    is_clinical_record: bool
    record_classification: str


class DocumentJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinical_document_id: int
    job_type: str
    provider: str
    status: str
    attempts: int
    error_message: str | None
    result_metadata_json: dict | None
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
