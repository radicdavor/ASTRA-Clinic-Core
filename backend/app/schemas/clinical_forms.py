from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClinicalFormDefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    form_key: str
    name: str
    specialty_key: str
    activity_kind: str
    description: str | None
    active: bool


class ClinicalFormVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    definition_id: int
    version: int
    status: str
    sections_json: list
    validation_schema_json: dict
    print_layout_json: dict
    output_document_type: str
    approved_by: int | None
    approved_at: datetime | None
    published_at: datetime | None


class ClinicalFormInstanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    activity_id: int
    form_version_id: int
    purpose: str
    status: str
    data_json: dict
    rendered_summary: str | None
    completed_by: int | None
    signed_by: int | None
    completed_at: datetime | None
    signed_at: datetime | None
    amended_from_instance_id: int | None
    binding_source: str
    resolved_at: datetime
    form_version: ClinicalFormVersionOut


class ClinicalFormDataUpdate(BaseModel):
    data: dict = Field(default_factory=dict)
