from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import InventoryBatch, Invoice, JourneyActivity, PatientJourney, StockMovement
from app.schemas.common import AppointmentMaterialConsumptionRequest, PaymentTransactionCreate
from app.schemas.journey_closure import ClosureOut, ConsumablesConfirm, DeferPayment, PaymentRecord
from app.services.appointment_materials import consume_appointment_materials
from app.services.billing import draft_invoice_from_journey, issue_invoice, record_payment
from app.services.journey_activities import get_activity
from app.services.patient_journeys import add_event, transition

router = APIRouter(prefix="/api/patient-journeys", tags=["journey-closure"])


def load_journey(db: Session, journey_id: int) -> PatientJourney:
    item = db.scalar(select(PatientJourney).options(joinedload(PatientJourney.appointment), selectinload(PatientJourney.blockers), selectinload(PatientJourney.activities)).where(PatientJourney.id == journey_id))
    if not item:
        raise HTTPException(404, detail="Tijek pacijenta nije pronađen")
    return item


def journey_invoice(db: Session, journey: PatientJourney) -> Invoice | None:
    return db.scalar(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(or_(Invoice.journey_id == journey.id, (Invoice.journey_id.is_(None)) & (Invoice.appointment_id == journey.appointment_id))).order_by(Invoice.id.desc()).limit(1))


def projection(db: Session, journey: PatientJourney) -> ClosureOut:
    invoice = journey_invoice(db, journey)
    movements = db.scalars(select(StockMovement).where(StockMovement.related_journey_id == journey.id).order_by(StockMovement.id)).all()
    invoice_data = None if not invoice else {"id": invoice.id, "number": invoice.invoice_number, "status": invoice.status, "payment_status": invoice.payment_status, "total": str(invoice.total_amount), "paid": str(sum((p.amount for p in invoice.payments), Decimal("0"))), "lines": [{"id": line.id, "activity_id": line.activity_id, "description": line.description, "total": str(line.total)} for line in invoice.lines]}
    consumables = [{"id": m.id, "activity_id": m.related_activity_id, "inventory_item_id": m.inventory_item_id, "quantity": str(m.quantity), "batch_id": m.batch_id, "serial_number": m.serial_number, "unit_cost": str(m.unit_cost) if m.unit_cost is not None else None} for m in movements]
    return ClosureOut(journey_id=journey.id, stage=journey.current_stage, consumables_status=journey.consumables_status, billing_status=journey.billing_status, payment_status=journey.payment_status, invoice=invoice_data, consumables=consumables)


@router.get("/{journey_id}/closure", response_model=ClosureOut)
def get_closure(journey_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("journey.read"))):
    return projection(db, load_journey(db, journey_id))


def _confirm_activity_consumables(db: Session, journey: PatientJourney, activity: JourneyActivity, payload: ConsumablesConfirm, actor: Actor, request: Request) -> ClosureOut:
    if journey.current_stage != "procedure_completed":
        raise HTTPException(409, detail="Materijal se potvrđuje nakon svih kliničkih aktivnosti")
    if activity.status not in {"completed", "not_performed", "cancelled"}:
        raise HTTPException(409, detail="Aktivnost još nije završena")
    if activity.consumables_status in {"confirmed", "not_applicable"}:
        raise HTTPException(409, detail="Materijal aktivnosti već je razriješen")
    if payload.not_applicable:
        if payload.lines:
            raise HTTPException(422, detail="Nije moguće poslati stavke i oznaku nije primjenjivo")
        activity.consumables_status = "not_applicable"
    else:
        if not payload.lines:
            raise HTTPException(422, detail="Upišite materijal ili označite da nije primjenjiv")
        if not activity.appointment:
            raise HTTPException(409, detail="Aktivnost nema termin za sljedivost materijala")
        request_payload = AppointmentMaterialConsumptionRequest(lines=[{"inventory_item_id": x.inventory_item_id, "quantity": x.quantity, "reason": x.reason} for x in payload.lines])
        movements = consume_appointment_materials(db, activity.appointment, request_payload, actor, request)
        serials = {x.inventory_item_id: x.serial_number for x in payload.lines}
        for movement in movements:
            movement.related_journey_id = journey.id
            movement.related_activity_id = activity.id
            movement.serial_number = serials.get(movement.inventory_item_id)
            batch = db.get(InventoryBatch, movement.batch_id) if movement.batch_id else None
            movement.unit_cost = batch.purchase_price if batch else None
        activity.consumables_status = "confirmed"
    unresolved = db.scalar(select(JourneyActivity.id).where(JourneyActivity.journey_id == journey.id, JourneyActivity.required.is_(True), JourneyActivity.status == "completed", JourneyActivity.consumables_status.notin_({"confirmed", "not_applicable"})).limit(1))
    if not unresolved:
        journey.consumables_status = "confirmed" if db.scalar(select(StockMovement.id).where(StockMovement.related_journey_id == journey.id).limit(1)) else "not_applicable"
        journey.billing_status = "ready"
        transition(db, journey, "awaiting_billing", actor, request, "Materijal svih aktivnosti je razriješen")
    add_event(db, journey, "activity_consumables_confirmed", "Materijal aktivnosti izričito je potvrđen", actor, request, metadata={"activity_id": activity.id, "status": activity.consumables_status})
    db.commit()
    return projection(db, journey)


@router.post("/{journey_id}/activities/{activity_id}/consumables/confirm", response_model=ClosureOut)
def confirm_activity_consumables(journey_id: int, activity_id: int, payload: ConsumablesConfirm, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("consumables.record"))):
    journey = load_journey(db, journey_id)
    return _confirm_activity_consumables(db, journey, get_activity(db, journey_id, activity_id), payload, actor, request)


@router.post("/{journey_id}/consumables/confirm", response_model=ClosureOut)
def confirm_consumables(journey_id: int, payload: ConsumablesConfirm, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("consumables.record"))):
    journey = load_journey(db, journey_id)
    activity = next((item for item in journey.activities if item.required and item.status == "completed" and item.consumables_status not in {"confirmed", "not_applicable"}), None)
    if not activity and journey.encounter_status == "completed":
        activity = next((item for item in journey.activities if item.required and item.consumables_status not in {"confirmed", "not_applicable"}), None)
        if activity and activity.status not in {"completed", "not_performed", "cancelled"}:
            activity.status = "completed"
    if not activity:
        raise HTTPException(409, detail="Nema nerazriješene dovršene aktivnosti")
    return _confirm_activity_consumables(db, journey, activity, payload, actor, request)


@router.post("/{journey_id}/billing/prepare", response_model=ClosureOut)
def prepare_billing(journey_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.write"))):
    journey = load_journey(db, journey_id)
    if journey.current_stage == "awaiting_payment" and journey_invoice(db, journey):
        return projection(db, journey)
    if journey.current_stage != "awaiting_billing" or journey.consumables_status not in {"confirmed", "not_applicable"}:
        raise HTTPException(409, detail="Naplata nije spremna")
    invoice, _ = draft_invoice_from_journey(db, journey)
    if invoice.status == "draft":
        issue_invoice(db, invoice)
    journey.billing_status = "invoice_created"
    journey.payment_status = "unpaid"
    transition(db, journey, "awaiting_payment", actor, request, "Račun za aktivnosti dolaska je izrađen")
    audit(db, "invoice_issued", "Invoice", invoice.id, "Izdan koordinirani račun za dolazak", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(invoice), request)
    db.commit()
    return projection(db, journey)


@router.post("/{journey_id}/payments", response_model=ClosureOut)
def add_payment(journey_id: int, payload: PaymentRecord, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("payment.record"))):
    journey = load_journey(db, journey_id)
    if journey.current_stage != "awaiting_payment":
        raise HTTPException(409, detail="Dolazak ne čeka plaćanje")
    invoice = journey_invoice(db, journey)
    if not invoice:
        raise HTTPException(409, detail="Račun nije izrađen")
    payment = record_payment(invoice, PaymentTransactionCreate(**payload.model_dump()), actor.user_id)
    db.add(payment); db.flush()
    journey.payment_status = invoice.payment_status
    if invoice.payment_status == "paid":
        journey.billing_status = "closed"
    audit(db, "payment_recorded", "PaymentTransaction", payment.id, "Evidentirano plaćanje dolaska", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(payment), request)
    add_event(db, journey, "payment_recorded", "Evidentirano plaćanje", actor, request, metadata={"amount": str(payment.amount), "method": payment.method})
    if invoice.payment_status == "paid" and "journey.transition" in actor.permissions:
        transition(db, journey, "completed", actor, request, "Puna uplata evidentirana; dolazak je završen")
    db.commit()
    return projection(db, journey)


@router.post("/{journey_id}/payments/defer", response_model=ClosureOut)
def defer_payment(journey_id: int, payload: DeferPayment, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("payment.record"))):
    journey = load_journey(db, journey_id)
    if journey.current_stage != "awaiting_payment" or not payload.reason.strip():
        raise HTTPException(409, detail="Odgoda plaćanja mora imati razlog i izdani račun")
    journey.payment_status = "deferred"; journey.billing_status = "closed"
    add_event(db, journey, "payment_deferred", "Plaćanje je izričito odgođeno", actor, request, metadata={"reason": payload.reason})
    if "journey.transition" in actor.permissions:
        transition(db, journey, "completed", actor, request, "Odgoda plaćanja je evidentirana; dolazak je završen")
    db.commit()
    return projection(db, journey)


@router.post("/{journey_id}/close", response_model=ClosureOut)
def close_journey(journey_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("journey.transition"))):
    journey = load_journey(db, journey_id)
    transition(db, journey, "completed", actor, request, "Dolazak je administrativno i financijski razriješen")
    audit(db, "journey_completed", "PatientJourney", journey.id, "Dolazak je završen", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(journey), request)
    db.commit()
    return projection(db, journey)
