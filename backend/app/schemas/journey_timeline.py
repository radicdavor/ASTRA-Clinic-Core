from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TimelineItem(BaseModel):
    date: datetime
    event_type: str
    title: str
    summary: str | None = None
    source_url: str | None = None
    provenance: dict = Field(default_factory=dict)
    review_state: str | None = None
    journey_id: int


class SummaryFactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    statement: str
    fact_type: str
    source_document_id: int | None
    confidence: Decimal | None
    limitation: str | None
    review_status: str
    reviewed_by: int | None
    reviewed_at: datetime | None


class JourneySummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    journey_id: int
    provider: str
    model_name: str
    status: str
    content_json: dict
    source_refs_json: list
    limitations_json: list
    generated_at: datetime
    reviewed_by: int | None
    reviewed_at: datetime | None
    facts: list[SummaryFactOut]


class SummaryFactReview(BaseModel):
    action: str = Field(pattern="^(accept|reject)$")
