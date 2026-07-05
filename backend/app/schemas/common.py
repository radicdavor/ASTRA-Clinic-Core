from __future__ import annotations

from datetime import date as DateType, datetime as DateTimeType, time as TimeType
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str

    model_config = ConfigDict(json_schema_extra={"example": {"detail": "Opis greske"}})


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
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None

    model_config = ConfigDict(json_schema_extra={"example": {"first_name": "Petra", "last_name": "Novak", "date_of_birth": "1990-01-15", "email": "petra.novak@example.com", "phone": "+385 91 111 2222"}})


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: DateType | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None


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


class AppointmentCreate(BaseModel):
    patient_id: int
    service_id: int
    provider_id: int
    room_id: int
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
    date: DateType | None = None
    start_time: TimeType | None = None
    end_time: TimeType | None = None
    duration_minutes: int | None = None
    status: str | None = None
    source: str | None = None
    notes: str | None = None


class AppointmentOut(AppointmentCreate, ORMModel):
    id: int
    created_at: DateTimeType
    updated_at: DateTimeType
    patient: PatientOut | None = None
    service: ServiceOut | None = None


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
