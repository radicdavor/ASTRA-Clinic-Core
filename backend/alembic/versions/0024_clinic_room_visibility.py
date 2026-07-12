"""clinic and room visibility

Revision ID: 0024_clinic_room_visibility
Revises: 0023_service_catalog_visibility
"""
from alembic import op
import sqlalchemy as sa
revision = "0024_clinic_room_visibility"
down_revision = "0023_service_catalog_visibility"
branch_labels = None
depends_on = None
def upgrade() -> None:
    for table in ("clinics", "rooms"):
        op.add_column(table, sa.Column("visible_in_catalog", sa.Boolean(), nullable=False, server_default=sa.true()))
        op.create_index(f"ix_{table}_visible_in_catalog", table, ["visible_in_catalog"])
def downgrade() -> None:
    for table in ("rooms", "clinics"):
        op.drop_index(f"ix_{table}_visible_in_catalog", table_name=table)
        op.drop_column(table, "visible_in_catalog")
