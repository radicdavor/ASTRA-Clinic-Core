"""Add visit-scoped reception note.

Revision ID: 0056_reception_note_patient_concurrency
Revises: 0055_check_in_red_flag_handoff
"""
from alembic import op
import sqlalchemy as sa


revision = "0056_reception_note_patient_concurrency"
down_revision = "0055_check_in_red_flag_handoff"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("journey_check_ins", sa.Column("reception_note", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("journey_check_ins", "reception_note")
