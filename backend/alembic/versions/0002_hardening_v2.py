"""hardening v2 inventory procurement billing

Revision ID: 0002_hardening_v2
Revises: 0001_initial
Create Date: 2026-07-05
"""

from alembic import op


revision = "0002_hardening_v2"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS operator VARCHAR(120)")
    op.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS business_unit VARCHAR(120)")
    op.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS register_id VARCHAR(80)")
    op.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS vat_id VARCHAR(80)")
    op.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS fiscalization_status VARCHAR(60) DEFAULT 'not_applicable'")
    op.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS fiscalization_reference VARCHAR(160)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id SERIAL PRIMARY KEY,
            invoice_id INTEGER NOT NULL REFERENCES invoices(id),
            amount NUMERIC(12, 2) NOT NULL,
            method VARCHAR(80) NOT NULL,
            reference VARCHAR(160),
            paid_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            created_by INTEGER REFERENCES users(id),
            CONSTRAINT ck_payment_transactions_amount_positive CHECK (amount > 0)
        )
        """
    )
    constraints = [
        ("inventory_items", "ck_inventory_items_current_stock_non_negative", "current_stock >= 0"),
        ("inventory_items", "ck_inventory_items_minimum_stock_non_negative", "minimum_stock >= 0"),
        ("inventory_items", "ck_inventory_items_reorder_point_non_negative", "reorder_point >= 0"),
        ("inventory_batches", "ck_inventory_batches_quantity_non_negative", "quantity >= 0"),
        ("stock_movements", "ck_stock_movements_quantity_positive", "quantity > 0"),
        ("purchase_order_lines", "ck_purchase_order_lines_quantity_ordered_positive", "quantity_ordered > 0"),
        ("purchase_order_lines", "ck_purchase_order_lines_quantity_received_non_negative", "quantity_received >= 0"),
        ("invoice_lines", "ck_invoice_lines_quantity_positive", "quantity > 0"),
        ("invoice_lines", "ck_invoice_lines_total_non_negative", "total >= 0"),
    ]
    for table, name, expression in constraints:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = '{name}' AND conrelid = '{table}'::regclass
                ) THEN
                    ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({expression});
                END IF;
            END
            $$;
            """
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS payment_transactions")
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS fiscalization_reference")
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS fiscalization_status")
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS vat_id")
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS register_id")
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS business_unit")
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS operator")
