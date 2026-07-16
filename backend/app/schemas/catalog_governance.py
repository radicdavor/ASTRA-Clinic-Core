from datetime import date, time

from pydantic import BaseModel, Field


class PackageCreate(BaseModel):
    package_key: str = Field(min_length=3, max_length=100, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=3, max_length=180)
    description: str | None = Field(default=None, max_length=2000)
    specialty_key: str = Field(min_length=2, max_length=80)


class PackageItemCreate(BaseModel):
    service_id: int
    activity_key: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9_-]+$")
    activity_kind: str = Field(min_length=2, max_length=60)
    specialty_key: str = Field(min_length=2, max_length=80)
    sequence: int = Field(ge=1)
    required: bool = True
    relative_start_offset_minutes: int = Field(default=0, ge=0)
    default_duration_minutes: int = Field(ge=10, le=480)
    preferred_clinic_id: int | None = None
    preferred_room_type: str | None = Field(default=None, max_length=80)
    form_binding_override_version_id: int | None = None
    preparation_requirements_json: list = Field(default_factory=list)
    billing_inclusion_rule: str = Field(default="include", pattern="^(include|exclude)$")


class PackageVersionCreate(BaseModel):
    items: list[PackageItemCreate] = Field(min_length=1)


class PackageActivityAssignment(BaseModel):
    package_item_id: int
    date: date
    start_time: time
    end_time: time
    provider_id: int
    room_id: int


class PackageMaterializeRequest(BaseModel):
    assignments: list[PackageActivityAssignment] = Field(min_length=1)


class FormDefinitionCreate(BaseModel):
    form_key: str = Field(min_length=3, max_length=100, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=3, max_length=180)
    specialty_key: str = Field(min_length=2, max_length=80)
    activity_kind: str = Field(min_length=2, max_length=60)
    description: str | None = Field(default=None, max_length=2000)
    sections_json: list
    validation_schema_json: dict = Field(default_factory=dict)
    print_layout_json: dict = Field(default_factory=dict)
    output_document_type: str = Field(min_length=3, max_length=80)


class FormVersionDraftCreate(BaseModel):
    sections_json: list | None = None
    validation_schema_json: dict | None = None
    print_layout_json: dict | None = None
    output_document_type: str | None = Field(default=None, min_length=3, max_length=80)


class FormBindingCreate(BaseModel):
    form_version_id: int
    service_id: int | None = None
    clinic_id: int | None = None
    specialty_key: str | None = None
    activity_kind: str | None = None
