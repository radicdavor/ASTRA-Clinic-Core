# Procurement Workflow

Purchase orders support lines and receiving.

## Purchase Order Statuses

- `draft`
- `ordered`
- `partially_received`
- `received`
- `cancelled`

Status is derived from line quantities during receiving.

## Receiving

Receiving validates all requested lines before mutating stock.

For each valid received line the system creates:

- `InventoryBatch`
- `StockMovement` with `movement_type=purchase_receipt`

The related purchase order line increases `quantity_received`, and inventory stock is recalculated.

## Rejection Rules

- received quantity must be positive
- line must belong to the order
- cumulative received quantity cannot exceed ordered quantity
- LOT and expiration date are required when item tracking flags require them

Failed receiving must leave no partial batches or stock movements.
