from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import CurrentUserContext
from app.models.domain import Appointment, Invoice, PaymentTransaction


def active_clinic_invoice_statement(context: CurrentUserContext):
    if context.active_clinic_id is None:
        raise HTTPException(403, detail="Aktivna klinika nije razriješena")
    return (
        select(Invoice)
        .options(selectinload(Invoice.lines), selectinload(Invoice.payments))
        .where(Invoice.clinic_id == context.active_clinic_id)
    )


def get_active_clinic_invoice(
    db: Session,
    invoice_id: int,
    context: CurrentUserContext,
) -> Invoice:
    invoice = db.scalar(active_clinic_invoice_statement(context).where(Invoice.id == invoice_id))
    if invoice is None:
        raise HTTPException(404, detail="Račun nije pronađen")
    return invoice


def get_active_clinic_appointment(
    db: Session,
    appointment_id: int,
    context: CurrentUserContext,
) -> Appointment:
    if context.active_clinic_id is None:
        raise HTTPException(403, detail="Aktivna klinika nije razriješena")
    appointment = db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == context.active_clinic_id,
        )
    )
    if appointment is None:
        raise HTTPException(404, detail="Termin nije pronađen")
    return appointment


def get_active_clinic_payment(
    db: Session,
    payment_id: int,
    context: CurrentUserContext,
) -> PaymentTransaction:
    if context.active_clinic_id is None:
        raise HTTPException(403, detail="Aktivna klinika nije razriješena")
    payment = db.scalar(
        select(PaymentTransaction)
        .join(Invoice, Invoice.id == PaymentTransaction.invoice_id)
        .where(
            PaymentTransaction.id == payment_id,
            Invoice.clinic_id == context.active_clinic_id,
        )
    )
    if payment is None:
        raise HTTPException(404, detail="Plaćanje nije pronađeno")
    return payment
