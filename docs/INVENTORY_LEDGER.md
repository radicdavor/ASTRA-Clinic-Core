# Inventory Ledger

Inventory batches are the source of truth.

`InventoryItem.current_stock` is a derived cache and should equal the sum of all related `InventoryBatch.quantity` values.

## Rules

- batch quantity cannot be negative
- stock movement quantity must be positive
- FEFO consumption uses the earliest expiration date first
- write-off and adjustment require a reason
- transfer creates one outgoing and one incoming stock movement
- transfer preserves total stock
- `POST /api/inventory/recalculate-stock` repairs the item stock cache

## Tracking

If an item has `lot_tracking_enabled`, receiving requires a LOT number.

If an item has `expiration_tracking_enabled`, receiving requires an expiration date.

## Transaction Boundary

Inventory-changing workflows must not commit inside service functions. Endpoints own commit/rollback boundaries.
