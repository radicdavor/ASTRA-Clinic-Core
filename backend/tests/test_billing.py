from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.domain import Invoice, InvoiceLine, Patient
from app.schemas.common import InvoiceLineCreate, InvoiceLineUpdate, PaymentTransactionCreate
from app.services.billing import add_invoice_line, delete_invoice_line, draft_invoice_from_appointment, issue_invoice, mark_invoice_paid, record_payment, update_invoice_line
from tests.factories import appointment


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
    issue_invoice(db, invoice)

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
    issue_invoice(db, invoice)

    with pytest.raises(HTTPException) as exc:
        record_payment(invoice, PaymentTransactionCreate(amount=Decimal("101"), method="cash"), created_by=1)

    assert exc.value.status_code == 409
    assert invoice.payment_status == "unpaid"
    assert invoice.status == "issued"


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
    issue_invoice(db, invoice)

    payment = mark_invoice_paid(invoice, "cash", created_by=1)
    db.add(payment)
    db.flush()
    second_payment = mark_invoice_paid(invoice, "cash", created_by=1)

    assert second_payment is None
    assert len(invoice.payments) == 1
    assert invoice.payment_status == "paid"


def test_draft_invoice_cannot_receive_payment(db):
    invoice = make_invoice(db)

    with pytest.raises(HTTPException) as exc:
        record_payment(invoice, PaymentTransactionCreate(amount=Decimal("10"), method="cash"), created_by=1)

    assert exc.value.status_code == 409


def test_cancelled_invoice_cannot_receive_payment(db):
    invoice = make_invoice(db)
    invoice.status = "cancelled"

    with pytest.raises(HTTPException) as exc:
        record_payment(invoice, PaymentTransactionCreate(amount=Decimal("10"), method="cash"), created_by=1)

    assert exc.value.status_code == 409


def test_issued_invoice_lines_cannot_be_changed(db):
    invoice = make_invoice(db)
    issue_invoice(db, invoice)
    line = invoice.lines[0]

    with pytest.raises(HTTPException):
        add_invoice_line(invoice, InvoiceLineCreate(description="Blocked", quantity=Decimal("1"), unit_price=Decimal("1")))
    with pytest.raises(HTTPException):
        update_invoice_line(invoice, line, InvoiceLineUpdate(description="Blocked"))
    with pytest.raises(HTTPException):
        delete_invoice_line(invoice, line)


def test_issue_requires_line_and_positive_total(db):
    empty = make_invoice(db, total=Decimal("0"), number="DRAFT-EMPTY")
    for line in list(empty.lines):
        empty.lines.remove(line)
        db.delete(line)
    db.flush()

    with pytest.raises(HTTPException) as exc:
        issue_invoice(db, empty)

    assert exc.value.status_code == 422


def test_draft_invoice_from_appointment_creates_draft_and_reuses_existing(db):
    appt = appointment(db)

    invoice, line, created = draft_invoice_from_appointment(db, appt.id)
    second, second_line, second_created = draft_invoice_from_appointment(db, appt.id)

    assert created is True
    assert line is not None
    assert invoice.invoice_number.startswith("DRAFT-")
    assert invoice.lines[0].description == appt.service.name
    assert second.id == invoice.id
    assert second_line is None
    assert second_created is False
