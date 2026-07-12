"""Simplify laboratory sample workflow to collection only.

Revision ID: 0034_simplify_laboratory_sample_status
Revises: 0033_laboratory_sample_dispatch
"""
from alembic import op
import sqlalchemy as sa
revision="0034_simplify_laboratory_sample_status";down_revision="0033_laboratory_sample_dispatch";branch_labels=None;depends_on=None

def upgrade():
    op.execute(sa.text("UPDATE lab_orders SET status='collected' WHERE status IN ('dispatched','external_received') AND collected_at IS NOT NULL"))

def downgrade():
    pass
