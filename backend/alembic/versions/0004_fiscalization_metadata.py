"""fiscalization metadata

Revision ID: 0004_fiscalization_metadata
Revises: 0003_v3_invoice_sequence
Create Date: 2026-07-05
"""

from alembic import op


revision = "0004_fiscalization_metadata"
down_revision = "0003_v3_invoice_sequence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS fiscalization_provider VARCHAR(80)")
    op.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS fiscalization_message TEXT")
    op.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS fiscalized_at TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS fiscalized_at")
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS fiscalization_message")
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS fiscalization_provider")
