from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit
from app.models.domain import InventoryBatch, InventoryItem, StockMovement


def recalculate_stock(db: Session, item_id: int) -> None:
    total = sum(batch.quantity for batch in db.scalars(select(InventoryBatch).where(InventoryBatch.inventory_item_id == item_id)))
    item = db.get(InventoryItem, item_id)
    if item:
        item.current_stock = total


def consume_fefo(db: Session, item_id: int, quantity: Decimal, appointment_id: int | None = None, reason: str = "Potrošnja materijala") -> list[StockMovement]:
    remaining = quantity
    movements: list[StockMovement] = []
    batches = db.scalars(
        select(InventoryBatch)
        .where(InventoryBatch.inventory_item_id == item_id, InventoryBatch.quantity > 0)
        .order_by(InventoryBatch.expiration_date.asc().nulls_last(), InventoryBatch.id.asc())
    ).all()
    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.quantity, remaining)
        batch.quantity -= take
        remaining -= take
        movement = StockMovement(
            inventory_item_id=item_id,
            batch_id=batch.id,
            from_location_id=batch.location_id,
            quantity=take,
            movement_type="consumption",
            reason=reason,
            related_appointment_id=appointment_id,
        )
        db.add(movement)
        movements.append(movement)
    if remaining > 0:
        raise HTTPException(status_code=409, detail="Nedovoljno zaliha za FEFO potrošnju")
    recalculate_stock(db, item_id)
    audit(db, "create", "StockMovement", item_id, f"FEFO potrošnja: {quantity}")
    return movements


def expiring_batches(db: Session, days: int = 30) -> list[InventoryBatch]:
    until = date.today() + timedelta(days=days)
    return db.scalars(select(InventoryBatch).where(InventoryBatch.expiration_date <= until).order_by(InventoryBatch.expiration_date)).all()
