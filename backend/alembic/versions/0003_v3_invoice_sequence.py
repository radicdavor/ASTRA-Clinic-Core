"""v3 invoice sequence

Revision ID: 0003_v3_invoice_sequence
Revises: 0002_hardening_v2
Create Date: 2026-07-05
"""

from alembic import op


revision = "0003_v3_invoice_sequence"
down_revision = "0002_hardening_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS invoice_number_sequences (
            id SERIAL PRIMARY KEY,
            business_unit VARCHAR(120) NOT NULL UNIQUE DEFAULT 'default',
            next_number INTEGER NOT NULL DEFAULT 1,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
        """
    )
    op.execute(
        """
        INSERT INTO invoice_number_sequences (business_unit, next_number)
        VALUES ('default', COALESCE((SELECT MAX(id) + 1 FROM invoices), 1))
        ON CONFLICT (business_unit) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS invoice_number_sequences")
