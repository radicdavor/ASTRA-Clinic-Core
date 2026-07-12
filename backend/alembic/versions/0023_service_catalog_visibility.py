"""service catalog visibility

Revision ID: 0023_service_catalog_visibility
Revises: 0022_knowledge_engine
"""
from alembic import op
import sqlalchemy as sa
revision = "0023_service_catalog_visibility"
down_revision = "0022_knowledge_engine"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("services", sa.Column("visible_in_catalog", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_services_visible_in_catalog", "services", ["visible_in_catalog"])
def downgrade() -> None:
    op.drop_index("ix_services_visible_in_catalog", table_name="services")
    op.drop_column("services", "visible_in_catalog")
