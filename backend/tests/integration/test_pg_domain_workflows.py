from decimal import Decimal
from datetime import date

import pytest
from fastapi import HTTPException

from app.models.domain import InventoryBatch, InventoryItem, PurchaseOrder, PurchaseOrderLine, ServiceMaterialTemplate, StockLocation, StockMovement, Supplier
from app.schemas.common import PurchaseOrderReceiveRequest
from app.services.inventory import consume_fefo, transfer_batch
from app.services.procurement import receive_purchase_order
from tests.factories import appointment, service, stock_item_with_batch


pytestmark = pytest.mark.integration


def test_pg_fefo_consumes_earliest_expiration_and_null_last(pg_db):
    item = InventoryItem(sku="PG-FEFO", name="PG FEFO")
    location = StockLocation(name="PG Main", type="main")
    pg_db.add_all([item, location])
    pg_db.flush()
    null_exp = InventoryBatch(inventory_item_id=item.id, quantity=Decimal("5"), location_id=location.id)
    early = InventoryBatch(inventory_item_id=item.id, expiration_date=date(2027, 1, 1), quantity=Decimal("5"), location_id=location.id)
    pg_db.add_all([null_exp, early])
    pg_db.flush()

    consume_fefo(pg_db, item.id, Decimal("6"))

    assert early.quantity == Decimal("0")
    assert null_exp.quantity == Decimal("4")


def test_pg_transfer_merges_into_existing_target_batch(pg_db):
    item = InventoryItem(sku="PG-TR", name="PG Transfer")
    source = StockLocation(name="PG Source", type="main")
    target = StockLocation(name="PG Target", type="room")
    pg_db.add_all([item, source, target])
    pg_db.flush()
    source_batch = InventoryBatch(inventory_item_id=item.id, lot_number="LOT", expiration_date=date(2027, 1, 1), quantity=Decimal("5"), location_id=source.id, purchase_price=Decimal("10"))
    target_batch = InventoryBatch(inventory_item_id=item.id, lot_number="LOT", expiration_date=date(2027, 1, 1), quantity=Decimal("1"), location_id=target.id, purchase_price=Decimal("10"))
    pg_db.add_all([source_batch, target_batch])
    pg_db.flush()

    transfer_batch(pg_db, source_batch, target.id, Decimal("2"), "PG transfer")

    assert source_batch.quantity == Decimal("3")
    assert target_batch.quantity == Decimal("3")
    assert pg_db.query(InventoryBatch).filter_by(inventory_item_id=item.id).count() == 2


def test_pg_purchase_receive_invalid_line_creates_no_batches_or_movements(pg_db):
    supplier = Supplier(name="PG Supplier")
    item_a = InventoryItem(sku="PG-PO-A", name="PG PO A")
    item_b = InventoryItem(sku="PG-PO-B", name="PG PO B")
    location = StockLocation(name="PG PO Main", type="main")
    pg_db.add_all([supplier, item_a, item_b, location])
    pg_db.flush()
    order = PurchaseOrder(supplier_id=supplier.id, status="ordered")
    pg_db.add(order)
    pg_db.flush()
    line_a = PurchaseOrderLine(purchase_order_id=order.id, inventory_item_id=item_a.id, quantity_ordered=Decimal("2"), unit_price=Decimal("10"))
    line_b = PurchaseOrderLine(purchase_order_id=order.id, inventory_item_id=item_b.id, quantity_ordered=Decimal("1"), unit_price=Decimal("10"))
    order.lines.extend([line_a, line_b])
    pg_db.add_all([line_a, line_b])
    pg_db.flush()

    with pytest.raises(HTTPException):
        receive_purchase_order(
            pg_db,
            order,
            PurchaseOrderReceiveRequest(lines=[
                {"purchase_order_line_id": line_a.id, "quantity_received": Decimal("1"), "location_id": location.id},
                {"purchase_order_line_id": line_b.id, "quantity_received": Decimal("2"), "location_id": location.id},
            ]),
            user_id=None,
        )

    assert line_a.quantity_received == 0
    assert pg_db.query(InventoryBatch).count() == 0
    assert pg_db.query(StockMovement).count() == 0


def test_pg_complete_with_consumption_rollback_through_endpoint(pg_client, pg_db):
    from tests.integration.test_quality_gate_api import create_user_with_permissions, login

    user = create_user_with_permissions(pg_db, "materials-pg@test.local", ["appointments.write", "inventory.write"])
    token = login(pg_client, user.email)
    svc = service(pg_db, name="PG Material Service")
    enough_item, enough_batch, _ = stock_item_with_batch(pg_db, sku="PG-MAT-ENOUGH", quantity=Decimal("5"))
    low_item, low_batch, _ = stock_item_with_batch(pg_db, sku="PG-MAT-LOW", quantity=Decimal("1"))
    appt = appointment(pg_db, service_obj=svc)
    pg_db.add_all([
        ServiceMaterialTemplate(service_id=svc.id, inventory_item_id=enough_item.id, default_quantity=Decimal("3"), required=True, variable_quantity_allowed=False),
        ServiceMaterialTemplate(service_id=svc.id, inventory_item_id=low_item.id, default_quantity=Decimal("3"), required=True, variable_quantity_allowed=False),
    ])
    pg_db.flush()

    response = pg_client.post(f"/api/appointments/{appt.id}/complete-with-consumption", headers={"Authorization": f"Bearer {token}"}, json={})

    assert response.status_code == 409
    assert enough_batch.quantity == Decimal("5")
    assert low_batch.quantity == Decimal("1")
    assert appt.status == "scheduled"
    assert pg_db.query(StockMovement).count() == 0
