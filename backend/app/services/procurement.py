from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.domain import InventoryBatch, InventoryItem, PurchaseOrder, PurchaseOrderLine, StockMovement, StockMovementType
from app.schemas.common import PurchaseOrderReceiveRequest
from app.services.inventory import ensure_positive, recalculate_stock


def calculate_line_total(quantity: Decimal, unit_price: Decimal) -> Decimal:
    return quantity * unit_price


def recalculate_purchase_order_total(order: PurchaseOrder) -> None:
    order.total_amount = sum(calculate_line_total(line.quantity_ordered, line.unit_price) for line in order.lines)


def derive_purchase_order_status(order: PurchaseOrder) -> str:
    if not order.lines or all(line.quantity_received <= 0 for line in order.lines):
        return order.status if order.status in {"draft", "ordered"} else "ordered"
    if all(line.quantity_received >= line.quantity_ordered for line in order.lines):
        return "received"
    return "partially_received"


def receive_purchase_order(db: Session, order: PurchaseOrder, payload: PurchaseOrderReceiveRequest, user_id: int | None) -> list[tuple[PurchaseOrderLine, InventoryBatch, StockMovement]]:
    validated: list[tuple[PurchaseOrderLine, InventoryItem, object]] = []
    for receive_line in payload.lines:
        ensure_positive(receive_line.quantity_received)
        line = db.get(PurchaseOrderLine, receive_line.purchase_order_line_id)
        if not line or line.purchase_order_id != order.id:
            raise HTTPException(status_code=422, detail="Stavka ne pripada narudzbenici")
        if line.quantity_received + receive_line.quantity_received > line.quantity_ordered:
            raise HTTPException(status_code=409, detail="Zaprimanje prelazi narucenu kolicinu")
        item = db.get(InventoryItem, line.inventory_item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Artikl nije pronaden")
        if item.lot_tracking_enabled and not receive_line.lot_number:
            raise HTTPException(status_code=422, detail="LOT broj je obavezan za ovaj artikl")
        if item.expiration_tracking_enabled and not receive_line.expiration_date:
            raise HTTPException(status_code=422, detail="Rok trajanja je obavezan za ovaj artikl")
        validated.append((line, item, receive_line))

    received: list[tuple[PurchaseOrderLine, InventoryBatch, StockMovement]] = []
    for line, _item, receive_line in validated:
        batch = InventoryBatch(
            inventory_item_id=line.inventory_item_id,
            lot_number=receive_line.lot_number,
            expiration_date=receive_line.expiration_date,
            quantity=receive_line.quantity_received,
            location_id=receive_line.location_id,
            purchase_price=receive_line.purchase_price if receive_line.purchase_price is not None else line.unit_price,
            supplier_id=order.supplier_id,
        )
        db.add(batch)
        db.flush()
        movement = StockMovement(
            inventory_item_id=line.inventory_item_id,
            batch_id=batch.id,
            to_location_id=batch.location_id,
            quantity=batch.quantity,
            movement_type=StockMovementType.purchase_receipt.value,
            reason=f"Zaprimanje PO-{order.id}",
            created_by=user_id,
        )
        db.add(movement)
        line.quantity_received += receive_line.quantity_received
        recalculate_stock(db, line.inventory_item_id)
        received.append((line, batch, movement))
    order.status = derive_purchase_order_status(order)
    recalculate_purchase_order_total(order)
    return received
