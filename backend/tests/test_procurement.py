from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.domain import InventoryBatch, InventoryItem, PurchaseOrder, PurchaseOrderLine, StockLocation, StockMovement, Supplier
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


def test_failed_receive_rolls_back_all_lines_before_mutation(db):
    supplier = Supplier(name="Supplier")
    item_a = InventoryItem(sku="POA", name="PO item A")
    item_b = InventoryItem(sku="POB", name="PO item B")
    location = StockLocation(name="Main", type="main")
    db.add_all([supplier, item_a, item_b, location])
    db.flush()
    order = PurchaseOrder(supplier_id=supplier.id, status="ordered")
    db.add(order)
    db.flush()
    line_a = PurchaseOrderLine(purchase_order_id=order.id, inventory_item_id=item_a.id, quantity_ordered=Decimal("2"), unit_price=Decimal("10"))
    line_b = PurchaseOrderLine(purchase_order_id=order.id, inventory_item_id=item_b.id, quantity_ordered=Decimal("1"), unit_price=Decimal("10"))
    order.lines.extend([line_a, line_b])
    db.add_all([line_a, line_b])
    db.flush()

    with pytest.raises(HTTPException):
        receive_purchase_order(
            db,
            order,
            PurchaseOrderReceiveRequest(lines=[
                {"purchase_order_line_id": line_a.id, "quantity_received": Decimal("1"), "location_id": location.id},
                {"purchase_order_line_id": line_b.id, "quantity_received": Decimal("2"), "location_id": location.id},
            ]),
            user_id=1,
        )

    assert line_a.quantity_received == 0
    assert db.query(InventoryBatch).count() == 0
    assert db.query(StockMovement).count() == 0
