from datetime import UTC, date
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.domain import Appointment, Invoice, InvoiceLine, InvoiceNumberSequence, JourneyActivity, PatientJourney, PaymentTransaction, Service
from app.schemas.common import InvoiceLineCreate, InvoiceLineUpdate, PaymentTransactionCreate
from app.services.fiscalization import FiscalizationProvider, get_fiscalization_provider
from app.services.inventory import ensure_positive
from app.services.clinic_time import utc_now


def calculate_line_total(quantity: Decimal, unit_price: Decimal) -> Decimal:
    return quantity * unit_price


def recalculate_invoice_total(invoice: Invoice) -> None:
    invoice.total_amount = sum((line.total for line in invoice.lines), Decimal("0"))
    paid = sum((payment.amount for payment in invoice.payments), Decimal("0"))
    if paid <= 0:
        invoice.payment_status = "unpaid"
        if invoice.status in {"paid", "partially_paid"}:
            invoice.status = "issued"
    elif paid < invoice.total_amount:
        invoice.payment_status = "partially_paid"
        invoice.status = "partially_paid"
    else:
        invoice.payment_status = "paid"
        invoice.status = "paid"


def ensure_invoice_editable(invoice: Invoice) -> None:
    if invoice.status != "draft":
        raise HTTPException(status_code=409, detail="Stavke se mogu mijenjati samo na draft racunu")


def ensure_invoice_payable(invoice: Invoice) -> None:
    if invoice.status not in {"issued", "partially_paid"}:
        raise HTTPException(status_code=409, detail="Placanje je dopusteno samo za izdane racune")


def next_invoice_number(db: Session, business_unit: str = "default") -> str:
    sequence = db.scalar(
        select(InvoiceNumberSequence)
        .where(InvoiceNumberSequence.business_unit == business_unit)
        .with_for_update()
    )
    if sequence is None:
        sequence = InvoiceNumberSequence(business_unit=business_unit, next_number=1)
        db.add(sequence)
        db.flush()
    number = sequence.next_number
    sequence.next_number += 1
    return f"ASTRA-{date.today():%Y%m%d}-{number:05d}"


def draft_invoice_number() -> str:
    return f"DRAFT-{uuid4().hex[:12].upper()}"


def load_invoice(db: Session, invoice_id: int) -> Invoice | None:
    return db.scalar(
        select(Invoice)
        .options(selectinload(Invoice.lines), selectinload(Invoice.payments))
        .where(Invoice.id == invoice_id)
    )


def draft_invoice_from_appointment(db: Session, appointment_id: int) -> tuple[Invoice, InvoiceLine | None, bool]:
    existing = db.scalar(
        select(Invoice)
        .options(selectinload(Invoice.lines), selectinload(Invoice.payments))
        .where(Invoice.appointment_id == appointment_id)
    )
    if existing:
        return existing, None, False
    appointment = db.scalar(select(Appointment).where(Appointment.id == appointment_id))
    if not appointment:
        raise HTTPException(status_code=404, detail="Termin nije pronaden")
    service = db.get(Service, appointment.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Usluga nije pronadena")
    invoice = Invoice(
        patient_id=appointment.patient_id,
        clinic_id=appointment.clinic_id,
        appointment_id=appointment.id,
        invoice_number=draft_invoice_number(),
        status="draft",
        payment_status="unpaid",
        total_amount=service.price,
    )
    db.add(invoice)
    db.flush()
    line = InvoiceLine(
        invoice=invoice,
        service_id=service.id,
        description=service.name,
        quantity=Decimal("1"),
        unit_price=service.price,
        vat_rate=Decimal("25"),
        total=service.price,
    )
    db.add(line)
    db.flush()
    return invoice, line, True


def draft_invoice_from_journey(db: Session, journey: PatientJourney) -> tuple[Invoice, bool]:
    existing = db.scalar(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.journey_id == journey.id))
    if existing:
        return existing, False
    activities = db.scalars(select(JourneyActivity).where(JourneyActivity.journey_id == journey.id, JourneyActivity.status == "completed").order_by(JourneyActivity.sequence)).all()
    if not activities:
        raise HTTPException(409, detail="Dolazak nema dovršenu aktivnost za naplatu")
    invoice = Invoice(patient_id=journey.patient_id, clinic_id=journey.clinic_id, appointment_id=journey.appointment_id, journey_id=journey.id, invoice_number=draft_invoice_number(), status="draft", payment_status="unpaid", total_amount=Decimal("0"))
    db.add(invoice)
    db.flush()
    for activity in activities:
        service = db.get(Service, activity.service_id)
        if not service:
            raise HTTPException(409, detail=f"Aktivnost {activity.id} nema valjanu uslugu")
        invoice.lines.append(InvoiceLine(activity_id=activity.id, source_key=f"activity:{activity.id}:service", service_id=service.id, description=service.name, quantity=Decimal("1"), unit_price=service.price, vat_rate=Decimal("25"), total=service.price))
    recalculate_invoice_total(invoice)
    db.flush()
    return invoice, True


def apply_fiscalization_result(invoice: Invoice, provider: FiscalizationProvider | None = None) -> None:
    provider = provider or get_fiscalization_provider()
    result = provider.fiscalize_invoice(invoice)
    invoice.fiscalization_provider = result.provider
    invoice.fiscalization_reference = result.reference
    invoice.fiscalization_message = result.message
    invoice.fiscalized_at = result.fiscalized_at
    invoice.fiscalization_status = "fiscalized" if result.success else "failed"


def issue_invoice(db: Session, invoice: Invoice, fiscalization_provider: FiscalizationProvider | None = None) -> None:
    if invoice.status != "draft":
        raise HTTPException(status_code=409, detail="Samo draft racun se moze izdati")
    if not invoice.lines:
        raise HTTPException(status_code=422, detail="Racun mora imati barem jednu stavku")
    if invoice.total_amount <= 0:
        raise HTTPException(status_code=422, detail="Racun mora imati pozitivan iznos")
    invoice.invoice_number = next_invoice_number(db, invoice.business_unit or "default")
    invoice.status = "issued"
    apply_fiscalization_result(invoice, fiscalization_provider)


def cancel_invoice(invoice: Invoice) -> None:
    if invoice.status == "cancelled":
        return
    if invoice.status == "paid":
        raise HTTPException(status_code=409, detail="Placeni racun se ne moze stornirati u MVP workflowu")
    if invoice.payments:
        raise HTTPException(status_code=409, detail="Racun s placanjima se ne moze stornirati")
    if invoice.status not in {"draft", "issued"}:
        raise HTTPException(status_code=409, detail="Racun se ne moze stornirati iz trenutnog statusa")
    invoice.status = "cancelled"


def add_invoice_line(invoice: Invoice, payload: InvoiceLineCreate) -> InvoiceLine:
    ensure_invoice_editable(invoice)
    ensure_positive(payload.quantity)
    line = InvoiceLine(invoice_id=invoice.id, **payload.model_dump(), total=calculate_line_total(payload.quantity, payload.unit_price))
    invoice.lines.append(line)
    recalculate_invoice_total(invoice)
    return line


def update_invoice_line(invoice: Invoice, line: InvoiceLine, payload: InvoiceLineUpdate) -> None:
    ensure_invoice_editable(invoice)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(line, key, value)
    ensure_positive(line.quantity)
    line.total = calculate_line_total(line.quantity, line.unit_price)
    recalculate_invoice_total(invoice)


def delete_invoice_line(invoice: Invoice, line: InvoiceLine) -> None:
    ensure_invoice_editable(invoice)
    invoice.lines.remove(line)
    recalculate_invoice_total(invoice)


def record_payment(invoice: Invoice, payload: PaymentTransactionCreate, created_by: int | None) -> PaymentTransaction:
    ensure_invoice_payable(invoice)
    ensure_positive(payload.amount)
    paid = sum((payment.amount for payment in invoice.payments), Decimal("0"))
    if paid + payload.amount > invoice.total_amount:
        raise HTTPException(status_code=409, detail="Uplata prelazi ukupni iznos racuna")
    paid_at = payload.paid_at or utc_now()
    if paid_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="Vrijeme plaćanja mora sadržavati vremensku zonu")
    paid_at = paid_at.astimezone(UTC)
    payment = PaymentTransaction(
        invoice_id=invoice.id,
        amount=payload.amount,
        method=payload.method,
        reference=payload.reference,
        paid_at=paid_at,
        created_by=created_by,
    )
    invoice.payments.append(payment)
    recalculate_invoice_total(invoice)
    return payment


def mark_invoice_paid(invoice: Invoice, method: str | None, created_by: int | None) -> PaymentTransaction | None:
    paid = sum((payment.amount for payment in invoice.payments), Decimal("0"))
    remaining = invoice.total_amount - paid
    if remaining <= 0:
        recalculate_invoice_total(invoice)
        return None
    return record_payment(invoice, PaymentTransactionCreate(amount=remaining, method=method or "manual"), created_by)
