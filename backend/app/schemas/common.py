from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None


class PatientOut(PatientCreate, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


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
    date: date
    start_time: time
    end_time: time
    duration_minutes: int
    status: str = "scheduled"
    source: str = "manual"
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    patient_id: int | None = None
    service_id: int | None = None
    provider_id: int | None = None
    room_id: int | None = None
    date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    status: str | None = None
    source: str | None = None
    notes: str | None = None


class AppointmentOut(AppointmentCreate, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
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
    expiration_date: date | None = None
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
    order_date: date | None = None
    expected_delivery_date: date | None = None
    total_amount: Decimal = Decimal("0")
    notes: str | None = None


class InvoiceCreate(BaseModel):
    patient_id: int
    appointment_id: int | None = None
    invoice_number: str
    invoice_date: date | None = None
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
