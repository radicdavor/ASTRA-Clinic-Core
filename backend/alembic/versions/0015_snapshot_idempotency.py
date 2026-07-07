"""snapshot idempotency

Revision ID: 0015_snapshot_idempotency
Revises: 0014_clinical_readiness_snapshots
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_snapshot_idempotency"
down_revision = "0014_clinical_readiness_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clinical_readiness_snapshots", sa.Column("idempotency_key", sa.String(length=160), nullable=True))
    op.add_column("clinical_readiness_snapshots", sa.Column("idempotency_fingerprint", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_clinical_readiness_snapshots_idempotency_key"), "clinical_readiness_snapshots", ["idempotency_key"])
    op.create_unique_constraint(
        "uq_clinical_readiness_snapshot_idempotency_key",
        "clinical_readiness_snapshots",
        ["appointment_id", "created_by_user_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_clinical_readiness_snapshot_idempotency_key", "clinical_readiness_snapshots", type_="unique")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_idempotency_key"), table_name="clinical_readiness_snapshots")
    op.drop_column("clinical_readiness_snapshots", "idempotency_fingerprint")
    op.drop_column("clinical_readiness_snapshots", "idempotency_key")
