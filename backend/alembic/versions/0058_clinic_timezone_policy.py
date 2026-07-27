"""Clinic timezone policy.

Revision ID: 0058_clinic_timezone_policy
Revises: 0057_clinic_scope_foundation
"""

from alembic import op
import sqlalchemy as sa


revision = "0058_clinic_timezone_policy"
down_revision = "0057_clinic_scope_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "clinics",
        sa.Column("timezone", sa.String(length=80), nullable=False, server_default="Europe/Zagreb"),
    )
    op.alter_column("clinics", "timezone", server_default=None)


def downgrade():
    op.drop_column("clinics", "timezone")
