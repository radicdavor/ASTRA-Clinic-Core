from decimal import Decimal
from pydantic import BaseModel
from app.schemas.common import AppointmentMaterialConsumptionLine

class ConsumableLine(AppointmentMaterialConsumptionLine):
    serial_number: str | None = None

class ConsumablesConfirm(BaseModel):
    lines: list[ConsumableLine] = []
    not_applicable: bool = False

class PaymentRecord(BaseModel):
    amount: Decimal
    method: str
    reference: str | None = None

class DeferPayment(BaseModel):
    reason: str

class ClosureOut(BaseModel):
    journey_id: int
    stage: str
    consumables_status: str
    billing_status: str
    payment_status: str
    invoice: dict | None = None
    consumables: list[dict] = []
