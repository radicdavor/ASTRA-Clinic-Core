"""Check-in red flag handoff metadata.

Revision ID: 0055_check_in_red_flag_handoff
Revises: 0054_activity_report_policies
"""
from alembic import op
import sqlalchemy as sa


revision = "0055_check_in_red_flag_handoff"
down_revision = "0054_activity_report_policies"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("journey_check_in_items", sa.Column("details_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("journey_check_in_items", sa.Column("activity_ids_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.add_column("journey_check_in_items", sa.Column("medical_disposition", sa.String(60), nullable=True))
    op.add_column("journey_check_in_items", sa.Column("medical_disposition_note", sa.Text(), nullable=True))
    op.add_column("journey_check_in_items", sa.Column("medical_reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("journey_check_in_items", sa.Column("medical_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_journey_check_in_items_medical_disposition", "journey_check_in_items", ["medical_disposition"])


def downgrade():
    op.drop_index("ix_journey_check_in_items_medical_disposition", table_name="journey_check_in_items")
    op.drop_column("journey_check_in_items", "medical_reviewed_at")
    op.drop_column("journey_check_in_items", "medical_reviewed_by")
    op.drop_column("journey_check_in_items", "medical_disposition_note")
    op.drop_column("journey_check_in_items", "medical_disposition")
    op.drop_column("journey_check_in_items", "activity_ids_json")
    op.drop_column("journey_check_in_items", "details_json")
