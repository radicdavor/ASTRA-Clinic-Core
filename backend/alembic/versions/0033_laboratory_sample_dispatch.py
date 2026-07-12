"""Add laboratory sample collection and dispatch tracking.

Revision ID: 0033_laboratory_sample_dispatch
Revises: 0032_categorize_laboratory_templates
"""
from alembic import op
import sqlalchemy as sa
revision="0033_laboratory_sample_dispatch";down_revision="0032_categorize_laboratory_templates";branch_labels=None;depends_on=None

def upgrade():
    op.add_column("lab_orders",sa.Column("specimen_type",sa.String(40),nullable=False,server_default="blood"));op.create_index("ix_lab_orders_specimen_type","lab_orders",["specimen_type"])
    op.add_column("lab_orders",sa.Column("collected_by",sa.Integer(),sa.ForeignKey("users.id")))
    op.add_column("lab_orders",sa.Column("dispatched_at",sa.DateTime(timezone=True)));op.create_index("ix_lab_orders_dispatched_at","lab_orders",["dispatched_at"])
    op.add_column("lab_orders",sa.Column("dispatched_by",sa.Integer(),sa.ForeignKey("users.id")))
    op.add_column("lab_orders",sa.Column("external_received_at",sa.DateTime(timezone=True)))

def downgrade():
    op.drop_column("lab_orders","external_received_at");op.drop_column("lab_orders","dispatched_by");op.drop_index("ix_lab_orders_dispatched_at",table_name="lab_orders");op.drop_column("lab_orders","dispatched_at");op.drop_column("lab_orders","collected_by");op.drop_index("ix_lab_orders_specimen_type",table_name="lab_orders");op.drop_column("lab_orders","specimen_type")
