"""Add laboratory orders and results.

Revision ID: 0028_laboratory_orders_results
Revises: 0027_cleanup_demo_service_clinic_links
"""
from alembic import op
import sqlalchemy as sa

revision = "0028_laboratory_orders_results"
down_revision = "0027_cleanup_demo_service_clinic_links"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("lab_orders", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False), sa.Column("episode_id", sa.Integer(), sa.ForeignKey("clinical_episodes.id")), sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id")), sa.Column("external_laboratory", sa.String(180)), sa.Column("status", sa.String(40), nullable=False, server_default="ordered"), sa.Column("ordered_at", sa.Date(), nullable=False), sa.Column("collected_at", sa.DateTime(timezone=True)), sa.Column("notes", sa.Text()), sa.Column("review_conclusion", sa.Text()), sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("reviewed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_lab_orders_patient_id", "lab_orders", ["patient_id"]); op.create_index("ix_lab_orders_status", "lab_orders", ["status"]); op.create_index("ix_lab_orders_ordered_at", "lab_orders", ["ordered_at"])
    op.create_table("lab_results", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("order_id", sa.Integer(), sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False), sa.Column("test_name", sa.String(180), nullable=False), sa.Column("value", sa.Numeric(14,4)), sa.Column("text_value", sa.String(240)), sa.Column("unit", sa.String(60)), sa.Column("reference_low", sa.Numeric(14,4)), sa.Column("reference_high", sa.Numeric(14,4)), sa.Column("flag", sa.String(30), nullable=False, server_default="pending"), sa.Column("resulted_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_lab_results_order_id", "lab_results", ["order_id"]); op.create_index("ix_lab_results_test_name", "lab_results", ["test_name"]); op.create_index("ix_lab_results_flag", "lab_results", ["flag"])

def downgrade() -> None:
    op.drop_table("lab_results"); op.drop_table("lab_orders")
