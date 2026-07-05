from collections import defaultdict
from decimal import Decimal

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor
from app.models.domain import Appointment, InventoryBatch, InventoryItem, ServiceMaterialTemplate, StockMovement
from app.schemas.common import AppointmentMaterialConsumptionRequest
from app.services.inventory import consume_fefo, ensure_positive


def _audit_actor(db: Session, action: str, entity_type: str, entity_id: int | None, summary: str, actor: Actor, request: Request | None, before=None, after=None) -> None:
    audit(db, action, entity_type, entity_id, summary, actor.user_id, actor.actor_type, actor.api_key_id, before, after, request)


def _requested_lines(db: Session, appointment: Appointment, payload: AppointmentMaterialConsumptionRequest | None):
    templates = db.scalars(select(ServiceMaterialTemplate).where(ServiceMaterialTemplate.service_id == appointment.service_id)).all()
    if payload and payload.lines is not None:
        requested = payload.lines
        provided_item_ids = {line.inventory_item_id for line in requested}
        missing_variable = [template for template in templates if template.required and template.variable_quantity_allowed and template.inventory_item_id not in provided_item_ids]
        if missing_variable:
            raise HTTPException(status_code=422, detail="Obavezni varijabilni materijal zahtijeva unesenu kolicinu")
        return requested

    if any(template.required and template.variable_quantity_allowed for template in templates):
        raise HTTPException(status_code=422, detail="Obavezni varijabilni materijal zahtijeva unesenu kolicinu")

    return [
        type("ConsumptionLine", (), {"inventory_item_id": template.inventory_item_id, "quantity": template.default_quantity, "reason": "Potrosnja po terminu"})()
        for template in templates
        if template.required and not template.variable_quantity_allowed
    ]


def _validate_stock_before_mutation(db: Session, requested) -> None:
    required_by_item: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    for line in requested:
        ensure_positive(line.quantity)
        required_by_item[line.inventory_item_id] += line.quantity

    for item_id, required_quantity in required_by_item.items():
        available = sum(
            batch.quantity
            for batch in db.scalars(select(InventoryBatch).where(InventoryBatch.inventory_item_id == item_id, InventoryBatch.quantity > 0))
        )
        if available < required_quantity:
            raise HTTPException(status_code=409, detail="Nedovoljno zaliha za FEFO potrosnju")


def consume_appointment_materials(db: Session, appointment: Appointment, payload: AppointmentMaterialConsumptionRequest | None, actor: Actor, request: Request | None) -> list[StockMovement]:
    requested = _requested_lines(db, appointment, payload)
    _validate_stock_before_mutation(db, requested)

    movements: list[StockMovement] = []
    for line in requested:
        before_item = snapshot(db.get(InventoryItem, line.inventory_item_id))
        movements.extend(consume_fefo(db, line.inventory_item_id, line.quantity, appointment.id, line.reason or "Potrosnja po terminu", actor.user_id))
        after_item = snapshot(db.get(InventoryItem, line.inventory_item_id))
        _audit_actor(db, "update", "InventoryItem", line.inventory_item_id, "Potrosnja materijala po terminu", actor, request, before_item, after_item)
    db.flush()
    for movement in movements:
        _audit_actor(db, "create", "StockMovement", movement.id, "Potrosnja materijala po terminu", actor, request, None, snapshot(movement))
    return movements
