"""Program 2 reception check-in.

Revision ID: 0043_program2_checkin
Revises: 0042_program2_summary
"""
from alembic import op
import sqlalchemy as sa

revision = "0043_program2_checkin"
down_revision = "0042_program2_summary"
branch_labels = None
depends_on = None

def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())]

def upgrade():
    op.create_table("journey_check_ins", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("journey_id", sa.Integer(), sa.ForeignKey("patient_journeys.id", ondelete="CASCADE"), nullable=False, unique=True), sa.Column("status", sa.String(40), nullable=False, server_default="in_review"), sa.Column("arrived_at", sa.DateTime(timezone=True)), sa.Column("started_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("completed_by", sa.Integer(), sa.ForeignKey("users.id")), *timestamps())
    op.create_index("ix_journey_check_ins_journey_id", "journey_check_ins", ["journey_id"])
    op.create_index("ix_journey_check_ins_status", "journey_check_ins", ["status"])
    op.create_table("journey_check_in_items", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("check_in_id", sa.Integer(), sa.ForeignKey("journey_check_ins.id", ondelete="CASCADE"), nullable=False), sa.Column("item_key", sa.String(100), nullable=False), sa.Column("category", sa.String(60), nullable=False), sa.Column("label", sa.String(220), nullable=False), sa.Column("state", sa.String(50), nullable=False, server_default="not_confirmed"), sa.Column("requires_clinician", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("note", sa.Text()), sa.Column("position", sa.Integer(), nullable=False, server_default="0"), sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id")), *timestamps(), sa.UniqueConstraint("check_in_id", "item_key", name="uq_check_in_item_key"))
    for column in ("check_in_id", "item_key", "category", "state", "requires_clinician"):
        op.create_index(f"ix_journey_check_in_items_{column}", "journey_check_in_items", [column])

def downgrade():
    op.drop_table("journey_check_in_items")
    op.drop_table("journey_check_ins")
