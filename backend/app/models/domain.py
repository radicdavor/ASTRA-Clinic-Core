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


class Patient(TimestampMixin, Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), index=True)
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    oib: Mapped[str | None] = mapped_column(String(11), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)


class Provider(TimestampMixin, Base):
    __tablename__ = "providers"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    specialty: Mapped[str | None] = mapped_column(String(120))
    staff_role: Mapped[str] = mapped_column(String(60), default="physician", index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    clinic: Mapped["Clinic | None"] = relationship()


class Room(TimestampMixin, Base):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    type: Mapped[str | None] = mapped_column(String(80))
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    clinic: Mapped["Clinic | None"] = relationship()
    allowed_services: Mapped[list["Service"]] = relationship(secondary=room_services, back_populates="allowed_rooms")


class Clinic(TimestampMixin, Base):
    __tablename__ = "clinics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


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


class ClinicalDocument(TimestampMixin, Base):
    __tablename__ = "clinical_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    document_type: Mapped[str] = mapped_column(String(60), index=True)
    origin: Mapped[str | None] = mapped_column(String(180))
    document_date: Mapped[date | None] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(String(220), index=True)
    author: Mapped[str | None] = mapped_column(String(160))
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
    patient: Mapped[Patient] = relationship()
    appointment: Mapped[Appointment | None] = relationship()
    reviewer: Mapped[User | None] = relationship()


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


class Service(TimestampMixin, Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    code: Mapped[str | None] = mapped_column(String(80), unique=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    module_id: Mapped[int | None] = mapped_column(ForeignKey("modules.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    module: Mapped[Module | None] = relationship()
    allowed_rooms: Mapped[list[Room]] = relationship(secondary=room_services, back_populates="allowed_services")


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
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
    episode: Mapped[ClinicalEpisode | None] = relationship()


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
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"))
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
