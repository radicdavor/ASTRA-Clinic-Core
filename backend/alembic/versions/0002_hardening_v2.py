"""hardening v2 inventory procurement billing

Revision ID: 0002_hardening_v2
Revises: 0001_initial
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_hardening_v2"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text()),
    )
    op.create_index("ix_permissions_name", "permissions", ["name"], unique=True)
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), primary_key=True),
    )
    op.add_column("api_keys", sa.Column("scopes", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("api_keys", sa.Column("expires_at", sa.DateTime(timezone=True)))
    op.add_column("api_keys", sa.Column("last_used_at", sa.DateTime(timezone=True)))
    op.add_column("audit_logs", sa.Column("actor_type", sa.String(40), nullable=False, server_default="system"))
    op.add_column("audit_logs", sa.Column("actor_api_key_id", sa.Integer()))
    op.add_column("audit_logs", sa.Column("before_json", sa.JSON()))
    op.add_column("audit_logs", sa.Column("after_json", sa.JSON()))
    op.add_column("audit_logs", sa.Column("request_id", sa.String(80)))
    op.add_column("audit_logs", sa.Column("ip_address", sa.String(80)))
    op.add_column("audit_logs", sa.Column("user_agent", sa.Text()))
    op.create_foreign_key("fk_audit_logs_actor_api_key_id", "audit_logs", "api_keys", ["actor_api_key_id"], ["id"])
    op.create_index("ix_audit_logs_actor_type", "audit_logs", ["actor_type"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
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
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_type", table_name="audit_logs")
    op.drop_constraint("fk_audit_logs_actor_api_key_id", "audit_logs", type_="foreignkey")
    op.drop_column("audit_logs", "user_agent")
    op.drop_column("audit_logs", "ip_address")
    op.drop_column("audit_logs", "request_id")
    op.drop_column("audit_logs", "after_json")
    op.drop_column("audit_logs", "before_json")
    op.drop_column("audit_logs", "actor_api_key_id")
    op.drop_column("audit_logs", "actor_type")
    op.drop_column("api_keys", "last_used_at")
    op.drop_column("api_keys", "expires_at")
    op.drop_column("api_keys", "scopes")
    op.drop_table("role_permissions")
    op.drop_index("ix_permissions_name", table_name="permissions")
    op.drop_table("permissions")
