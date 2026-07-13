"""Program 2 consumable provenance for journey closure.

Revision ID: 0045_program2_closure
Revises: 0044_program2_encounter
"""
from alembic import op
import sqlalchemy as sa

revision = "0045_program2_closure"
down_revision = "0044_program2_encounter"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("stock_movements", sa.Column("related_journey_id", sa.Integer(), nullable=True))
    op.add_column("stock_movements", sa.Column("serial_number", sa.String(120), nullable=True))
    op.add_column("stock_movements", sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True))
    op.create_foreign_key("fk_stock_movements_journey", "stock_movements", "patient_journeys", ["related_journey_id"], ["id"])
    op.create_index("ix_stock_movements_related_journey_id", "stock_movements", ["related_journey_id"])

def downgrade():
    op.drop_index("ix_stock_movements_related_journey_id", table_name="stock_movements")
    op.drop_constraint("fk_stock_movements_journey", "stock_movements", type_="foreignkey")
    op.drop_column("stock_movements", "unit_cost")
    op.drop_column("stock_movements", "serial_number")
    op.drop_column("stock_movements", "related_journey_id")
