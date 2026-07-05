from __future__ import annotations

from datetime import date as DateType, datetime as DateTimeType, time as TimeType
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str]
    expires_at: DateTimeType | None = None


class ApiKeyCreated(ORMModel):
    id: int
    name: str
    scopes: list[str]
    active: bool
    expires_at: DateTimeType | None
    key: str


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: DateType | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None


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


class InventoryBatchCreate(BaseModel):
    inventory_item_id: int
    lot_number: str | None = None
    expiration_date: DateType | None = None
    quantity: Decimal
    location_id: int
    purchase_price: Decimal = Decimal("0")
    supplier_id: int | None = None


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


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    status: str = "draft"
    order_date: DateType | None = None
    expected_delivery_date: DateType | None = None
    total_amount: Decimal = Decimal("0")
    notes: str | None = None


class InvoiceCreate(BaseModel):
    patient_id: int
    appointment_id: int | None = None
    invoice_number: str
    invoice_date: DateType | None = None
    status: str = "draft"
    total_amount: Decimal = Decimal("0")
    payment_status: str = "unpaid"
    payment_method: str | None = None
    notes: str | None = None


class ServiceMaterialCreate(BaseModel):
    inventory_item_id: int
    default_quantity: Decimal = Decimal("1")
    required: bool = True
    variable_quantity_allowed: bool = False
    notes: str | None = None
