from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, DDL, ForeignKey, Integer, JSON, Numeric, String, Table, Text, Time, Column, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)

room_services = Table(
    "room_services",
    Base.metadata,
    Column("room_id", ForeignKey("rooms.id"), primary_key=True),
    Column("service_id", ForeignKey("services.id"), primary_key=True),
)


class AppointmentStatus(StrEnum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    arrived = "arrived"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"
    rescheduled = "rescheduled"
    waiting_for_result = "waiting_for_result"
    follow_up_needed = "follow_up_needed"


class AppointmentSource(StrEnum):
    manual = "manual"
    api = "api"
    ai_agent = "ai_agent"
    call_center = "call_center"
    web_booking = "web_booking"
    google_calendar = "google_calendar"
    import_excel = "import_excel"
    external_emr = "external_emr"


class StockMovementType(StrEnum):
    purchase_receipt = "purchase_receipt"
    consumption = "consumption"
    transfer_out = "transfer_out"
    transfer_in = "transfer_in"
    adjustment = "adjustment"
    write_off = "write_off"
    return_to_supplier = "return_to_supplier"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    professional_category: Mapped[str] = mapped_column(String(60), default="administrative", index=True)
    description: Mapped[str | None] = mapped_column(Text)
    permissions: Mapped[list["Permission"]] = relationship(secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    roles: Mapped[list[Role]] = relationship(secondary=role_permissions, back_populates="permissions")


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    role: Mapped[Role] = relationship()
    clinic_memberships: Mapped[list["ClinicMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="ClinicMembership.user_id",
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user: Mapped[User] = relationship()


class Institution(TimestampMixin, Base):
    __tablename__ = "institutions"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    clinics: Mapped[list["Clinic"]] = relationship(back_populates="institution")


class Patient(TimestampMixin, Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), index=True)
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    oib: Mapped[str | None] = mapped_column(String(11), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    phone: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    clinic_associations: Mapped[list["PatientClinicAssociation"]] = relationship(back_populates="patient", cascade="all, delete-orphan")


class Provider(TimestampMixin, Base):
    __tablename__ = "providers"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    specialty: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    work_start: Mapped[time] = mapped_column(Time, default=time(7, 0))
    work_end: Mapped[time] = mapped_column(Time, default=time(15, 0))
    weekly_working_hours: Mapped[dict] = mapped_column(JSON, default=dict)
    staff_role: Mapped[str] = mapped_column(String(60), default="physician", index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    available_for_work: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    clinic: Mapped["Clinic | None"] = relationship()


class Room(TimestampMixin, Base):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    type: Mapped[str | None] = mapped_column(String(80))
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    visible_in_catalog: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    clinic: Mapped["Clinic | None"] = relationship()
    allowed_services: Mapped[list["Service"]] = relationship(secondary=room_services, back_populates="allowed_rooms")


class Clinic(TimestampMixin, Base):
    __tablename__ = "clinics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    institution_key: Mapped[str] = mapped_column(String(120), default="default", index=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), index=True)
    timezone: Mapped[str] = mapped_column(String(80), default="Europe/Zagreb")
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    visible_in_catalog: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    institution: Mapped[Institution | None] = relationship(back_populates="clinics")
    user_memberships: Mapped[list["ClinicMembership"]] = relationship(back_populates="clinic", cascade="all, delete-orphan")
    patient_associations: Mapped[list["PatientClinicAssociation"]] = relationship(back_populates="clinic", cascade="all, delete-orphan")


class ClinicMembership(Base):
    __tablename__ = "clinic_memberships"
    __table_args__ = (UniqueConstraint("user_id", "clinic_id", name="uq_clinic_membership_user_clinic"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(foreign_keys=[user_id], back_populates="clinic_memberships")
    clinic: Mapped[Clinic] = relationship(back_populates="user_memberships")
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_user_id])


class PatientClinicAssociation(Base):
    __tablename__ = "patient_clinic_associations"
    __table_args__ = (UniqueConstraint("patient_id", "clinic_id", name="uq_patient_clinic_association_patient_clinic"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    patient: Mapped[Patient] = relationship(back_populates="clinic_associations")
    clinic: Mapped[Clinic] = relationship(back_populates="patient_associations")
    created_by: Mapped[User | None] = relationship()


class Module(TimestampMixin, Base):
    __tablename__ = "modules"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ClinicalEpisode(TimestampMixin, Base):
    __tablename__ = "clinical_episodes"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    episode_type: Mapped[str] = mapped_column(String(80), default="general", index=True)
    status: Mapped[str] = mapped_column(String(40), default="open", index=True)
    priority: Mapped[str] = mapped_column(String(40), default="routine", index=True)
    start_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    end_date: Mapped[date | None] = mapped_column(Date)
    summary: Mapped[str | None] = mapped_column(Text)
    clinical_notes: Mapped[str | None] = mapped_column(Text)
    owner_provider_id: Mapped[int | None] = mapped_column(ForeignKey("providers.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    patient: Mapped[Patient] = relationship()
    institution: Mapped[Institution | None] = relationship()
    owner_provider: Mapped[Provider | None] = relationship()


class ClinicalPlan(TimestampMixin, Base):
    __tablename__ = "clinical_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("clinical_episodes.id"), index=True)
    source: Mapped[str] = mapped_column(String(40), default="ai_suggestion", index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    proposed_episode_status: Mapped[str | None] = mapped_column(String(40))
    next_action: Mapped[str] = mapped_column(String(80), index=True)
    due_date: Mapped[date | None] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String(40), default="routine", index=True)
    rationale: Mapped[str | None] = mapped_column(Text)
    suggested_follow_up: Mapped[str | None] = mapped_column(Text)
    physician_conclusion: Mapped[str | None] = mapped_column(Text)
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    physician_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    confirmed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    episode: Mapped[ClinicalEpisode] = relationship()
    confirmer: Mapped[User | None] = relationship()


class WorkflowTemplate(TimestampMixin, Base):
    __tablename__ = "workflow_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    default_priority: Mapped[str] = mapped_column(String(40), default="routine")
    checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class WorkflowTask(TimestampMixin, Base):
    __tablename__ = "workflow_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="open", index=True)
    priority: Mapped[str] = mapped_column(String(40), default="routine", index=True)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_episodes.id"), index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"), index=True)
    assignee_provider_id: Mapped[int | None] = mapped_column(ForeignKey("providers.id"), index=True)
    responsible_role: Mapped[str | None] = mapped_column(String(60), index=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_templates.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    patient: Mapped[Patient] = relationship()
    episode: Mapped[ClinicalEpisode | None] = relationship()
    appointment: Mapped["Appointment | None"] = relationship(foreign_keys=[appointment_id])
    assignee_provider: Mapped[Provider | None] = relationship()
    template: Mapped[WorkflowTemplate | None] = relationship()
    checklist: Mapped[list["WorkflowChecklistItem"]] = relationship(back_populates="task", cascade="all, delete-orphan", order_by="WorkflowChecklistItem.position")


class WorkflowChecklistItem(TimestampMixin, Base):
    __tablename__ = "workflow_checklist_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("workflow_tasks.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(220))
    position: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    completed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    task: Mapped[WorkflowTask] = relationship(back_populates="checklist")


class KnowledgeProtocol(TimestampMixin, Base):
    __tablename__ = "knowledge_protocols"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(220), index=True)
    specialty: Mapped[str] = mapped_column(String(100), index=True)
    version: Mapped[str] = mapped_column(String(40))
    summary: Mapped[str] = mapped_column(Text)
    source_title: Mapped[str] = mapped_column(String(260))
    source_url: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    rules: Mapped[list["KnowledgeRule"]] = relationship(back_populates="protocol", cascade="all, delete-orphan", order_by="KnowledgeRule.position")


class KnowledgeRule(TimestampMixin, Base):
    __tablename__ = "knowledge_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    protocol_id: Mapped[int] = mapped_column(ForeignKey("knowledge_protocols.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(220))
    condition_text: Mapped[str] = mapped_column(Text)
    guidance_text: Mapped[str] = mapped_column(Text)
    evidence_level: Mapped[str | None] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer, default=0)
    protocol: Mapped[KnowledgeProtocol] = relationship(back_populates="rules")


class ClinicalDocument(TimestampMixin, Base):
    __tablename__ = "clinical_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id", ondelete="RESTRICT"), index=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    document_type: Mapped[str] = mapped_column(String(60), index=True)
    origin: Mapped[str | None] = mapped_column(String(180))
    document_date: Mapped[date | None] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(String(220), index=True)
    author: Mapped[str | None] = mapped_column(String(160))
    author_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    author_professional_role: Mapped[str | None] = mapped_column(String(80))
    is_clinical_record: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    record_classification: Mapped[str] = mapped_column(String(40), default="clinical", index=True)
    institution: Mapped[str | None] = mapped_column(String(180))
    raw_text: Mapped[str | None] = mapped_column(Text)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    key_findings: Mapped[list | None] = mapped_column(JSON)
    recommendations: Mapped[list | None] = mapped_column(JSON)
    ai_extraction_status: Mapped[str] = mapped_column(String(40), default="not_run", index=True)
    ai_extraction_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_extraction_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    physician_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attachment_path: Mapped[str | None] = mapped_column(Text)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"))
    journey_id: Mapped[int | None] = mapped_column(ForeignKey("patient_journeys.id", ondelete="SET NULL"), index=True)
    clinical_episode_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_episodes.id", ondelete="SET NULL"), index=True)
    upload_channel: Mapped[str | None] = mapped_column(String(60), index=True)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(120))
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    lifecycle_status: Mapped[str] = mapped_column(String(50), default="received", index=True)
    ocr_text: Mapped[str | None] = mapped_column(Text)
    extraction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    classification_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    provenance_json: Mapped[dict | None] = mapped_column(JSON)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    patient: Mapped[Patient] = relationship()
    clinic: Mapped[Clinic | None] = relationship()
    institution_scope: Mapped[Institution | None] = relationship()
    appointment: Mapped[Appointment | None] = relationship()
    author_user: Mapped[User | None] = relationship(foreign_keys=[author_user_id])
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])


class ClinicalDocumentAddendum(TimestampMixin, Base):
    __tablename__ = "clinical_document_addenda"
    id: Mapped[int] = mapped_column(primary_key=True)
    original_document_id: Mapped[int] = mapped_column(ForeignKey("clinical_documents.id", ondelete="CASCADE"), index=True)
    signed_report_id: Mapped[int | None] = mapped_column(ForeignKey("signed_clinical_reports.id", ondelete="RESTRICT"), index=True)
    original_document_type: Mapped[str] = mapped_column(String(80), default="clinical_document", index=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), index=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    signed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    original_document: Mapped[ClinicalDocument] = relationship()
    signed_report: Mapped["SignedClinicalReport | None"] = relationship()
    patient: Mapped[Patient | None] = relationship()
    institution: Mapped[Institution | None] = relationship()
    clinic: Mapped[Clinic | None] = relationship()
    author_user: Mapped[User] = relationship(foreign_keys=[author_user_id])
    signed_by_user: Mapped[User | None] = relationship(foreign_keys=[signed_by_user_id])


class PatientClinicalSummaryRecord(TimestampMixin, Base):
    __tablename__ = "patient_clinical_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    summary_text: Mapped[str | None] = mapped_column(Text)
    known_conditions: Mapped[list | None] = mapped_column(JSON)
    key_findings: Mapped[list | None] = mapped_column(JSON)
    open_items: Mapped[list | None] = mapped_column(JSON)
    risks: Mapped[list | None] = mapped_column(JSON)
    last_recommendations: Mapped[list | None] = mapped_column(JSON)
    source_document_ids: Mapped[list | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(40), default="needs_review", index=True)
    generated_by: Mapped[str | None] = mapped_column(String(80))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    patient: Mapped[Patient] = relationship()
    reviewer: Mapped[User | None] = relationship()


class DocumentProcessingJob(TimestampMixin, Base):
    __tablename__ = "document_processing_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    clinical_document_id: Mapped[int] = mapped_column(ForeignKey("clinical_documents.id", ondelete="CASCADE"), index=True)
    job_type: Mapped[str] = mapped_column(String(40), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    result_metadata_json: Mapped[dict | None] = mapped_column(JSON)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    document: Mapped[ClinicalDocument] = relationship()


class JourneyAISummary(TimestampMixin, Base):
    __tablename__ = "journey_ai_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    journey_id: Mapped[int] = mapped_column(ForeignKey("patient_journeys.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    model_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="pending_review", index=True)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_refs_json: Mapped[list] = mapped_column(JSON, default=list)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    journey: Mapped[PatientJourney] = relationship()
    facts: Mapped[list["JourneyAISummaryFact"]] = relationship(cascade="all, delete-orphan", order_by="JourneyAISummaryFact.id")


class JourneyAISummaryFact(TimestampMixin, Base):
    __tablename__ = "journey_ai_summary_facts"
    id: Mapped[int] = mapped_column(primary_key=True)
    summary_id: Mapped[int] = mapped_column(ForeignKey("journey_ai_summaries.id", ondelete="CASCADE"), index=True)
    statement: Mapped[str] = mapped_column(Text)
    fact_type: Mapped[str] = mapped_column(String(40), index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_documents.id", ondelete="SET NULL"), index=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    limitation: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(40), default="pending_review", index=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_document: Mapped[ClinicalDocument | None] = relationship()


class JourneyCheckIn(TimestampMixin, Base):
    __tablename__ = "journey_check_ins"
    id: Mapped[int] = mapped_column(primary_key=True)
    journey_id: Mapped[int] = mapped_column(ForeignKey("patient_journeys.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="in_review", index=True)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reception_note: Mapped[str | None] = mapped_column(Text)
    journey: Mapped[PatientJourney] = relationship()
    items: Mapped[list["JourneyCheckInItem"]] = relationship(back_populates="check_in", cascade="all, delete-orphan", order_by="JourneyCheckInItem.position")


class JourneyCheckInItem(TimestampMixin, Base):
    __tablename__ = "journey_check_in_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    check_in_id: Mapped[int] = mapped_column(ForeignKey("journey_check_ins.id", ondelete="CASCADE"), index=True)
    item_key: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    label: Mapped[str] = mapped_column(String(220))
    state: Mapped[str] = mapped_column(String(50), default="not_confirmed", index=True)
    requires_clinician: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    note: Mapped[str | None] = mapped_column(Text)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    activity_ids_json: Mapped[list[int]] = mapped_column(JSON, default=list)
    medical_disposition: Mapped[str | None] = mapped_column(String(60), index=True)
    medical_disposition_note: Mapped[str | None] = mapped_column(Text)
    medical_reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    medical_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    position: Mapped[int] = mapped_column(Integer, default=0)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    check_in: Mapped[JourneyCheckIn] = relationship(back_populates="items")


class JourneyEncounter(TimestampMixin, Base):
    __tablename__ = "journey_encounters"
    id: Mapped[int] = mapped_column(primary_key=True)
    journey_id: Mapped[int] = mapped_column(ForeignKey("patient_journeys.id", ondelete="CASCADE"), unique=True, index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    clinical_episode_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_episodes.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="in_progress", index=True)
    anamnesis: Mapped[str | None] = mapped_column(Text)
    examination: Mapped[str | None] = mapped_column(Text)
    patient_findings: Mapped[str | None] = mapped_column(Text)
    opinion: Mapped[str | None] = mapped_column(Text)
    procedure_findings: Mapped[str | None] = mapped_column(Text)
    diagnosis: Mapped[str | None] = mapped_column(Text)
    treatment: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[str | None] = mapped_column(Text)
    follow_up_plan: Mapped[str | None] = mapped_column(Text)
    opened_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    journey: Mapped[PatientJourney] = relationship()
    clinic: Mapped[Clinic | None] = relationship()


class ClinicalFinding(TimestampMixin, Base):
    __tablename__ = "clinical_findings"
    __table_args__ = (
        CheckConstraint("length(trim(source_type)) > 0", name="ck_clinical_findings_source_type_non_empty"),
        CheckConstraint("length(trim(source_label)) > 0", name="ck_clinical_findings_source_label_non_empty"),
        CheckConstraint("length(trim(source_reference)) > 0", name="ck_clinical_findings_source_reference_non_empty"),
        CheckConstraint("length(trim(finding_key)) > 0", name="ck_clinical_findings_key_non_empty"),
        CheckConstraint("length(trim(label)) > 0", name="ck_clinical_findings_label_non_empty"),
        CheckConstraint("length(trim(schema_version)) > 0", name="ck_clinical_findings_schema_version_non_empty"),
        CheckConstraint(
            "lifecycle_status in ('received', 'linked_to_patient', 'awaiting_review', 'review_in_progress', 'reviewed', 'needs_clinician_decision', 'decision_documented', 'follow_up_recommended', 'external_referral_recommended', 'closed_for_now')",
            name="ck_clinical_findings_lifecycle_status_safe",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id", ondelete="RESTRICT"), index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_documents.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    source_label: Mapped[str] = mapped_column(String(220))
    source_reference: Mapped[str] = mapped_column(Text)
    finding_key: Mapped[str] = mapped_column(String(160), index=True)
    label: Mapped[str] = mapped_column(String(240))
    category: Mapped[str] = mapped_column(String(80), index=True)
    lifecycle_status: Mapped[str] = mapped_column(String(80), index=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    schema_version: Mapped[str] = mapped_column(String(80), default="clinical_finding.v1")

    patient: Mapped[Patient] = relationship()
    institution: Mapped[Institution | None] = relationship()
    source_document: Mapped[ClinicalDocument | None] = relationship()
    reviewer: Mapped[User | None] = relationship()


class ClinicalOpenQuestion(TimestampMixin, Base):
    __tablename__ = "clinical_open_questions"
    __table_args__ = (
        CheckConstraint("length(trim(source_type)) > 0", name="ck_clinical_open_questions_source_type_non_empty"),
        CheckConstraint("length(trim(source_label)) > 0", name="ck_clinical_open_questions_source_label_non_empty"),
        CheckConstraint("length(trim(source_reference)) > 0", name="ck_clinical_open_questions_source_reference_non_empty"),
        CheckConstraint("length(trim(question_key)) > 0", name="ck_clinical_open_questions_key_non_empty"),
        CheckConstraint("length(trim(label)) > 0", name="ck_clinical_open_questions_label_non_empty"),
        CheckConstraint("length(trim(schema_version)) > 0", name="ck_clinical_open_questions_schema_version_non_empty"),
        CheckConstraint(
            "status in ('draft', 'suggested', 'awaiting_review', 'under_review', 'needs_clinician_decision', 'decision_documented', 'deferred', 'closed_for_now')",
            name="ck_clinical_open_questions_status_safe",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id", ondelete="RESTRICT"), index=True)
    finding_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_findings.id"), index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_documents.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    source_label: Mapped[str] = mapped_column(String(220))
    source_reference: Mapped[str] = mapped_column(Text)
    question_key: Mapped[str] = mapped_column(String(160), index=True)
    label: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(80), index=True)
    requires_clinician_review: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    schema_version: Mapped[str] = mapped_column(String(80), default="clinical_open_question.v1")

    patient: Mapped[Patient] = relationship()
    institution: Mapped[Institution | None] = relationship()
    finding: Mapped[ClinicalFinding | None] = relationship()
    source_document: Mapped[ClinicalDocument | None] = relationship()
    reviewer: Mapped[User | None] = relationship()


class Service(TimestampMixin, Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    code: Mapped[str | None] = mapped_column(String(80), unique=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    module_id: Mapped[int | None] = mapped_column(ForeignKey("modules.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    visible_in_catalog: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    module: Mapped[Module | None] = relationship()
    allowed_rooms: Mapped[list[Room]] = relationship(secondary=room_services, back_populates="allowed_services")


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_episodes.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), default=AppointmentStatus.scheduled.value, index=True)
    source: Mapped[str] = mapped_column(String(40), default=AppointmentSource.manual.value)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    identity_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    identity_verified_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    patient: Mapped[Patient] = relationship()
    service: Mapped[Service] = relationship()
    provider: Mapped[Provider] = relationship()
    room: Mapped[Room] = relationship()
    clinic: Mapped[Clinic | None] = relationship()
    episode: Mapped[ClinicalEpisode | None] = relationship()


class PatientJourney(TimestampMixin, Base):
    __tablename__ = "patient_journeys"
    __table_args__ = (UniqueConstraint("appointment_id", name="uq_patient_journeys_appointment_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), unique=True, index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    package_version_id: Mapped[int | None] = mapped_column(ForeignKey("service_package_versions.id"), index=True)
    package_booking_key: Mapped[str | None] = mapped_column(String(160), unique=True, index=True)
    intake_channel: Mapped[str] = mapped_column(String(30), index=True)
    current_stage: Mapped[str] = mapped_column(String(50), default="requested", index=True)
    document_status: Mapped[str] = mapped_column(String(40), default="not_requested", index=True)
    preparation_status: Mapped[str] = mapped_column(String(40), default="not_assigned", index=True)
    check_in_status: Mapped[str] = mapped_column(String(40), default="not_arrived", index=True)
    encounter_status: Mapped[str] = mapped_column(String(40), default="not_started", index=True)
    consumables_status: Mapped[str] = mapped_column(String(40), default="not_ready", index=True)
    billing_status: Mapped[str] = mapped_column(String(40), default="not_ready", index=True)
    payment_status: Mapped[str] = mapped_column(String(40), default="not_due", index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    patient: Mapped[Patient] = relationship()
    appointment: Mapped[Appointment] = relationship()
    clinic: Mapped[Clinic | None] = relationship()
    activities: Mapped[list["JourneyActivity"]] = relationship(back_populates="journey", cascade="all, delete-orphan", order_by="JourneyActivity.sequence")
    events: Mapped[list["JourneyEvent"]] = relationship(back_populates="journey", cascade="all, delete-orphan", order_by="JourneyEvent.created_at")
    blockers: Mapped[list["JourneyBlocker"]] = relationship(back_populates="journey", cascade="all, delete-orphan", order_by="JourneyBlocker.created_at")


class JourneyActivity(TimestampMixin, Base):
    __tablename__ = "journey_activities"
    __table_args__ = (
        CheckConstraint("sequence > 0", name="ck_journey_activities_sequence_positive"),
        CheckConstraint("planned_end > planned_start", name="ck_journey_activities_planned_range"),
        UniqueConstraint("appointment_id", name="uq_journey_activities_appointment_id"),
        UniqueConstraint("journey_id", "activity_key", name="uq_journey_activities_key"),
        UniqueConstraint("journey_id", "sequence", name="uq_journey_activities_sequence"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    journey_id: Mapped[int] = mapped_column(ForeignKey("patient_journeys.id", ondelete="CASCADE"), index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id", ondelete="SET NULL"), unique=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    activity_key: Mapped[str] = mapped_column(String(120))
    activity_kind: Mapped[str] = mapped_column(String(60), index=True)
    specialty_key: Mapped[str] = mapped_column(String(80), index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    primary_provider_id: Mapped[int | None] = mapped_column(ForeignKey("providers.id"), index=True)
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    depends_on_activity_id: Mapped[int | None] = mapped_column(ForeignKey("journey_activities.id", ondelete="SET NULL"))
    package_item_id: Mapped[int | None] = mapped_column(ForeignKey("service_package_items.id", ondelete="SET NULL"), index=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    planned_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), default="planned", index=True)
    not_performed_reason: Mapped[str | None] = mapped_column(Text)
    form_resolution_status: Mapped[str] = mapped_column(String(40), default="unresolved")
    billing_status: Mapped[str] = mapped_column(String(40), default="not_ready")
    consumables_status: Mapped[str] = mapped_column(String(40), default="not_ready")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    started_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    completed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    journey: Mapped[PatientJourney] = relationship(back_populates="activities")
    appointment: Mapped[Appointment | None] = relationship()
    service: Mapped[Service] = relationship()
    clinic: Mapped[Clinic | None] = relationship()
    primary_provider: Mapped[Provider | None] = relationship(foreign_keys=[primary_provider_id])
    room: Mapped[Room | None] = relationship()
    participants: Mapped[list["JourneyActivityParticipant"]] = relationship(back_populates="activity", cascade="all, delete-orphan")


class JourneyActivityParticipant(Base):
    __tablename__ = "journey_activity_participants"
    __table_args__ = (UniqueConstraint("activity_id", "provider_id", "role_key", name="uq_journey_activity_participant_role"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("journey_activities.id", ondelete="CASCADE"), index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), index=True)
    role_key: Mapped[str] = mapped_column(String(60))
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(40), default="assigned")
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activity: Mapped[JourneyActivity] = relationship(back_populates="participants")
    provider: Mapped[Provider] = relationship()


class ActivityPreparationRequirement(TimestampMixin, Base):
    __tablename__ = "activity_preparation_requirements"
    __table_args__ = (UniqueConstraint("activity_id", "requirement_key", name="uq_activity_preparation_requirement"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("journey_activities.id", ondelete="CASCADE"), index=True)
    requirement_key: Mapped[str] = mapped_column(String(100), index=True)
    label: Mapped[str] = mapped_column(String(220))
    patient_instruction: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(60))
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    state: Mapped[str] = mapped_column(String(40), default="assigned")
    source_template_key: Mapped[str] = mapped_column(String(120))
    source_template_version: Mapped[str] = mapped_column(String(40))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
    activity: Mapped[JourneyActivity] = relationship()


class ServicePackage(TimestampMixin, Base):
    __tablename__ = "service_packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    package_key: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text)
    specialty_key: Mapped[str] = mapped_column(String(80), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    versions: Mapped[list["ServicePackageVersion"]] = relationship(back_populates="package", cascade="all, delete-orphan")


class ServicePackageVersion(Base):
    __tablename__ = "service_package_versions"
    __table_args__ = (UniqueConstraint("package_id", "version", name="uq_service_package_version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("service_packages.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    package: Mapped[ServicePackage] = relationship(back_populates="versions")
    items: Mapped[list["ServicePackageItem"]] = relationship(back_populates="package_version", cascade="all, delete-orphan", order_by="ServicePackageItem.sequence")


class ServicePackageItem(Base):
    __tablename__ = "service_package_items"
    __table_args__ = (
        CheckConstraint("sequence > 0", name="ck_service_package_items_sequence_positive"),
        CheckConstraint("default_duration_minutes > 0", name="ck_service_package_items_duration_positive"),
        UniqueConstraint("package_version_id", "sequence", name="uq_service_package_item_sequence"),
        UniqueConstraint("package_version_id", "activity_key", name="uq_service_package_item_key"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    package_version_id: Mapped[int] = mapped_column(ForeignKey("service_package_versions.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    activity_key: Mapped[str] = mapped_column(String(120))
    activity_kind: Mapped[str] = mapped_column(String(60))
    specialty_key: Mapped[str] = mapped_column(String(80))
    sequence: Mapped[int] = mapped_column(Integer)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    relative_start_offset_minutes: Mapped[int] = mapped_column(Integer, default=0)
    default_duration_minutes: Mapped[int] = mapped_column(Integer)
    preferred_clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"))
    preferred_room_type: Mapped[str | None] = mapped_column(String(80))
    depends_on_item_id: Mapped[int | None] = mapped_column(ForeignKey("service_package_items.id", ondelete="SET NULL"))
    form_binding_override_version_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_form_versions.id", ondelete="SET NULL"))
    preparation_requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    billing_inclusion_rule: Mapped[str] = mapped_column(String(40), default="include")
    package_version: Mapped[ServicePackageVersion] = relationship(back_populates="items")
    service: Mapped[Service] = relationship()


class ClinicalFormDefinition(TimestampMixin, Base):
    __tablename__ = "clinical_form_definitions"
    id: Mapped[int] = mapped_column(primary_key=True)
    form_key: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    specialty_key: Mapped[str] = mapped_column(String(80), index=True)
    activity_kind: Mapped[str] = mapped_column(String(60), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    owner_clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    versions: Mapped[list[ClinicalFormVersion]] = relationship(back_populates="definition", cascade="all, delete-orphan", order_by="ClinicalFormVersion.version")


class ClinicalFormVersion(Base):
    __tablename__ = "clinical_form_versions"
    __table_args__ = (
        UniqueConstraint("definition_id", "version", name="uq_clinical_form_definition_version"),
        CheckConstraint("status in ('draft','published','retired')", name="ck_clinical_form_versions_status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    definition_id: Mapped[int] = mapped_column(ForeignKey("clinical_form_definitions.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    sections_json: Mapped[list] = mapped_column(JSON, default=list)
    validation_schema_json: Mapped[dict] = mapped_column(JSON, default=dict)
    print_layout_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_document_type: Mapped[str] = mapped_column(String(80))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supersedes_version_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_form_versions.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    definition: Mapped[ClinicalFormDefinition] = relationship(back_populates="versions")


class ServiceFormBinding(Base):
    __tablename__ = "service_form_bindings"
    __table_args__ = (CheckConstraint("service_id is not null or (specialty_key is not null and activity_kind is not null)", name="ck_service_form_binding_scope"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id"), index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    specialty_key: Mapped[str | None] = mapped_column(String(80), index=True)
    activity_kind: Mapped[str | None] = mapped_column(String(60), index=True)
    form_version_id: Mapped[int] = mapped_column(ForeignKey("clinical_form_versions.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    form_version: Mapped[ClinicalFormVersion] = relationship()


class ActivityReportPolicy(Base):
    __tablename__ = "activity_report_policies"
    __table_args__ = (
        CheckConstraint("service_id is not null or activity_kind is not null", name="ck_activity_report_policy_scope"),
        CheckConstraint("policy_version <> ''", name="ck_activity_report_policy_version_nonempty"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id"), index=True)
    specialty_key: Mapped[str | None] = mapped_column(String(80), index=True)
    activity_kind: Mapped[str | None] = mapped_column(String(60), index=True)
    report_required: Mapped[bool] = mapped_column(Boolean, default=True)
    signature_required_before_activity_completion: Mapped[bool] = mapped_column(Boolean, default=False)
    signature_required_before_billing: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_post_visit_signing: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_source: Mapped[str] = mapped_column(String(80), default="configured")
    policy_version: Mapped[str] = mapped_column(String(40), default="1")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    service: Mapped[Service | None] = relationship()


class ClinicalFormInstance(TimestampMixin, Base):
    __tablename__ = "clinical_form_instances"
    __table_args__ = (
        UniqueConstraint("activity_id", "purpose", "amended_from_instance_id", name="uq_clinical_form_instance_lineage"),
        CheckConstraint("status in ('draft','in_progress','completed','signed','amended','void')", name="ck_clinical_form_instances_status"),
        CheckConstraint(
            "(completion_idempotency_key is null and completion_payload_hash is null) or "
            "(completion_idempotency_key is not null and completion_payload_hash is not null)",
            name="ck_clinical_form_completion_idempotency_pair",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("journey_activities.id", ondelete="CASCADE"), index=True)
    form_version_id: Mapped[int] = mapped_column(ForeignKey("clinical_form_versions.id"))
    purpose: Mapped[str] = mapped_column(String(60), default="clinical_report")
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    data_json: Mapped[dict] = mapped_column(JSON, default=dict)
    rendered_summary: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    last_edited_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    completed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    signed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    amended_from_instance_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_form_instances.id", ondelete="SET NULL"))
    binding_source: Mapped[str] = mapped_column(String(80))
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completion_idempotency_key: Mapped[str | None] = mapped_column(String(160))
    completion_payload_hash: Mapped[str | None] = mapped_column(String(64))
    form_version: Mapped[ClinicalFormVersion] = relationship()
    revisions: Mapped[list[ClinicalFormRevision]] = relationship(back_populates="instance", cascade="all, delete-orphan", order_by="ClinicalFormRevision.revision_number")

    @property
    def revision_number(self) -> int:
        return self.revisions[-1].revision_number if self.revisions else 0


class ClinicalFormRevision(Base):
    __tablename__ = "clinical_form_revisions"
    __table_args__ = (UniqueConstraint("instance_id", "revision_number", name="uq_clinical_form_revision_number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("clinical_form_instances.id", ondelete="CASCADE"), index=True)
    revision_number: Mapped[int] = mapped_column(Integer)
    data_json: Mapped[dict] = mapped_column(JSON)
    rendered_summary: Mapped[str | None] = mapped_column(Text)
    edited_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    instance: Mapped[ClinicalFormInstance] = relationship(back_populates="revisions")


class SignedClinicalReport(Base):
    __tablename__ = "signed_clinical_reports"
    __table_args__ = (
        UniqueConstraint("form_instance_id", name="uq_signed_clinical_reports_form_instance"),
        UniqueConstraint("clinical_document_id", name="uq_signed_clinical_reports_document"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    form_instance_id: Mapped[int] = mapped_column(ForeignKey("clinical_form_instances.id"), index=True)
    form_version_id: Mapped[int] = mapped_column(ForeignKey("clinical_form_versions.id"))
    clinical_document_id: Mapped[int] = mapped_column(ForeignKey("clinical_documents.id"), index=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("journey_activities.id", ondelete="CASCADE"), index=True)
    journey_id: Mapped[int] = mapped_column(ForeignKey("patient_journeys.id", ondelete="CASCADE"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    document_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(220))
    structured_data_json: Mapped[dict] = mapped_column(JSON)
    rendered_content: Mapped[str] = mapped_column(Text)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    signer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    signer_name: Mapped[str] = mapped_column(String(160))
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    supersedes_report_id: Mapped[int | None] = mapped_column(ForeignKey("signed_clinical_reports.id", ondelete="SET NULL"))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str] = mapped_column(String(128))
    hash_algorithm: Mapped[str] = mapped_column(String(30), default="sha256")
    form_instance: Mapped[ClinicalFormInstance] = relationship()
    form_version: Mapped[ClinicalFormVersion] = relationship()
    clinical_document: Mapped[ClinicalDocument] = relationship()
    activity: Mapped[JourneyActivity] = relationship()


class ReportPrintEvent(Base):
    __tablename__ = "report_print_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("signed_clinical_reports.id", ondelete="CASCADE"), index=True)
    printed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    printed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    request_id: Mapped[str | None] = mapped_column(String(120))


class ReportDeliveryEvent(Base):
    __tablename__ = "report_delivery_events"
    __table_args__ = (CheckConstraint("status in ('queued_stub','sent','delivered','failed','cancelled')", name="ck_report_delivery_status"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("signed_clinical_reports.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(40))
    recipient: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(40), default="queued_stub", index=True)
    provider_mode: Mapped[str] = mapped_column(String(60), default="local_demo")
    initiated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    correlation_id: Mapped[str] = mapped_column(String(120), unique=True)
    recipient_source: Mapped[str] = mapped_column(String(40), default="patient_verified")
    alternate_recipient_reason: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(160), unique=True, index=True)


class ProcedureIntervention(Base):
    __tablename__ = "procedure_interventions"
    __table_args__ = (
        CheckConstraint("intervention_type in ('biopsy','polypectomy','injection','clip_placement','dilation','hemostasis','foreign_body_removal','other')", name="ck_procedure_intervention_type"),
        CheckConstraint("count > 0", name="ck_procedure_intervention_count"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("journey_activities.id", ondelete="CASCADE"), index=True)
    intervention_type: Mapped[str] = mapped_column(String(60))
    anatomical_site: Mapped[str | None] = mapped_column(String(220))
    description: Mapped[str | None] = mapped_column(Text)
    technique: Mapped[str | None] = mapped_column(String(220))
    device: Mapped[str | None] = mapped_column(String(220))
    size: Mapped[str | None] = mapped_column(String(80))
    count: Mapped[int] = mapped_column(Integer, default=1)
    retrieval_status: Mapped[str | None] = mapped_column(String(60))
    complication: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PathologyCase(TimestampMixin, Base):
    __tablename__ = "pathology_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    journey_id: Mapped[int] = mapped_column(ForeignKey("patient_journeys.id", ondelete="CASCADE"), index=True)
    source_activity_id: Mapped[int] = mapped_column(ForeignKey("journey_activities.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), unique=True)
    status: Mapped[str] = mapped_column(String(60), default="draft", index=True)
    external_lab: Mapped[str | None] = mapped_column(String(220))
    external_case_number: Mapped[str | None] = mapped_column(String(160))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lab_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    patient_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    communication_disposition: Mapped[str | None] = mapped_column(String(80))
    communication_note: Mapped[str | None] = mapped_column(Text)
    communication_attempts: Mapped[int] = mapped_column(Integer, default=0)
    communication_decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    communication_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    specimens: Mapped[list[PathologySpecimen]] = relationship(back_populates="case", cascade="all, delete-orphan", order_by="PathologySpecimen.id")
    reports: Mapped[list[PathologyReportLink]] = relationship(back_populates="case", cascade="all, delete-orphan", order_by="PathologyReportLink.id")


class PathologySpecimen(Base):
    __tablename__ = "pathology_specimens"
    __table_args__ = (UniqueConstraint("case_id", "specimen_label", name="uq_pathology_specimen_label"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("pathology_cases.id", ondelete="CASCADE"), index=True)
    specimen_label: Mapped[str] = mapped_column(String(160))
    anatomical_site: Mapped[str] = mapped_column(String(220))
    specimen_type: Mapped[str] = mapped_column(String(100))
    source_intervention_id: Mapped[int | None] = mapped_column(ForeignKey("procedure_interventions.id", ondelete="SET NULL"))
    container: Mapped[str | None] = mapped_column(String(120))
    fixation: Mapped[str | None] = mapped_column(String(120))
    collection_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    case: Mapped[PathologyCase] = relationship(back_populates="specimens")


class PathologyReportLink(Base):
    __tablename__ = "pathology_report_links"
    __table_args__ = (UniqueConstraint("case_id", "clinical_document_id", name="uq_pathology_report_link"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("pathology_cases.id", ondelete="CASCADE"), index=True)
    clinical_document_id: Mapped[int] = mapped_column(ForeignKey("clinical_documents.id"))
    linked_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    case: Mapped[PathologyCase] = relationship(back_populates="reports")
    document: Mapped[ClinicalDocument] = relationship()


class JourneyEvent(Base):
    __tablename__ = "journey_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    journey_id: Mapped[int] = mapped_column(ForeignKey("patient_journeys.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    from_stage: Mapped[str | None] = mapped_column(String(50), index=True)
    to_stage: Mapped[str | None] = mapped_column(String(50), index=True)
    summary: Mapped[str] = mapped_column(Text)
    source_channel: Mapped[str] = mapped_column(String(40), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    actor_type: Mapped[str] = mapped_column(String(40), default="user")
    request_id: Mapped[str | None] = mapped_column(String(80), index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    journey: Mapped[PatientJourney] = relationship(back_populates="events")


class JourneyBlocker(TimestampMixin, Base):
    __tablename__ = "journey_blockers"
    id: Mapped[int] = mapped_column(primary_key=True)
    journey_id: Mapped[int] = mapped_column(ForeignKey("patient_journeys.id", ondelete="CASCADE"), index=True)
    blocker_key: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(220))
    details: Mapped[str | None] = mapped_column(Text)
    is_clinical: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    resolved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    journey: Mapped[PatientJourney] = relationship(back_populates="blockers")


class PreparationPlanTemplate(TimestampMixin, Base):
    __tablename__="preparation_plan_templates"
    __table_args__=(UniqueConstraint("template_key","version",name="uq_preparation_template_version"),)
    id:Mapped[int]=mapped_column(primary_key=True);template_key:Mapped[str]=mapped_column(String(100),index=True);name:Mapped[str]=mapped_column(String(180));procedure_type:Mapped[str]=mapped_column(String(100),index=True);version:Mapped[str]=mapped_column(String(40));patient_instructions:Mapped[str]=mapped_column(Text);requirements_json:Mapped[list]=mapped_column(JSON,default=list);reminder_schedule_json:Mapped[list]=mapped_column(JSON,default=list);active:Mapped[bool]=mapped_column(Boolean,default=True,index=True);approved_by:Mapped[int|None]=mapped_column(ForeignKey("users.id"));approved_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class JourneyPreparation(TimestampMixin, Base):
    __tablename__="journey_preparations"
    id:Mapped[int]=mapped_column(primary_key=True);journey_id:Mapped[int]=mapped_column(ForeignKey("patient_journeys.id",ondelete="CASCADE"),unique=True,index=True);template_id:Mapped[int]=mapped_column(ForeignKey("preparation_plan_templates.id"));status:Mapped[str]=mapped_column(String(40),default="assigned",index=True);assigned_by:Mapped[int|None]=mapped_column(ForeignKey("users.id"));assigned_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now());acknowledged_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));requirement_states_json:Mapped[dict]=mapped_column(JSON,default=dict);journey:Mapped[PatientJourney]=relationship();template:Mapped[PreparationPlanTemplate]=relationship()

class PatientFormTemplate(TimestampMixin, Base):
    __tablename__="patient_form_templates"
    __table_args__=(UniqueConstraint("template_key","version",name="uq_patient_form_template_version"),)
    id:Mapped[int]=mapped_column(primary_key=True);template_key:Mapped[str]=mapped_column(String(100),index=True);name:Mapped[str]=mapped_column(String(180));version:Mapped[str]=mapped_column(String(40));fields_json:Mapped[list]=mapped_column(JSON,default=list);active:Mapped[bool]=mapped_column(Boolean,default=True,index=True);approved_by:Mapped[int|None]=mapped_column(ForeignKey("users.id"));approved_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class JourneyForm(TimestampMixin, Base):
    __tablename__="journey_forms"
    id:Mapped[int]=mapped_column(primary_key=True);journey_id:Mapped[int]=mapped_column(ForeignKey("patient_journeys.id",ondelete="CASCADE"),index=True);template_id:Mapped[int]=mapped_column(ForeignKey("patient_form_templates.id"));status:Mapped[str]=mapped_column(String(40),default="requested",index=True);answers_json:Mapped[dict|None]=mapped_column(JSON);requested_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now());completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));reviewed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));reviewed_by:Mapped[int|None]=mapped_column(ForeignKey("users.id"));journey:Mapped[PatientJourney]=relationship();template:Mapped[PatientFormTemplate]=relationship()

class DocumentRequest(TimestampMixin, Base):
    __tablename__="document_requests"
    id:Mapped[int]=mapped_column(primary_key=True);journey_id:Mapped[int]=mapped_column(ForeignKey("patient_journeys.id",ondelete="CASCADE"),index=True);document_type:Mapped[str]=mapped_column(String(100),index=True);title:Mapped[str]=mapped_column(String(220));mandatory:Mapped[bool]=mapped_column(Boolean,default=True,index=True);status:Mapped[str]=mapped_column(String(40),default="requested",index=True);clinical_document_id:Mapped[int|None]=mapped_column(ForeignKey("clinical_documents.id"));requested_by:Mapped[int|None]=mapped_column(ForeignKey("users.id"));resolved_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));journey:Mapped[PatientJourney]=relationship();clinical_document:Mapped[ClinicalDocument|None]=relationship()

class CommunicationEvent(TimestampMixin, Base):
    __tablename__="communication_events"
    id:Mapped[int]=mapped_column(primary_key=True);journey_id:Mapped[int]=mapped_column(ForeignKey("patient_journeys.id",ondelete="CASCADE"),index=True);channel:Mapped[str]=mapped_column(String(40),index=True);template_key:Mapped[str]=mapped_column(String(120));status:Mapped[str]=mapped_column(String(40),default="queued",index=True);scheduled_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),index=True);sent_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));delivered_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));failure_reason:Mapped[str|None]=mapped_column(Text);correlation_id:Mapped[str]=mapped_column(String(100),unique=True,index=True);journey:Mapped[PatientJourney]=relationship()

class JourneyReminder(TimestampMixin, Base):
    __tablename__="journey_reminders"
    id:Mapped[int]=mapped_column(primary_key=True);journey_id:Mapped[int]=mapped_column(ForeignKey("patient_journeys.id",ondelete="CASCADE"),index=True);reminder_type:Mapped[str]=mapped_column(String(100),index=True);channel:Mapped[str]=mapped_column(String(40));scheduled_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True);status:Mapped[str]=mapped_column(String(40),default="scheduled",index=True);communication_event_id:Mapped[int|None]=mapped_column(ForeignKey("communication_events.id"));journey:Mapped[PatientJourney]=relationship();communication_event:Mapped[CommunicationEvent|None]=relationship()


class ClinicalReadinessSnapshot(Base):
    __tablename__ = "clinical_readiness_snapshots"
    __table_args__ = (
        CheckConstraint("length(trim(snapshot_reason)) > 0", name="ck_clinical_readiness_snapshots_reason_non_empty"),
        UniqueConstraint("appointment_id", "created_by_user_id", "idempotency_key", name="uq_clinical_readiness_snapshot_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    schema_version: Mapped[str] = mapped_column(String(80))
    preview_generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    preview_status: Mapped[str] = mapped_column(String(60), index=True)
    preview_summary: Mapped[str] = mapped_column(Text)
    template_key: Mapped[str | None] = mapped_column(String(120), index=True)
    template_label: Mapped[str | None] = mapped_column(String(180))
    template_version: Mapped[str | None] = mapped_column(String(80), index=True)
    template_binding_status: Mapped[str | None] = mapped_column(String(80), index=True)
    template_binding_warning: Mapped[str | None] = mapped_column(Text)
    is_preview_snapshot: Mapped[bool] = mapped_column(Boolean, default=True)
    items_json: Mapped[list] = mapped_column(JSON)
    limitations_json: Mapped[list] = mapped_column(JSON)
    source_warnings_json: Mapped[list] = mapped_column(JSON)
    source_refs_json: Mapped[list] = mapped_column(JSON)
    disclaimer: Mapped[str] = mapped_column(Text)
    snapshot_reason: Mapped[str] = mapped_column(Text)
    superseded_by_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_readiness_snapshots.id"), index=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_reason: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(160), index=True)
    idempotency_fingerprint: Mapped[str | None] = mapped_column(String(64))

    appointment: Mapped[Appointment] = relationship()
    patient: Mapped[Patient] = relationship()
    service: Mapped[Service] = relationship()
    creator: Mapped[User] = relationship()
    superseded_by_snapshot: Mapped["ClinicalReadinessSnapshot | None"] = relationship(remote_side=[id])


class ClinicalReadinessReviewAcknowledgment(Base):
    __tablename__ = "clinical_readiness_review_acknowledgments"
    __table_args__ = (
        CheckConstraint("length(trim(reason)) > 0", name="ck_clinical_readiness_review_acknowledgments_reason_non_empty"),
        CheckConstraint("is_decision = false", name="ck_clinical_readiness_review_acknowledgments_not_decision"),
        CheckConstraint("is_clearance = false", name="ck_clinical_readiness_review_acknowledgments_not_clearance"),
        CheckConstraint("is_override = false", name="ck_clinical_readiness_review_acknowledgments_not_override"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_readiness_snapshots.id"), index=True)
    advisory_signal_key: Mapped[str] = mapped_column(String(160), index=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    actor_role: Mapped[str] = mapped_column(String(80), index=True)
    reason: Mapped[str] = mapped_column(Text)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    schema_version: Mapped[str] = mapped_column(String(80), default="acknowledgment.v1")
    not_decision_disclaimer: Mapped[str] = mapped_column(Text, default="Acknowledgment je zapis ljudskog pregleda signala, nije klinicka odluka.")
    is_decision: Mapped[bool] = mapped_column(Boolean, default=False)
    is_clearance: Mapped[bool] = mapped_column(Boolean, default=False)
    is_override: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    appointment: Mapped[Appointment] = relationship()
    patient: Mapped[Patient] = relationship()
    snapshot: Mapped[ClinicalReadinessSnapshot | None] = relationship()
    actor: Mapped[User] = relationship()


_SNAPSHOT_PROTECTED_FIELDS = [
    "id",
    "appointment_id",
    "patient_id",
    "service_id",
    "created_at",
    "created_by_user_id",
    "schema_version",
    "preview_generated_at",
    "preview_status",
    "preview_summary",
    "template_key",
    "template_label",
    "template_version",
    "template_binding_status",
    "template_binding_warning",
    "is_preview_snapshot",
    "items_json",
    "limitations_json",
    "source_warnings_json",
    "source_refs_json",
    "disclaimer",
    "snapshot_reason",
    "idempotency_key",
    "idempotency_fingerprint",
]


def _sqlite_snapshot_protected_fields_same() -> str:
    return " AND ".join(f"NEW.{field} IS OLD.{field}" for field in _SNAPSHOT_PROTECTED_FIELDS)


event.listen(
    ClinicalReadinessSnapshot.__table__,
    "after_create",
    DDL(
        f"""
        CREATE TRIGGER IF NOT EXISTS trg_clinical_readiness_snapshots_immutable_update
        BEFORE UPDATE ON clinical_readiness_snapshots
        FOR EACH ROW
        WHEN NOT (
            (
                {_sqlite_snapshot_protected_fields_same()}
                AND NEW.superseded_by_snapshot_id IS OLD.superseded_by_snapshot_id
                AND NEW.superseded_at IS OLD.superseded_at
                AND NEW.superseded_reason IS OLD.superseded_reason
            )
            OR
            (
                {_sqlite_snapshot_protected_fields_same()}
                AND OLD.superseded_by_snapshot_id IS NULL
                AND OLD.superseded_at IS NULL
                AND OLD.superseded_reason IS NULL
                AND NEW.superseded_by_snapshot_id IS NOT NULL
                AND NEW.superseded_at IS NOT NULL
                AND NEW.superseded_reason IS NOT NULL
            )
        )
        BEGIN
            SELECT RAISE(ABORT, 'Clinical Readiness Snapshot is immutable after insert except first-time additive supersession metadata');
        END;
        """
    ).execute_if(dialect="sqlite"),
)

event.listen(
    ClinicalReadinessSnapshot.__table__,
    "after_create",
    DDL(
        """
        CREATE TRIGGER IF NOT EXISTS trg_clinical_readiness_snapshots_immutable_delete
        BEFORE DELETE ON clinical_readiness_snapshots
        FOR EACH ROW
        BEGIN
            SELECT RAISE(ABORT, 'Clinical Readiness Snapshot rows cannot be deleted');
        END;
        """
    ).execute_if(dialect="sqlite"),
)


class LabTemplate(TimestampMixin, Base):
    __tablename__ = "lab_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    condition: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    tests: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class LabOrder(TimestampMixin, Base):
    __tablename__ = "lab_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_episodes.id"), index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"), index=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("lab_templates.id"))
    external_laboratory: Mapped[str | None] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(40), default="ordered", index=True)
    ordered_at: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    specimen_type: Mapped[str] = mapped_column(String(40), default="blood", index=True)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    dispatched_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    external_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    review_conclusion: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    patient: Mapped[Patient] = relationship()
    episode: Mapped[ClinicalEpisode | None] = relationship()
    appointment: Mapped["Appointment | None"] = relationship()
    template: Mapped[LabTemplate | None] = relationship()
    results: Mapped[list["LabResult"]] = relationship(back_populates="order", cascade="all, delete-orphan", order_by="LabResult.id")


class LabResult(TimestampMixin, Base):
    __tablename__ = "lab_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("lab_orders.id", ondelete="CASCADE"), index=True)
    test_name: Mapped[str] = mapped_column(String(180), index=True)
    value: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    text_value: Mapped[str | None] = mapped_column(String(240))
    unit: Mapped[str | None] = mapped_column(String(60))
    reference_low: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    reference_high: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    flag: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    resulted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    order: Mapped[LabOrder] = relationship(back_populates="results")


class Therapy(TimestampMixin, Base):
    __tablename__ = "therapies"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_episodes.id"), index=True)
    parent_therapy_id: Mapped[int | None] = mapped_column(ForeignKey("therapies.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    instructions: Mapped[str] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    prescriber: Mapped[str | None] = mapped_column(String(160))
    notes: Mapped[str | None] = mapped_column(Text)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    stop_reason: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    completion_note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    patient: Mapped[Patient] = relationship()
    episode: Mapped[ClinicalEpisode | None] = relationship()


class ApiKey(TimestampMixin, Base):
    __tablename__ = "api_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    key_hash: Mapped[str] = mapped_column(String(255), unique=True)
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    scope_type: Mapped[str | None] = mapped_column(String(40), index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id", ondelete="RESTRICT"), index=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id", ondelete="RESTRICT"), index=True)
    actor_type: Mapped[str] = mapped_column(String(40), default="system", index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    actor_api_key_id: Mapped[int | None] = mapped_column(ForeignKey("api_keys.id"))
    action: Mapped[str] = mapped_column(String(40), index=True)
    entity_type: Mapped[str] = mapped_column(String(120), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    before_json: Mapped[dict | None] = mapped_column(JSON)
    after_json: Mapped[dict | None] = mapped_column(JSON)
    summary: Mapped[str | None] = mapped_column(Text)
    request_id: Mapped[str | None] = mapped_column(String(80), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Supplier(TimestampMixin, Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    contact_person: Mapped[str | None] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(80))
    address: Mapped[str | None] = mapped_column(Text)
    vat_id: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)


class StockLocation(TimestampMixin, Base):
    __tablename__ = "stock_locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    type: Mapped[str] = mapped_column(String(80))


class InventoryItem(TimestampMixin, Base):
    __tablename__ = "inventory_items"
    __table_args__ = (
        CheckConstraint("current_stock >= 0", name="ck_inventory_items_current_stock_non_negative"),
        CheckConstraint("minimum_stock >= 0", name="ck_inventory_items_minimum_stock_non_negative"),
        CheckConstraint("reorder_point >= 0", name="ck_inventory_items_reorder_point_non_negative"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    category: Mapped[str | None] = mapped_column(String(120))
    unit_of_measure: Mapped[str] = mapped_column(String(40), default="kom")
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    current_stock: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    minimum_stock: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    expiration_tracking_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    lot_tracking_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    supplier: Mapped[Supplier | None] = relationship()


class InventoryBatch(TimestampMixin, Base):
    __tablename__ = "inventory_batches"
    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_inventory_batches_quantity_non_negative"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    lot_number: Mapped[str | None] = mapped_column(String(100), index=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    location_id: Mapped[int] = mapped_column(ForeignKey("stock_locations.id"))
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    item: Mapped[InventoryItem] = relationship()
    location: Mapped[StockLocation] = relationship()


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_stock_movements_quantity_positive"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_batches.id"))
    from_location_id: Mapped[int | None] = mapped_column(ForeignKey("stock_locations.id"))
    to_location_id: Mapped[int | None] = mapped_column(ForeignKey("stock_locations.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    movement_type: Mapped[str] = mapped_column(String(60), index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    related_appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"))
    related_invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    related_journey_id: Mapped[int | None] = mapped_column(ForeignKey("patient_journeys.id"), index=True)
    related_activity_id: Mapped[int | None] = mapped_column(ForeignKey("journey_activities.id"), index=True)
    serial_number: Mapped[str | None] = mapped_column(String(120))
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    item: Mapped[InventoryItem] = relationship()


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    status: Mapped[str] = mapped_column(String(60), default="draft")
    order_date: Mapped[date] = mapped_column(Date, default=date.today)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    supplier: Mapped[Supplier] = relationship()
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(cascade="all, delete-orphan", back_populates="order")


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        CheckConstraint("quantity_ordered > 0", name="ck_purchase_order_lines_quantity_ordered_positive"),
        CheckConstraint("quantity_received >= 0", name="ck_purchase_order_lines_quantity_received_non_negative"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"))
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=25)
    order: Mapped[PurchaseOrder] = relationship(back_populates="lines")
    item: Mapped[InventoryItem] = relationship()


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"))
    journey_id: Mapped[int | None] = mapped_column(ForeignKey("patient_journeys.id"), unique=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    invoice_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(60), default="draft")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    payment_status: Mapped[str] = mapped_column(String(60), default="unpaid")
    payment_method: Mapped[str | None] = mapped_column(String(80))
    operator: Mapped[str | None] = mapped_column(String(120))
    business_unit: Mapped[str | None] = mapped_column(String(120))
    register_id: Mapped[str | None] = mapped_column(String(80))
    vat_id: Mapped[str | None] = mapped_column(String(80))
    fiscalization_status: Mapped[str | None] = mapped_column(String(60), default="not_applicable")
    fiscalization_provider: Mapped[str | None] = mapped_column(String(80))
    fiscalization_reference: Mapped[str | None] = mapped_column(String(160))
    fiscalization_message: Mapped[str | None] = mapped_column(Text)
    fiscalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    patient: Mapped[Patient] = relationship()
    clinic: Mapped[Clinic | None] = relationship()
    appointment: Mapped[Appointment | None] = relationship()
    lines: Mapped[list["InvoiceLine"]] = relationship(cascade="all, delete-orphan", back_populates="invoice")
    payments: Mapped[list["PaymentTransaction"]] = relationship(cascade="all, delete-orphan", back_populates="invoice")


class InvoiceNumberSequence(Base):
    __tablename__ = "invoice_number_sequences"
    id: Mapped[int] = mapped_column(primary_key=True)
    business_unit: Mapped[str] = mapped_column(String(120), default="default", unique=True)
    next_number: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_invoice_lines_quantity_positive"),
        CheckConstraint("total >= 0", name="ck_invoice_lines_total_non_negative"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id"))
    inventory_item_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_items.id"))
    activity_id: Mapped[int | None] = mapped_column(ForeignKey("journey_activities.id"), index=True)
    source_key: Mapped[str | None] = mapped_column(String(160), unique=True)
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=25)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    invoice: Mapped[Invoice] = relationship(back_populates="lines")
    service: Mapped[Service | None] = relationship()
    inventory_item: Mapped[InventoryItem | None] = relationship()


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_payment_transactions_amount_positive"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    method: Mapped[str] = mapped_column(String(80))
    reference: Mapped[str | None] = mapped_column(String(160))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    invoice: Mapped[Invoice] = relationship(back_populates="payments")


class ServiceMaterialTemplate(TimestampMixin, Base):
    __tablename__ = "service_material_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    default_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=1)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    variable_quantity_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    item: Mapped[InventoryItem] = relationship()
    service: Mapped[Service] = relationship()
