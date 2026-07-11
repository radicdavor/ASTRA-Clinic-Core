from __future__ import annotations

from datetime import date as DateType, datetime as DateTimeType, time as TimeType
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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
CLINICAL_READINESS_ADVISORY_SIGNAL_SEVERITIES = {"info", "warning", "review_required", "missing_input"}
CLINICAL_READINESS_ADVISORY_SIGNAL_CATEGORIES = {
    "documentation",
    "medication",
    "consent",
    "logistics",
    "clinical_review",
    "source_warning",
    "other",
}
CLINICAL_FINDING_LIFECYCLE_STATUSES = {
    "received",
    "linked_to_patient",
    "awaiting_review",
    "review_in_progress",
    "reviewed",
    "needs_clinician_decision",
    "decision_documented",
    "follow_up_recommended",
    "external_referral_recommended",
    "closed_for_now",
}
CLINICAL_FINDING_CATEGORIES = {
    "documentation",
    "laboratory",
    "pathology",
    "endoscopy",
    "radiology",
    "medication",
    "clinical_history",
    "open_question",
    "readiness_context",
    "other",
}
CLINICAL_FINDING_SOURCE_TYPES = {
    "clinical_document",
    "patient_clinical_summary",
    "manual_review",
    "clinical_readiness_preview",
    "external_report",
    "other",
}
CLINICAL_FINDING_EXTRACTION_CONFIDENCE_LABELS = {"unknown", "low", "medium", "high"}
CLINICAL_FINDING_EXTRACTION_SUGGESTED_STATUSES = {"received", "awaiting_review"}
CLINICAL_OPEN_QUESTION_STATUSES = {
    "draft",
    "suggested",
    "awaiting_review",
    "under_review",
    "needs_clinician_decision",
    "decision_documented",
    "deferred",
    "closed_for_now",
}
CLINICAL_REVIEW_STATUSES = {
    "not_started",
    "awaiting_review",
    "in_review",
    "reviewed",
    "needs_clinician_decision",
    "decision_documented",
    "deferred",
    "closed_for_now",
}
CLINICAL_REVIEW_OBJECT_TYPES = {
    "clinical_document",
    "finding",
    "open_question",
    "extraction_candidate",
    "source_evidence",
}
CLINICAL_EVIDENCE_TIMELINE_EVENT_TYPES = {
    "clinical_document_received",
    "clinical_document_review_pending",
    "finding_recorded",
    "finding_requires_review",
    "open_question_suggested",
    "open_question_awaiting_review",
    "extraction_candidate_generated",
    "review_pending",
    "review_completed",
    "readiness_snapshot_captured",
    "readiness_snapshot_superseded",
    "acknowledgment_recorded",
    "access_audit_recorded",
}
CLINICAL_EVIDENCE_TIMELINE_SOURCE_TYPES = {
    "clinical_document",
    "clinical_finding",
    "clinical_open_question",
    "extraction_candidate",
    "clinical_review",
    "readiness_snapshot",
    "acknowledgment",
    "access_audit",
}


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


class ClinicalReadinessAdvisorySignal(BaseModel):
    signal_key: str
    label: str
    severity: str
    category: str
    source_type: str
    source_reference: str | None = None
    explanation: str
    limitations: list[str] = []
    created_at: DateTimeType
    is_decision: bool = False
    not_decision_disclaimer: str = "Advisory signal je neblokirajuci signal za ljudski pregled, nije klinicka odluka."

    @field_validator("severity")
    @classmethod
    def validate_advisory_severity(cls, value: str) -> str:
        if value not in CLINICAL_READINESS_ADVISORY_SIGNAL_SEVERITIES:
            raise ValueError("Nepoznata tezina advisory signala")
        return value

    @field_validator("category")
    @classmethod
    def validate_advisory_category(cls, value: str) -> str:
        if value not in CLINICAL_READINESS_ADVISORY_SIGNAL_CATEGORIES:
            raise ValueError("Nepoznata kategorija advisory signala")
        return value

    @field_validator("is_decision")
    @classmethod
    def validate_not_decision(cls, value: bool) -> bool:
        if value:
            raise ValueError("Advisory signal ne smije biti klinicka odluka")
        return value


class ClinicalFindingSourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_id: int | None = None
    source_label: str
    source_reference: str | None = None
    source_date: DateType | None = None
    reviewed: bool = False
    extraction_method: str | None = None
    limitations: list[str] = Field(default_factory=list)

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_SOURCE_TYPES:
            raise ValueError("Nepoznat source type za finding")
        return value


class ClinicalFindingPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_key: str
    label: str
    category: str
    status: str
    source_reference: ClinicalFindingSourceReference
    limitations: list[str] = Field(default_factory=lambda: ["Finding je source-linked context za review, nije klinicka odluka."])
    requires_review: bool = True
    created_at: DateTimeType
    not_decision_disclaimer: str = "Finding nije automatska dijagnoza, treatment plan, Task, Outcome Evidence ili patient message."

    @field_validator("finding_key", "label")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Finding polje ne smije biti prazno")
        return cleaned

    @field_validator("category")
    @classmethod
    def validate_finding_category(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_CATEGORIES:
            raise ValueError("Nepoznata kategorija findinga")
        return value

    @field_validator("status")
    @classmethod
    def validate_finding_status(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_LIFECYCLE_STATUSES:
            raise ValueError("Nepoznat lifecycle status findinga")
        return value


class ClinicalFindingReadItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    finding_key: str
    patient_id: int
    source_type: str
    source_label: str
    source_reference: str
    source_document_id: int | None = None
    label: str
    category: str
    lifecycle_status: str
    requires_review: bool
    reviewed_at: DateTimeType | None = None
    reviewed_by_user_id: int | None = None
    limitations: list[str] = Field(default_factory=list)
    schema_version: str
    created_at: DateTimeType
    updated_at: DateTimeType
    safe_disclaimer: str = "Finding je source-linked zapis za ljudski pregled; nije dijagnoza, treatment plan, Task, Outcome Evidence ili patient message."

    @field_validator("finding_key", "source_type", "source_label", "source_reference", "label", "schema_version")
    @classmethod
    def validate_non_empty_read_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Finding read polje ne smije biti prazno")
        return cleaned

    @field_validator("source_type")
    @classmethod
    def validate_read_source_type(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_SOURCE_TYPES:
            raise ValueError("Nepoznat source type za finding")
        return value

    @field_validator("category")
    @classmethod
    def validate_read_category(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_CATEGORIES:
            raise ValueError("Nepoznata kategorija findinga")
        return value

    @field_validator("lifecycle_status")
    @classmethod
    def validate_read_lifecycle_status(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_LIFECYCLE_STATUSES:
            raise ValueError("Nepoznat lifecycle status findinga")
        return value


class ClinicalFindingListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int
    findings: list[ClinicalFindingReadItem]
    count: int
    is_read_only: bool = True
    warning: str = "Findings read API prikazuje source-linked zapise za ljudski pregled. Ne predstavlja dijagnozu, treatment plan, Task, Outcome Evidence, patient message, approval, clearance ili override."


class ClinicalFindingDetailResponse(ClinicalFindingReadItem):
    model_config = ConfigDict(extra="forbid")

    warning: str = "Finding detail je read-only source-linked zapis. Ne predstavlja dijagnozu, treatment plan, Task, Outcome Evidence, patient message, approval, clearance ili override."


class ClinicalFindingExtractionSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_document_id: int | None = None
    source_type: str
    source_label: str
    source_reference: str
    text_span_reference: str | None = None
    page_reference: str | None = None
    section_reference: str | None = None
    source_date: DateType | None = None
    source_author: str | None = None
    source_institution: str | None = None
    extraction_method: str = "contract_only"
    extracted_at: DateTimeType
    limitations: list[str] = Field(default_factory=lambda: ["Extraction source is traceability metadata, not clinical truth."])

    @field_validator("source_type")
    @classmethod
    def validate_extraction_source_type(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_SOURCE_TYPES:
            raise ValueError("Nepoznat source type za extraction candidate")
        return value

    @field_validator("source_label", "source_reference", "extraction_method")
    @classmethod
    def validate_extraction_source_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Extraction source polje ne smije biti prazno")
        return cleaned


class ClinicalFindingExtractionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_key: str
    label: str
    category: str
    source: ClinicalFindingExtractionSource
    confidence_label: str = "unknown"
    limitations: list[str] = Field(default_factory=lambda: ["Candidate finding requires human review and is not persisted clinical truth."])
    requires_human_review: bool = True
    suggested_lifecycle_status: str = "awaiting_review"
    created_at: DateTimeType
    is_persisted: bool = False
    not_decision_disclaimer: str = "Extraction candidate nije dijagnoza, preporuka, physician decision, patient instruction, Task, Outcome Evidence ili patient message."

    @field_validator("candidate_key", "label")
    @classmethod
    def validate_candidate_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Extraction candidate polje ne smije biti prazno")
        return cleaned

    @field_validator("category")
    @classmethod
    def validate_candidate_category(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_CATEGORIES:
            raise ValueError("Nepoznata kategorija extraction candidatea")
        return value

    @field_validator("confidence_label")
    @classmethod
    def validate_confidence_label(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_EXTRACTION_CONFIDENCE_LABELS:
            raise ValueError("Nepoznat confidence label za extraction candidate")
        return value

    @field_validator("suggested_lifecycle_status")
    @classmethod
    def validate_suggested_lifecycle_status(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_EXTRACTION_SUGGESTED_STATUSES:
            raise ValueError("Extraction candidate smije predloziti samo review-needed status")
        return value

    @field_validator("requires_human_review")
    @classmethod
    def validate_requires_human_review(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Extraction candidate mora zahtijevati human review")
        return value

    @field_validator("is_persisted")
    @classmethod
    def validate_not_persisted(cls, value: bool) -> bool:
        if value:
            raise ValueError("Extraction candidate ne smije implicirati persisted finding")
        return value


class ClinicalFindingExtractionBatchPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clinical_document_id: int
    patient_id: int
    candidates: list[ClinicalFindingExtractionCandidate]
    is_runtime_extraction: bool = False
    warning: str = "Extraction batch preview je pasivni contract shape; ne pokrece OCR/AI, ne sprema findings i ne stvara klinicke odluke."

    @field_validator("is_runtime_extraction")
    @classmethod
    def validate_not_runtime_extraction(cls, value: bool) -> bool:
        if value:
            raise ValueError("Extraction batch preview ne smije biti runtime extraction")
        return value


class ClinicalOpenQuestionSourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_label: str
    source_reference: str
    source_document_id: int | None = None
    source_finding_key: str | None = None
    extraction_candidate_key: str | None = None
    confidence_label: str = "unknown"
    limitations: list[str] = Field(default_factory=lambda: ["Open question source requires human interpretation."])

    @field_validator("source_type")
    @classmethod
    def validate_open_question_source_type(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_SOURCE_TYPES:
            raise ValueError("Nepoznat source type za open question")
        return value

    @field_validator("source_label", "source_reference")
    @classmethod
    def validate_open_question_source_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Open question source polje ne smije biti prazno")
        return cleaned

    @field_validator("confidence_label")
    @classmethod
    def validate_open_question_confidence(cls, value: str) -> str:
        if value not in CLINICAL_FINDING_EXTRACTION_CONFIDENCE_LABELS:
            raise ValueError("Nepoznat confidence label za open question")
        return value


class ClinicalOpenQuestionPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_key: str
    label: str
    status: str = "awaiting_review"
    source_reference: ClinicalOpenQuestionSourceReference
    linked_finding_key: str
    limitations: list[str] = Field(default_factory=lambda: ["Open question je source-linked pitanje za ljudsku interpretaciju, nije klinicka odluka."])
    requires_clinician_review: bool = True
    created_at: DateTimeType
    is_persisted: bool = False
    not_decision_disclaimer: str = "Open question nije Task, Outcome Evidence, dijagnoza, preporuka, physician decision ili patient message."

    @field_validator("question_key", "label", "linked_finding_key")
    @classmethod
    def validate_open_question_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Open question polje ne smije biti prazno")
        return cleaned

    @field_validator("status")
    @classmethod
    def validate_open_question_status(cls, value: str) -> str:
        if value not in CLINICAL_OPEN_QUESTION_STATUSES:
            raise ValueError("Nepoznat open question status")
        return value

    @field_validator("requires_clinician_review")
    @classmethod
    def validate_requires_clinician_review(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Open question mora zahtijevati clinician review")
        return value

    @field_validator("is_persisted")
    @classmethod
    def validate_open_question_not_persisted(cls, value: bool) -> bool:
        if value:
            raise ValueError("Open question preview ne smije implicirati persistence")
        return value


class ClinicalOpenQuestionReadItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    question_key: str
    patient_id: int
    finding_id: int | None = None
    source_type: str
    source_label: str
    source_reference_summary: str
    label: str
    status: str
    requires_clinician_review: bool
    reviewed_at: DateTimeType | None = None
    reviewed_by_user_id: int | None = None
    limitations: list[str] = Field(default_factory=list)
    created_at: DateTimeType
    updated_at: DateTimeType
    no_decision_disclaimer: str = "Open question je source-linked pitanje za ljudsku interpretaciju, nije klinicka odluka."

    @field_validator("question_key", "source_type", "source_label", "source_reference_summary", "label")
    @classmethod
    def validate_open_question_read_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Open question read polje ne smije biti prazno")
        return cleaned

    @field_validator("status")
    @classmethod
    def validate_open_question_read_status(cls, value: str) -> str:
        if value not in CLINICAL_OPEN_QUESTION_STATUSES:
            raise ValueError("Nepoznat open question read status")
        return value

    @field_validator("requires_clinician_review")
    @classmethod
    def validate_open_question_read_review_requirement(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Open question read response mora zahtijevati clinician review")
        return value


class ClinicalOpenQuestionDetail(ClinicalOpenQuestionReadItem):
    source_reference: str
    linked_finding_key: str | None = None
    review_note: str | None = None

    @field_validator("source_reference")
    @classmethod
    def validate_open_question_detail_source_reference(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Open question detail source reference ne smije biti prazan")
        return cleaned


class ClinicalOpenQuestionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int
    questions: list[ClinicalOpenQuestionReadItem]
    count: int
    is_read_only: bool = True
    warning: str = "Open questions read API prikazuje source-linked pitanja za ljudsku interpretaciju. Ne predstavlja dijagnozu, treatment plan, Task, Outcome Evidence, patient message, approval, clearance ili override."


class ClinicalOpenQuestionDetailResponse(ClinicalOpenQuestionDetail):
    model_config = ConfigDict(extra="forbid")

    warning: str = "Open question detail je read-only source-linked pitanje. Ne predstavlja dijagnozu, treatment plan, Task, Outcome Evidence, patient message, approval, clearance ili override."


class ClinicalReviewSourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_label: str
    source_reference: str
    reviewed_object_type: str
    reviewed_object_reference: str
    limitations: list[str] = Field(default_factory=lambda: ["Review source requires human interpretation and is not a clinical decision."])

    @field_validator("source_type", "source_label", "source_reference", "reviewed_object_reference")
    @classmethod
    def validate_review_source_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Review source polje ne smije biti prazno")
        return cleaned

    @field_validator("reviewed_object_type")
    @classmethod
    def validate_review_object_type(cls, value: str) -> str:
        if value not in CLINICAL_REVIEW_OBJECT_TYPES:
            raise ValueError("Nepoznat review object type")
        return value


class ClinicalReviewPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_key: str
    reviewed_object_type: str
    reviewed_object_reference: str
    status: str
    source_reference: ClinicalReviewSourceReference
    limitations: list[str] = Field(default_factory=lambda: ["Review je ljudski pregled source-linked konteksta; nije odluka."])
    requires_clinician_decision: bool = True
    created_at: DateTimeType
    is_persisted: bool = False
    no_decision_disclaimer: str = "Review nije approval, clearance, override, diagnosis, treatment plan, Task, Outcome Evidence ili patient message."

    @field_validator("review_key", "reviewed_object_reference")
    @classmethod
    def validate_review_preview_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Review preview polje ne smije biti prazno")
        return cleaned

    @field_validator("reviewed_object_type")
    @classmethod
    def validate_preview_object_type(cls, value: str) -> str:
        if value not in CLINICAL_REVIEW_OBJECT_TYPES:
            raise ValueError("Nepoznat review object type")
        return value

    @field_validator("status")
    @classmethod
    def validate_review_status(cls, value: str) -> str:
        if value not in CLINICAL_REVIEW_STATUSES:
            raise ValueError("Nepoznat review status")
        return value

    @field_validator("requires_clinician_decision")
    @classmethod
    def validate_review_requires_clinician_decision(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Review preview mora zadrzati clinician decision boundary")
        return value

    @field_validator("is_persisted")
    @classmethod
    def validate_review_not_persisted(cls, value: bool) -> bool:
        if value:
            raise ValueError("Review preview ne smije implicirati persistence")
        return value


class ClinicalEvidenceTimelineSourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_object_type: str
    source_object_reference: str
    patient_id: int
    source_label: str
    provenance_label: str
    source_document_reference: str | None = None
    limitations: list[str] = Field(default_factory=lambda: ["Timeline event requires source traceability and human interpretation."])

    @field_validator("source_object_type")
    @classmethod
    def validate_timeline_source_type(cls, value: str) -> str:
        if value not in CLINICAL_EVIDENCE_TIMELINE_SOURCE_TYPES:
            raise ValueError("Nepoznat timeline source object type")
        return value

    @field_validator("source_object_reference", "source_label", "provenance_label")
    @classmethod
    def validate_timeline_source_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Timeline source polje ne smije biti prazno")
        return cleaned


class ClinicalEvidenceTimelineEventPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_key: str
    event_type: str
    label: str
    source_reference: ClinicalEvidenceTimelineSourceReference
    event_timestamp: DateTimeType
    display_timestamp: DateTimeType
    limitations: list[str] = Field(default_factory=lambda: ["Timeline event je source-linked kontekst; nije klinicka odluka."])
    requires_review: bool = False
    is_decision: bool = False
    created_at: DateTimeType
    no_decision_disclaimer: str = "Timeline event nije diagnosis, treatment plan, Task, Outcome Evidence, patient message, approval, clearance ili override."

    @field_validator("event_key", "label")
    @classmethod
    def validate_timeline_event_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Timeline event polje ne smije biti prazno")
        return cleaned

    @field_validator("event_type")
    @classmethod
    def validate_timeline_event_type(cls, value: str) -> str:
        if value not in CLINICAL_EVIDENCE_TIMELINE_EVENT_TYPES:
            raise ValueError("Nepoznat timeline event type")
        return value

    @field_validator("is_decision")
    @classmethod
    def validate_timeline_not_decision(cls, value: bool) -> bool:
        if value:
            raise ValueError("Timeline event ne smije biti clinical decision")
        return value


class ClinicalEvidenceTimelineListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int
    events: list[ClinicalEvidenceTimelineEventPreview]
    count: int
    is_read_only: bool = True
    warning: str = "Clinical Evidence Timeline je read-only source-linked prikaz; nije diagnosis, treatment plan, Task, Outcome Evidence, patient message, approval, clearance ili override."


class ClinicalReadinessReviewAcknowledgment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acknowledgment_key: str
    advisory_signal_key: str
    snapshot_id: int | None = None
    appointment_id: int
    patient_id: int
    actor_role: str
    reason: str
    created_at: DateTimeType
    limitations: list[str] = Field(default_factory=lambda: ["Human review acknowledgment nije klinicka odluka."])
    is_decision: bool = False
    is_clearance: bool = False
    is_override: bool = False
    not_decision_disclaimer: str = "Acknowledgment znaci da je covjek pregledao signal; ne znaci odobrenje, clearance ili override."

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Razlog pregleda signala je obavezan")
        return cleaned

    @field_validator("is_decision", "is_clearance", "is_override")
    @classmethod
    def validate_false_safety_flags(cls, value: bool) -> bool:
        if value:
            raise ValueError("Acknowledgment ne smije biti odluka, clearance ili override")
        return value


class ClinicalReadinessReviewAcknowledgmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    advisory_signal_key: str
    snapshot_id: int | None = None
    reason: str
    client_context_key: str | None = None
    idempotency_key: str | None = None

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Razlog pregleda signala je obavezan")
        return cleaned


class ClinicalReadinessReviewAcknowledgmentResponse(BaseModel):
    acknowledgment_key: str
    advisory_signal_key: str
    snapshot_id: int | None = None
    appointment_id: int
    patient_id: int
    actor_role: str
    reason: str
    created_at: DateTimeType
    limitations: list[str] = Field(default_factory=lambda: ["Acknowledgment je zapis ljudskog pregleda signala, nije klinicka odluka."])
    warning: str = "Acknowledgment ne predstavlja clinical approval, readiness clearance, override, Outcome Evidence ili dozvolu za postupak."
    is_decision: bool = False
    is_clearance: bool = False
    is_override: bool = False

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Razlog pregleda signala je obavezan")
        return cleaned

    @field_validator("is_decision", "is_clearance", "is_override")
    @classmethod
    def validate_false_safety_flags(cls, value: bool) -> bool:
        if value:
            raise ValueError("Acknowledgment response ne smije biti odluka, clearance ili override")
        return value


class ClinicalReadinessAcknowledgmentReadItem(BaseModel):
    id: int
    acknowledgment_key: str
    appointment_id: int
    patient_id: int
    advisory_signal_key: str
    snapshot_id: int | None = None
    actor_user_id: int
    actor_role: str
    reason: str
    limitations: list[str]
    schema_version: str
    created_at: DateTimeType
    safe_disclaimer: str
    is_decision: bool = False
    is_clearance: bool = False
    is_override: bool = False

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Razlog pregleda signala je obavezan")
        return cleaned

    @field_validator("is_decision", "is_clearance", "is_override")
    @classmethod
    def validate_false_safety_flags(cls, value: bool) -> bool:
        if value:
            raise ValueError("Acknowledgment read response ne smije biti odluka, clearance ili override")
        return value


class ClinicalReadinessAcknowledgmentListResponse(BaseModel):
    appointment_id: int
    acknowledgments: list[ClinicalReadinessAcknowledgmentReadItem]
    count: int
    is_read_only: bool
    warning: str


class ClinicalReadinessAcknowledgmentDetailResponse(ClinicalReadinessAcknowledgmentReadItem):
    warning: str


class ClinicalReadinessSnapshotHistoryItem(BaseModel):
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
    item_count: int
    limitation_count: int
    source_warning_count: int
    superseded_by_snapshot_id: int | None = None
    superseded_at: DateTimeType | None = None
    superseded_reason: str | None = None

    @field_validator("preview_status")
    @classmethod
    def validate_preview_status(cls, value: str) -> str:
        if value not in CLINICAL_READINESS_STATUSES:
            raise ValueError("Nepoznat status klinicke spremnosti")
        return value


class ClinicalReadinessSnapshotHistoryResponse(BaseModel):
    appointment_id: int
    snapshots: list[ClinicalReadinessSnapshotHistoryItem]
    count: int
    is_preview_history: bool
    warning: str


class ClinicalReadinessSnapshotDetailResponse(BaseModel):
    id: int
    appointment_id: int
    patient_id: int
    service_id: int
    created_at: DateTimeType
    created_by_user_id: int
    schema_version: str
    preview_generated_at: DateTimeType
    preview_status: str
    preview_summary: str
    template_key: str | None = None
    template_label: str | None = None
    template_version: str | None = None
    template_binding_status: str | None = None
    template_binding_warning: str | None = None
    snapshot_reason: str
    is_preview_snapshot: bool
    disclaimer: str
    items: list[dict]
    limitations: list[str]
    source_warnings: list[str]
    source_refs: list[dict]
    superseded_by_snapshot_id: int | None = None
    superseded_at: DateTimeType | None = None
    superseded_reason: str | None = None
    warning: str

    @field_validator("preview_status")
    @classmethod
    def validate_preview_status(cls, value: str) -> str:
        if value not in CLINICAL_READINESS_STATUSES:
            raise ValueError("Nepoznat status klinicke spremnosti")
        return value


class ClinicalReadinessSnapshotSupersedeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Razlog zamjene snapshota je obavezan")
        return cleaned


class ClinicalReadinessSnapshotSupersedeResponse(BaseModel):
    old_snapshot_id: int
    new_snapshot: ClinicalReadinessSnapshotResponse
    superseded_at: DateTimeType
    superseded_reason: str
    warning: str


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


class ClinicCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class ProviderOut(ORMModel):
    id: int
    full_name: str
    specialty: str | None = None
    email: EmailStr | None = None
    work_start: TimeType
    work_end: TimeType
    staff_role: str = "physician"
    clinic_id: int | None = None
    active: bool
    created_at: DateTimeType
    updated_at: DateTimeType
    clinic: ClinicOut | None = None


class ProviderCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    specialty: str = Field(min_length=2, max_length=120)
    email: EmailStr
    clinic_id: int
    work_start: TimeType
    work_end: TimeType

    @field_validator("work_end")
    @classmethod
    def validate_work_end(cls, value: TimeType, info) -> TimeType:
        work_start = info.data.get("work_start")
        if work_start and value <= work_start:
            raise ValueError("Kraj radnog vremena mora biti nakon početka")
        return value


class RoomOut(ORMModel):
    id: int
    name: str
    type: str | None = None
    clinic_id: int | None = None
    active: bool
    created_at: DateTimeType
    updated_at: DateTimeType
    clinic: ClinicOut | None = None


class RoomCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    type: str | None = Field(default=None, max_length=80)
    clinic_id: int


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
