"""bounded security audit aggregation

Revision ID: 0067_audit_aggregation
Revises: 0066_api_key_tenant_scope
"""

from alembic import op
import sqlalchemy as sa


revision = "0067_audit_aggregation"
down_revision = "0066_api_key_tenant_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("audit_logs", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("audit_logs", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("audit_logs", sa.Column("aggregation_key", sa.String(length=64), nullable=True))
    op.create_index("ix_audit_logs_last_seen_at", "audit_logs", ["last_seen_at"])
    op.create_unique_constraint("uq_audit_logs_aggregation_key", "audit_logs", ["aggregation_key"])


def downgrade() -> None:
    op.drop_constraint("uq_audit_logs_aggregation_key", "audit_logs", type_="unique")
    op.drop_index("ix_audit_logs_last_seen_at", table_name="audit_logs")
    op.drop_column("audit_logs", "aggregation_key")
    op.drop_column("audit_logs", "last_seen_at")
    op.drop_column("audit_logs", "first_seen_at")
    op.drop_column("audit_logs", "occurrence_count")
