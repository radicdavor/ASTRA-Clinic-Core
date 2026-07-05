from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.domain import InventoryBatch, InventoryItem, StockLocation
from app.services.inventory import consume_fefo, recalculate_stock, transfer_batch


def test_fefo_consumes_earliest_expiration_first(db):
    item = InventoryItem(sku="FEFO", name="FEFO item", current_stock=Decimal("0"))
    location = StockLocation(name="Main", type="main")
    db.add_all([item, location])
    db.flush()
    later = InventoryBatch(inventory_item_id=item.id, expiration_date=date(2027, 1, 1), quantity=Decimal("5"), location_id=location.id)
    earlier = InventoryBatch(inventory_item_id=item.id, expiration_date=date(2026, 1, 1), quantity=Decimal("5"), location_id=location.id)
    db.add_all([later, earlier])
    db.flush()

    movements = consume_fefo(db, item.id, Decimal("6"))

    assert len(movements) == 2
    assert earlier.quantity == Decimal("0")
    assert later.quantity == Decimal("4")
    assert item.current_stock == Decimal("4")


def test_insufficient_stock_does_not_change_batches(db):
    item = InventoryItem(sku="LOW", name="Low item", current_stock=Decimal("0"))
    location = StockLocation(name="Main", type="main")
    db.add_all([item, location])
    db.flush()
    batch = InventoryBatch(inventory_item_id=item.id, quantity=Decimal("1"), location_id=location.id)
    db.add(batch)
    db.flush()

    with pytest.raises(HTTPException) as exc:
        consume_fefo(db, item.id, Decimal("2"))

    assert exc.value.status_code == 409
    assert batch.quantity == Decimal("1")


def test_transfer_preserves_total_stock(db):
    item = InventoryItem(sku="TR", name="Transfer item", current_stock=Decimal("0"))
    source = StockLocation(name="Main", type="main")
    target = StockLocation(name="Room", type="room")
    db.add_all([item, source, target])
    db.flush()
    batch = InventoryBatch(inventory_item_id=item.id, lot_number="A", quantity=Decimal("5"), location_id=source.id)
    db.add(batch)
    db.flush()

    movements = transfer_batch(db, batch, target.id, Decimal("2"), "test")
    recalculate_stock(db, item.id)

    assert len(movements) == 2
    assert item.current_stock == Decimal("5")
    assert sum(b.quantity for b in db.query(InventoryBatch).filter_by(inventory_item_id=item.id)) == Decimal("5")
