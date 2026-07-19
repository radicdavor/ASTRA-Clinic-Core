"""Clinical form concurrency and completion idempotency.

Revision ID: 0053_form_reliability
Revises: 0052_gastro_hardening
"""
from alembic import op
import sqlalchemy as sa


revision = "0053_form_reliability"
down_revision = "0052_gastro_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("clinical_form_instances", sa.Column("completion_idempotency_key", sa.String(160), nullable=True))
    op.add_column("clinical_form_instances", sa.Column("completion_payload_hash", sa.String(64), nullable=True))
    op.create_check_constraint(
        "ck_clinical_form_completion_idempotency_pair",
        "clinical_form_instances",
        "(completion_idempotency_key IS NULL) = (completion_payload_hash IS NULL)",
    )


def downgrade():
    op.drop_constraint("ck_clinical_form_completion_idempotency_pair", "clinical_form_instances", type_="check")
    op.drop_column("clinical_form_instances", "completion_payload_hash")
    op.drop_column("clinical_form_instances", "completion_idempotency_key")
