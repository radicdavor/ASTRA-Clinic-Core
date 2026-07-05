from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.domain import Invoice, InvoiceLine, Patient
from app.schemas.common import InvoiceLineCreate, PaymentTransactionCreate
from app.services.billing import add_invoice_line, issue_invoice, mark_invoice_paid, record_payment


def make_invoice(db, total=Decimal("100"), number="DRAFT-TEST"):
    patient = Patient(first_name="Test", last_name="Patient")
    db.add(patient)
    db.flush()
    invoice = Invoice(patient_id=patient.id, invoice_number=number, status="draft", payment_status="unpaid", total_amount=total)
    db.add(invoice)
    db.flush()
    line = InvoiceLine(invoice_id=invoice.id, description="Service", quantity=Decimal("1"), unit_price=total, total=total)
    invoice.lines.append(line)
    db.add(line)
    db.flush()
    return invoice


def test_add_invoice_line_recalculates_total(db):
    invoice = make_invoice(db)

    line = add_invoice_line(invoice, InvoiceLineCreate(description="Extra", quantity=Decimal("2"), unit_price=Decimal("25")))
    db.add(line)
    db.flush()

    assert invoice.total_amount == Decimal("150")


def test_partial_and_full_payment_status(db):
    invoice = make_invoice(db)

    first = record_payment(invoice, PaymentTransactionCreate(amount=Decimal("40"), method="cash"), created_by=1)
    db.add(first)
    db.flush()
    assert invoice.payment_status == "partially_paid"
    assert invoice.status == "partially_paid"

    second = record_payment(invoice, PaymentTransactionCreate(amount=Decimal("60"), method="cash"), created_by=1)
    db.add(second)
    db.flush()
    assert invoice.payment_status == "paid"
    assert invoice.status == "paid"


def test_overpayment_is_rejected(db):
    invoice = make_invoice(db)

    with pytest.raises(HTTPException) as exc:
        record_payment(invoice, PaymentTransactionCreate(amount=Decimal("101"), method="cash"), created_by=1)

    assert exc.value.status_code == 409


def test_issue_invoice_assigns_unique_numbers(db):
    first = make_invoice(db)
    second = make_invoice(db, number="DRAFT-TEST-2")

    issue_invoice(db, first)
    issue_invoice(db, second)

    assert first.status == "issued"
    assert second.status == "issued"
    assert first.invoice_number != second.invoice_number
    assert first.invoice_number.startswith("ASTRA-")


def test_mark_paid_creates_remaining_payment_once(db):
    invoice = make_invoice(db)

    payment = mark_invoice_paid(invoice, "cash", created_by=1)
    db.add(payment)
    db.flush()
    second_payment = mark_invoice_paid(invoice, "cash", created_by=1)

    assert second_payment is None
    assert len(invoice.payments) == 1
    assert invoice.payment_status == "paid"
