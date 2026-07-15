"""Add patient-provided findings and physician opinion to encounters.

Revision ID: 0046_encounter_findings_opinion
Revises: 0045_program2_closure
"""

from alembic import op
import sqlalchemy as sa


revision = "0046_encounter_findings_opinion"
down_revision = "0045_program2_closure"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("journey_encounters", sa.Column("patient_findings", sa.Text(), nullable=True))
    op.add_column("journey_encounters", sa.Column("opinion", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("journey_encounters", "opinion")
    op.drop_column("journey_encounters", "patient_findings")
