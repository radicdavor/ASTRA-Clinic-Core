"""Complete laboratory v1 with cancellation metadata.

Revision ID: 0035_complete_laboratory_v1
Revises: 0034_simplify_laboratory_sample_status
"""
from alembic import op
import sqlalchemy as sa
revision="0035_complete_laboratory_v1";down_revision="0034_simplify_laboratory_sample_status";branch_labels=None;depends_on=None
def upgrade():
    op.add_column("lab_orders",sa.Column("cancelled_at",sa.DateTime(timezone=True)));op.add_column("lab_orders",sa.Column("cancelled_by",sa.Integer(),sa.ForeignKey("users.id")));op.add_column("lab_orders",sa.Column("cancellation_reason",sa.Text()))
def downgrade():
    op.drop_column("lab_orders","cancellation_reason");op.drop_column("lab_orders","cancelled_by");op.drop_column("lab_orders","cancelled_at")
