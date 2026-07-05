from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import InventoryBatch, InventoryItem, StockMovement, StockMovementType


def ensure_positive(quantity: Decimal) -> None:
    if quantity <= 0:
        raise HTTPException(status_code=422, detail="Kolicina mora biti veca od nule")


def recalculate_stock(db: Session, item_id: int) -> None:
    total = sum(batch.quantity for batch in db.scalars(select(InventoryBatch).where(InventoryBatch.inventory_item_id == item_id)))
    item = db.get(InventoryItem, item_id)
    if item:
        item.current_stock = total


def recalculate_all_stock(db: Session) -> None:
    for item_id in db.scalars(select(InventoryItem.id)).all():
        recalculate_stock(db, item_id)


def ensure_batch_available(batch: InventoryBatch, quantity: Decimal) -> None:
    ensure_positive(quantity)
    if batch.quantity < quantity:
        raise HTTPException(status_code=409, detail="Serija nema dovoljno zalihe")


def consume_fefo(
    db: Session,
    item_id: int,
    quantity: Decimal,
    appointment_id: int | None = None,
    reason: str = "Potrosnja materijala",
    user_id: int | None = None,
) -> list[StockMovement]:
    ensure_positive(quantity)
    available = sum(
        batch.quantity
        for batch in db.scalars(select(InventoryBatch).where(InventoryBatch.inventory_item_id == item_id, InventoryBatch.quantity > 0))
    )
    if available < quantity:
        raise HTTPException(status_code=409, detail="Nedovoljno zaliha za FEFO potrosnju")

    remaining = quantity
    movements: list[StockMovement] = []
    batches = db.scalars(
        select(InventoryBatch)
        .where(InventoryBatch.inventory_item_id == item_id, InventoryBatch.quantity > 0)
        .order_by(InventoryBatch.expiration_date.asc().nulls_last(), InventoryBatch.id.asc())
        .with_for_update()
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
            movement_type=StockMovementType.consumption.value,
            reason=reason,
            related_appointment_id=appointment_id,
            created_by=user_id,
        )
        db.add(movement)
        movements.append(movement)
    recalculate_stock(db, item_id)
    return movements


def transfer_batch(db: Session, batch: InventoryBatch, to_location_id: int, quantity: Decimal, reason: str | None, user_id: int | None = None) -> list[StockMovement]:
    if not reason:
        raise HTTPException(status_code=422, detail="Transfer mora imati razlog")
    ensure_batch_available(batch, quantity)
    batch.quantity -= quantity
    target_batch = db.scalar(
        select(InventoryBatch)
        .where(
            InventoryBatch.inventory_item_id == batch.inventory_item_id,
            InventoryBatch.lot_number == batch.lot_number,
            InventoryBatch.expiration_date == batch.expiration_date,
            InventoryBatch.location_id == to_location_id,
            InventoryBatch.purchase_price == batch.purchase_price,
            InventoryBatch.supplier_id == batch.supplier_id,
        )
        .with_for_update()
    )
    if target_batch:
        target_batch.quantity += quantity
    else:
        target_batch = InventoryBatch(
            inventory_item_id=batch.inventory_item_id,
            lot_number=batch.lot_number,
            expiration_date=batch.expiration_date,
            quantity=quantity,
            location_id=to_location_id,
            purchase_price=batch.purchase_price,
            supplier_id=batch.supplier_id,
        )
        db.add(target_batch)
    db.flush()
    movements = [
        StockMovement(inventory_item_id=batch.inventory_item_id, batch_id=batch.id, from_location_id=batch.location_id, quantity=quantity, movement_type=StockMovementType.transfer_out.value, reason=reason, created_by=user_id),
        StockMovement(inventory_item_id=batch.inventory_item_id, batch_id=target_batch.id, to_location_id=to_location_id, quantity=quantity, movement_type=StockMovementType.transfer_in.value, reason=reason, created_by=user_id),
    ]
    db.add_all(movements)
    recalculate_stock(db, batch.inventory_item_id)
    return movements


def expiring_batches(db: Session, days: int = 30) -> list[InventoryBatch]:
    until = date.today() + timedelta(days=days)
    return db.scalars(select(InventoryBatch).where(InventoryBatch.expiration_date <= until).order_by(InventoryBatch.expiration_date)).all()
