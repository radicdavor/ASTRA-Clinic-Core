from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.domain import InventoryItem, PurchaseOrder, PurchaseOrderLine, StockLocation, Supplier
from app.schemas.common import PurchaseOrderReceiveRequest
from app.services.procurement import recalculate_purchase_order_total, receive_purchase_order


def test_partial_receive_creates_batch_movement_and_updates_status(db):
    supplier = Supplier(name="Supplier")
    item = InventoryItem(sku="PO", name="PO item", lot_tracking_enabled=True, expiration_tracking_enabled=True)
    location = StockLocation(name="Main", type="main")
    db.add_all([supplier, item, location])
    db.flush()
    order = PurchaseOrder(supplier_id=supplier.id, status="ordered")
    db.add(order)
    db.flush()
    line = PurchaseOrderLine(purchase_order_id=order.id, inventory_item_id=item.id, quantity_ordered=Decimal("5"), unit_price=Decimal("10"))
    order.lines.append(line)
    db.add(line)
    db.flush()
    recalculate_purchase_order_total(order)

    received = receive_purchase_order(
        db,
        order,
        PurchaseOrderReceiveRequest(lines=[{
            "purchase_order_line_id": line.id,
            "quantity_received": Decimal("2"),
            "lot_number": "LOT-1",
            "expiration_date": "2027-01-01",
            "location_id": location.id,
            "purchase_price": Decimal("10"),
        }]),
        user_id=1,
    )

    assert len(received) == 1
    assert line.quantity_received == Decimal("2")
    assert order.status == "partially_received"
    assert item.current_stock == Decimal("2")


def test_over_receive_is_rejected(db):
    supplier = Supplier(name="Supplier")
    item = InventoryItem(sku="PO2", name="PO item 2")
    location = StockLocation(name="Main", type="main")
    db.add_all([supplier, item, location])
    db.flush()
    order = PurchaseOrder(supplier_id=supplier.id, status="ordered")
    db.add(order)
    db.flush()
    line = PurchaseOrderLine(purchase_order_id=order.id, inventory_item_id=item.id, quantity_ordered=Decimal("1"), unit_price=Decimal("10"))
    order.lines.append(line)
    db.add(line)
    db.flush()

    with pytest.raises(HTTPException) as exc:
        receive_purchase_order(
            db,
            order,
            PurchaseOrderReceiveRequest(lines=[{
                "purchase_order_line_id": line.id,
                "quantity_received": Decimal("2"),
                "location_id": location.id,
            }]),
            user_id=1,
        )

    assert exc.value.status_code == 409
