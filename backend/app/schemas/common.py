from __future__ import annotations

from datetime import date as DateType, datetime as DateTimeType, time as TimeType
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


EPISODE_STATUSES = {"open", "active", "waiting", "completed", "cancelled", "archived"}
CLINICAL_PLAN_STATUSES = {"draft", "waiting", "active", "completed", "cancelled", "archived"}
CLINICAL_PLAN_SOURCES = {"physician", "ai_suggestion", "imported"}
CLINICAL_PLAN_PRIORITIES = {"routine", "important", "urgent"}
CLINICAL_PLAN_NEXT_ACTIONS = {
    "wait_for_pathology",
    "follow_up_visit",
    "repeat_endoscopy",
    "colonoscopy",
    "gastroscopy",
    "MR_enterography",
    "CT",
    "surgery_referral",
    "continue_therapy",
    "stop_therapy",
    "episode_completed",
}
CLINICAL_DOCUMENT_SOURCE_TYPES = {"internal", "external", "scanned", "uploaded"}
CLINICAL_DOCUMENT_TYPES = {"consultation", "gastroscopy", "colonoscopy", "pathology", "laboratory", "radiology", "discharge", "referral", "other"}
CLINICAL_DOCUMENT_REVIEW_STATUSES = {"draft", "extracted", "needs_physician_review", "reviewed", "rejected", "superseded"}
CLINICAL_DOCUMENT_AI_EXTRACTION_STATUSES = {"not_run", "generated", "edited", "accepted", "rejected", "superseded"}
PATIENT_CLINICAL_SUMMARY_STATUSES = {"draft_ai", "needs_review", "reviewed", "stale", "rejected", "superseded"}
CLINICAL_READINESS_STATUSES = {
    "ready",
    "ready_with_warning",
    "not_ready",
    "needs_physician_review",
    "needs_nurse_action",
    "needs_missing_document",
    "needs_consent",
    "needs_rescheduling",
    "blocked",
}
CLINICAL_READINESS_SEVERITIES = {"info", "warning", "blocking", "critical"}


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str

    model_config = ConfigDict(json_schema_extra={"example": {"detail": "Opis greske"}})


class ReadinessCheck(BaseModel):
    key: str
    label: str
    status: str
    message: str
    count: int | None = None
    action: str | None = None
    target_path: str | None = None
    target_label: str | None = None
    decision_impact: str = "none"
    severity_reason: str | None = None


class ReadinessOut(BaseModel):
    status: str
    demo_mode: bool
    real_data_allowed: bool
    fiscalization_mode: str
    summary: dict[str, int]
    checks: list[ReadinessCheck]


class ClinicalReadinessPreviewItem(BaseModel):
    key: str
    label: str
    category: str
    status: str
    severity: str
    responsible_role: str | None = None
    source_type: str
    source_ref: str | None = None
    source_label: str | None = None
    suggested_action: str | None = None
    blocking: bool
    override_allowed: bool
    override_role: str | None = None
    override_reason_required: bool
    audit_required: bool

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in CLINICAL_READINESS_STATUSES:
            raise ValueError("Nepoznat status klinicke spremnosti")
        return value

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        if value not in CLINICAL_READINESS_SEVERITIES:
            raise ValueError("Nepoznata tezina klinicke spremnosti")
        return value


class ClinicalReadinessPreviewResponse(BaseModel):
    appointment_id: int
    patient_id: int | None
    service_id: int | None
    template_key: str | None = None
    template_label: str | None = None
    template_version: str | None = None
    template_version_warning: str | None = None
    template_binding_status: str
    template_binding_warning: str | None = None
    snapshot_supported: bool
    snapshot_status: str
    snapshot_warning: str
    status: str
    is_preview: bool
    generated_at: DateTimeType
    summary: str
    items: list[ClinicalReadinessPreviewItem]
    source_warnings: list[str]
    limitations: list[str]

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in CLINICAL_READINESS_STATUSES:
            raise ValueError("Nepoznat status klinicke spremnosti")
        return value


class ClinicalReadinessSnapshotCaptureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str
    client_preview_generated_at: DateTimeType | None = None
    idempotency_key: str | None = None

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Razlog spremanja snapshota je obavezan")
        return cleaned


class ClinicalReadinessSnapshotResponse(BaseModel):
    id: int
    appointment_id: int
    patient_id: int
    service_id: int
    created_at: DateTimeType
    created_by_user_id: int
    schema_version: str
    preview_generated_at: DateTimeType
    preview_status: str
    template_key: str | None = None
    template_label: str | None = None
    template_version: str | None = None
    template_binding_status: str | None = None
    snapshot_reason: str
    is_preview_snapshot: bool
    disclaimer: str
    items: list[dict]
    limitations: list[str]
    source_warnings: list[str]
    source_refs: list[dict]

    @field_validator("preview_status")
    @classmethod
    def validate_preview_status(cls, value: str) -> str:
        if value not in CLINICAL_READINESS_STATUSES:
            raise ValueError("Nepoznat status klinicke spremnosti")
        return value


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(json_schema_extra={"example": {"email": "admin@astra.local", "password": "astra123"}})


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str]
    expires_at: DateTimeType | None = None

    model_config = ConfigDict(json_schema_extra={"example": {"name": "AI scheduler", "scopes": ["ai.appointments.create", "ai.free_slots.read"], "expires_at": None}})


class ApiKeyCreated(ORMModel):
    id: int
    name: str
    scopes: list[str]
    active: bool
    expires_at: DateTimeType | None
    key: str


class ApiKeyOut(ORMModel):
    id: int
    name: str
    scopes: list[str]
    active: bool
    expires_at: DateTimeType | None
    last_used_at: DateTimeType | None = None
    created_at: DateTimeType
    updated_at: DateTimeType


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: DateType | None = None
    oib: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None

    @field_validator("oib")
    @classmethod
    def validate_oib(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if cleaned == "":
            return None
        if len(cleaned) != 11 or not cleaned.isdigit():
            raise ValueError("OIB mora imati tocno 11 znamenki")
        return cleaned

    model_config = ConfigDict(json_schema_extra={"example": {"first_name": "Petra", "last_name": "Novak", "date_of_birth": "1990-01-15", "oib": "12345678901", "email": "petra.novak@example.com", "phone": "+385 91 111 2222"}})


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: DateType | None = None
    oib: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None

    @field_validator("oib")
    @classmethod
    def validate_oib(cls, value: str | None) -> str | None:
        return PatientCreate.validate_oib(value)


class PatientOut(PatientCreate, ORMModel):
    id: int
    created_at: DateTimeType
    updated_at: DateTimeType


class ServiceCreate(BaseModel):
    name: str
    code: str | None = None
    duration_minutes: int = 30
    price: Decimal = Decimal("0")
    module_id: int | None = None
    active: bool = True

    model_config = ConfigDict(json_schema_extra={"example": {"name": "Gastroskopija", "code": "GASTRO", "duration_minutes": 30, "price": "120.00", "module_id": None, "active": True}})


class ServiceOut(ServiceCreate, ORMModel):
    id: int


class ClinicOut(ORMModel):
    id: int
    name: str
    active: bool
    created_at: DateTimeType
    updated_at: DateTimeType


class ProviderOut(ORMModel):
    id: int
    full_name: str
    specialty: str | None = None
    staff_role: str = "physician"
    clinic_id: int | None = None
    active: bool
    created_at: DateTimeType
    updated_at: DateTimeType
    clinic: ClinicOut | None = None


class RoomOut(ORMModel):
    id: int
    name: str
    type: str | None = None
    clinic_id: int | None = None
    active: bool
    created_at: DateTimeType
    updated_at: DateTimeType
    clinic: ClinicOut | None = None


class ClinicalEpisodeCreate(BaseModel):
    patient_id: int
    title: str
    episode_type: str = "general"
    status: str = "open"
    priority: str = "routine"
    start_date: DateType
    end_date: DateType | None = None
    summary: str | None = None
    clinical_notes: str | None = None
    owner_provider_id: int | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in EPISODE_STATUSES:
            raise ValueError("Nepoznat status epizode")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        if value not in CLINICAL_PLAN_PRIORITIES:
            raise ValueError("Nepoznat prioritet")
        return value


class ClinicalEpisodeUpdate(BaseModel):
    title: str | None = None
    episode_type: str | None = None
    status: str | None = None
    priority: str | None = None
    start_date: DateType | None = None
    end_date: DateType | None = None
    summary: str | None = None
    clinical_notes: str | None = None
    owner_provider_id: int | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in EPISODE_STATUSES:
            raise ValueError("Nepoznat status epizode")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        if value is not None and value not in CLINICAL_PLAN_PRIORITIES:
            raise ValueError("Nepoznat prioritet")
        return value


class ClinicalEpisodeOut(ClinicalEpisodeCreate, ORMModel):
    id: int
    created_by: int | None = None
    created_at: DateTimeType
    updated_at: DateTimeType
    patient: PatientOut | None = None
    owner_provider: ProviderOut | None = None
    appointment_count: int | None = None


class ClinicalPlanGenerate(BaseModel):
    appointment_id: int | None = None
    procedure_type: str | None = None
    findings: str | None = None
    pathology_ordered: bool = False
    physician_conclusion: str | None = None
    episode_goal: str | None = None


class ClinicalPlanUpdate(BaseModel):
    proposed_episode_status: str | None = None
    next_action: str | None = None
    due_date: DateType | None = None
    priority: str | None = None
    rationale: str | None = None
    suggested_follow_up: str | None = None
    physician_conclusion: str | None = None

    @field_validator("proposed_episode_status")
    @classmethod
    def validate_proposed_episode_status(cls, value: str | None) -> str | None:
        if value is not None and value not in EPISODE_STATUSES:
            raise ValueError("Nepoznat status epizode")
        return value

    @field_validator("next_action")
    @classmethod
    def validate_next_action(cls, value: str | None) -> str | None:
        if value is not None and value not in CLINICAL_PLAN_NEXT_ACTIONS:
            raise ValueError("Nepoznata sljedeca radnja")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        if value is not None and value not in CLINICAL_PLAN_PRIORITIES:
            raise ValueError("Nepoznat prioritet")
        return value


class ClinicalPlanOut(ORMModel):
    id: int
    episode_id: int
    source: str
    status: str
    proposed_episode_status: str | None = None
    next_action: str
    due_date: DateType | None = None
    priority: str
    rationale: str | None = None
    suggested_follow_up: str | None = None
    physician_conclusion: str | None = None
    ai_confidence: Decimal | None = None
    physician_confirmed: bool
    confirmed_by: int | None = None
    confirmed_at: DateTimeType | None = None
    created_at: DateTimeType
    updated_at: DateTimeType


class ClinicalDecisionTimelineItem(BaseModel):
    id: int
    action: str
    label: str
    summary: str | None = None
    source: str | None = None
    created_at: DateTimeType


class ClinicalDocumentBase(BaseModel):
    patient_id: int
    source_type: str = "uploaded"
    document_type: str = "other"
    origin: str | None = None
    document_date: DateType | None = None
    title: str
    author: str | None = None
    institution: str | None = None
    raw_text: str | None = None
    ai_summary: str | None = None
    key_findings: list[str] | None = None
    recommendations: list[str] | None = None
    attachment_path: str | None = None
    appointment_id: int | None = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        if value not in CLINICAL_DOCUMENT_SOURCE_TYPES:
            raise ValueError("Nepoznat izvor dokumenta")
        return value

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str) -> str:
        if value not in CLINICAL_DOCUMENT_TYPES:
            raise ValueError("Nepoznat tip dokumenta")
        return value


class ClinicalDocumentCreate(ClinicalDocumentBase):
    pass


class ClinicalDocumentUpload(BaseModel):
    patient_id: int
    title: str
    source_type: str = "uploaded"
    document_type: str = "other"
    origin: str | None = "Uploaded by patient"
    document_date: DateType | None = None
    author: str | None = None
    institution: str | None = None
    raw_text: str | None = None
    attachment_name: str | None = None
    appointment_id: int | None = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        return ClinicalDocumentBase.validate_source_type(value)

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str) -> str:
        return ClinicalDocumentBase.validate_document_type(value)


class ClinicalDocumentUpdate(BaseModel):
    source_type: str | None = None
    document_type: str | None = None
    origin: str | None = None
    document_date: DateType | None = None
    title: str | None = None
    author: str | None = None
    institution: str | None = None
    raw_text: str | None = None
    ai_summary: str | None = None
    key_findings: list[str] | None = None
    recommendations: list[str] | None = None
    attachment_path: str | None = None
    appointment_id: int | None = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str | None) -> str | None:
        if value is not None and value not in CLINICAL_DOCUMENT_SOURCE_TYPES:
            raise ValueError("Nepoznat izvor dokumenta")
        return value

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str | None) -> str | None:
        if value is not None and value not in CLINICAL_DOCUMENT_TYPES:
            raise ValueError("Nepoznat tip dokumenta")
        return value


class ClinicalDocumentOut(ClinicalDocumentBase, ORMModel):
    id: int
    review_status: str
    ai_extraction_status: str
    ai_extraction_generated_at: DateTimeType | None = None
    ai_extraction_updated_at: DateTimeType | None = None
    physician_reviewed: bool
    reviewed_by: int | None = None
    reviewed_at: DateTimeType | None = None
    patient: PatientOut | None = None
    created_at: DateTimeType
    updated_at: DateTimeType

    @field_validator("review_status")
    @classmethod
    def validate_review_status(cls, value: str) -> str:
        if value not in CLINICAL_DOCUMENT_REVIEW_STATUSES:
            raise ValueError("Nepoznat status pregleda dokumenta")
        return value

    @field_validator("ai_extraction_status")
    @classmethod
    def validate_ai_extraction_status(cls, value: str) -> str:
        if value not in CLINICAL_DOCUMENT_AI_EXTRACTION_STATUSES:
            raise ValueError("Nepoznat status AI ekstrakcije")
        return value


class ClinicalEvidenceTimelineItem(BaseModel):
    id: int
    action: str
    object_type: str
    object_id: int | None = None
    message: str | None = None
    actor_type: str | None = None
    actor_user_id: int | None = None
    actor_api_key_id: int | None = None
    created_at: DateTimeType
    clinical_event_category: str
    clinical_event_label: str
    knowledge_impact: str
    is_clinical_evidence_event: bool


class PatientKnowledgeSource(BaseModel):
    document_id: int
    title: str
    document_type: str
    source_type: str
    origin: str | None = None
    document_date: DateType | None = None


class PatientKnowledgeItem(BaseModel):
    text: str
    sources: list[PatientKnowledgeSource]
    display_kind: str | None = None
    severity: str | None = None
    requires_attention: bool = False


class PatientClinicalSummaryRecordUpdate(BaseModel):
    summary_text: str | None = None
    known_conditions: list[str] | None = None
    key_findings: list[str] | None = None
    open_items: list[str] | None = None
    risks: list[str] | None = None
    last_recommendations: list[str] | None = None
    source_document_ids: list[int] | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in PATIENT_CLINICAL_SUMMARY_STATUSES:
            raise ValueError("Nepoznat status klinickog sazetka")
        return value


class PatientClinicalSummaryRecordOut(ORMModel):
    id: int
    patient_id: int
    summary_text: str | None = None
    known_conditions: list[str] | None = None
    key_findings: list[str] | None = None
    open_items: list[str] | None = None
    risks: list[str] | None = None
    last_recommendations: list[str] | None = None
    source_document_ids: list[int] | None = None
    status: str
    generated_by: str | None = None
    reviewed_by: int | None = None
    reviewed_at: DateTimeType | None = None
    created_at: DateTimeType
    updated_at: DateTimeType

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in PATIENT_CLINICAL_SUMMARY_STATUSES:
            raise ValueError("Nepoznat status klinickog sazetka")
        return value


class PatientClinicalSummary(BaseModel):
    patient_id: int
    generated_from_reviewed_documents: int
    awaiting_review_count: int
    reviewed_summary: PatientClinicalSummaryRecordOut | None = None
    draft_summary: PatientClinicalSummaryRecordOut | None = None
    reviewed_summary_is_stale: bool = False
    draft_summary_is_stale: bool = False
    latest_reviewed_document_updated_at: DateTimeType | None = None
    reviewed_summary_updated_at: DateTimeType | None = None
    summary_warning: str | None = None
    known_problems: list[PatientKnowledgeItem]
    completed_procedures: list[PatientKnowledgeItem]
    pathology: list[PatientKnowledgeItem]
    laboratory: list[PatientKnowledgeItem]
    imaging: list[PatientKnowledgeItem]
    current_therapy: list[PatientKnowledgeItem]
    open_questions: list[PatientKnowledgeItem]
    latest_recommendations: list[PatientKnowledgeItem]


class AppointmentCreate(BaseModel):
    patient_id: int
    service_id: int
    provider_id: int
    room_id: int
    episode_id: int | None = None
    date: DateType
    start_time: TimeType
    end_time: TimeType
    duration_minutes: int
    status: str = "scheduled"
    source: str = "manual"
    notes: str | None = None

    model_config = ConfigDict(json_schema_extra={"example": {"patient_id": 1, "service_id": 1, "provider_id": 1, "room_id": 1, "date": "2026-07-05", "start_time": "09:00", "end_time": "09:30", "duration_minutes": 30, "status": "scheduled", "source": "manual", "notes": "Kontrolni termin"}})


class AppointmentUpdate(BaseModel):
    patient_id: int | None = None
    service_id: int | None = None
    provider_id: int | None = None
    room_id: int | None = None
    episode_id: int | None = None
    date: DateType | None = None
    start_time: TimeType | None = None
    end_time: TimeType | None = None
    duration_minutes: int | None = None
    status: str | None = None
    source: str | None = None
    notes: str | None = None


class AppointmentOut(AppointmentCreate, ORMModel):
    id: int
    arrived_at: DateTimeType | None = None
    identity_verified_at: DateTimeType | None = None
    identity_verified_by: int | None = None
    created_at: DateTimeType
    updated_at: DateTimeType
    patient: PatientOut | None = None
    service: ServiceOut | None = None
    provider: ProviderOut | None = None
    room: RoomOut | None = None
    episode: ClinicalEpisodeOut | None = None


class ReceptionPatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: DateType | None = None
    oib: str | None = None
    phone: str | None = None
    email: EmailStr | None = None

    @field_validator("oib")
    @classmethod
    def validate_oib(cls, value: str | None) -> str | None:
        return PatientCreate.validate_oib(value)


class ReceptionArrivalRequest(BaseModel):
    patient: ReceptionPatientUpdate | None = None
    identity_verified: bool = True


class ReceptionSlot(BaseModel):
    time: str
    appointment: AppointmentOut | None = None
    span: int = 1
    empty: bool = True


class SupplierCreate(BaseModel):
    name: str
    contact_person: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    vat_id: str | None = None
    notes: str | None = None


class SupplierOut(SupplierCreate, ORMModel):
    id: int
    created_at: DateTimeType
    updated_at: DateTimeType


class InventoryItemCreate(BaseModel):
    sku: str
    name: str
    category: str | None = None
    unit_of_measure: str = "kom"
    supplier_id: int | None = None
    current_stock: Decimal = Decimal("0")
    minimum_stock: Decimal = Decimal("0")
    reorder_point: Decimal = Decimal("0")
    purchase_price: Decimal = Decimal("0")
    selling_price: Decimal = Decimal("0")
    expiration_tracking_enabled: bool = False
    lot_tracking_enabled: bool = False
    active: bool = True


class InventoryItemOut(InventoryItemCreate, ORMModel):
    id: int
    created_at: DateTimeType
    updated_at: DateTimeType


class InventoryBatchCreate(BaseModel):
    inventory_item_id: int
    lot_number: str | None = None
    expiration_date: DateType | None = None
    quantity: Decimal
    location_id: int
    purchase_price: Decimal = Decimal("0")
    supplier_id: int | None = None


class InventoryBatchOut(InventoryBatchCreate, ORMModel):
    id: int
    created_at: DateTimeType
    updated_at: DateTimeType


class StockMovementCreate(BaseModel):
    inventory_item_id: int
    batch_id: int | None = None
    from_location_id: int | None = None
    to_location_id: int | None = None
    quantity: Decimal
    movement_type: str
    reason: str | None = None
    related_appointment_id: int | None = None
    related_invoice_id: int | None = None


class StockMovementOut(StockMovementCreate, ORMModel):
    id: int
    created_by: int | None = None
    created_at: DateTimeType


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    status: str = "draft"
    order_date: DateType | None = None
    expected_delivery_date: DateType | None = None
    total_amount: Decimal = Decimal("0")
    notes: str | None = None


class PurchaseOrderLineCreate(BaseModel):
    inventory_item_id: int
    quantity_ordered: Decimal
    unit_price: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("25")


class PurchaseOrderLineUpdate(BaseModel):
    inventory_item_id: int | None = None
    quantity_ordered: Decimal | None = None
    unit_price: Decimal | None = None
    vat_rate: Decimal | None = None


class PurchaseOrderReceiveLine(BaseModel):
    purchase_order_line_id: int
    quantity_received: Decimal
    lot_number: str | None = None
    expiration_date: DateType | None = None
    location_id: int
    purchase_price: Decimal | None = None


class PurchaseOrderReceiveRequest(BaseModel):
    lines: list[PurchaseOrderReceiveLine]


class PurchaseOrderLineOut(PurchaseOrderLineCreate, ORMModel):
    id: int
    purchase_order_id: int
    quantity_received: Decimal


class PurchaseOrderOut(PurchaseOrderCreate, ORMModel):
    id: int
    created_at: DateTimeType
    updated_at: DateTimeType
    lines: list[PurchaseOrderLineOut] = []


class InvoiceCreate(BaseModel):
    patient_id: int
    appointment_id: int | None = None
    invoice_number: str | None = None
    invoice_date: DateType | None = None
    status: str = "draft"
    total_amount: Decimal = Decimal("0")
    payment_status: str = "unpaid"
    payment_method: str | None = None
    operator: str | None = None
    business_unit: str | None = None
    register_id: str | None = None
    vat_id: str | None = None
    fiscalization_status: str | None = "not_applicable"
    fiscalization_provider: str | None = None
    fiscalization_reference: str | None = None
    fiscalization_message: str | None = None
    fiscalized_at: DateTimeType | None = None
    notes: str | None = None


class InvoiceLineCreate(BaseModel):
    service_id: int | None = None
    inventory_item_id: int | None = None
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("25")


class InvoiceLineUpdate(BaseModel):
    service_id: int | None = None
    inventory_item_id: int | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    vat_rate: Decimal | None = None


class PaymentTransactionCreate(BaseModel):
    amount: Decimal
    method: str
    reference: str | None = None
    paid_at: DateTimeType | None = None


class AppointmentMaterialConsumptionLine(BaseModel):
    inventory_item_id: int
    quantity: Decimal
    reason: str | None = None


class AppointmentMaterialConsumptionRequest(BaseModel):
    lines: list[AppointmentMaterialConsumptionLine] | None = None
    allow_missing_optional: bool = True


class InvoiceLineOut(InvoiceLineCreate, ORMModel):
    id: int
    invoice_id: int
    total: Decimal


class PaymentTransactionOut(PaymentTransactionCreate, ORMModel):
    id: int
    invoice_id: int
    created_by: int | None = None


class InvoiceOut(InvoiceCreate, ORMModel):
    id: int
    created_at: DateTimeType
    updated_at: DateTimeType
    lines: list[InvoiceLineOut] = []
    payments: list[PaymentTransactionOut] = []


class InvoiceIssueOut(InvoiceOut):
    pass


class ServiceMaterialCreate(BaseModel):
    inventory_item_id: int
    default_quantity: Decimal = Decimal("1")
    required: bool = True
    variable_quantity_allowed: bool = False
    notes: str | None = None
