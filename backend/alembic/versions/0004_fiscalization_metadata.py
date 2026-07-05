"""fiscalization metadata

Revision ID: 0004_fiscalization_metadata
Revises: 0003_v3_invoice_sequence
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_fiscalization_metadata"
down_revision = "0003_v3_invoice_sequence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("fiscalization_provider", sa.String(length=80), nullable=True))
    op.add_column("invoices", sa.Column("fiscalization_message", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("fiscalized_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("invoices", "fiscalized_at")
    op.drop_column("invoices", "fiscalization_message")
    op.drop_column("invoices", "fiscalization_provider")
