"""provider availability

Revision ID: 0026_provider_availability
Revises: 0025_provider_weekly_working_hours
"""
from alembic import op
import sqlalchemy as sa
revision = "0026_provider_availability"
down_revision = "0025_provider_weekly_working_hours"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("providers", sa.Column("available_for_work", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_providers_available_for_work", "providers", ["available_for_work"])
def downgrade() -> None:
    op.drop_index("ix_providers_available_for_work", table_name="providers")
    op.drop_column("providers", "available_for_work")
