"""provider contact and working hours

Revision ID: 0020_provider_contact_working_hours
Revises: 0019_clinical_open_questions
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_provider_contact_working_hours"
down_revision = "0019_clinical_open_questions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("providers", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("providers", sa.Column("work_start", sa.Time(), nullable=False, server_default="07:00:00"))
    op.add_column("providers", sa.Column("work_end", sa.Time(), nullable=False, server_default="15:00:00"))
    op.create_index(op.f("ix_providers_email"), "providers", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_providers_email"), table_name="providers")
    op.drop_column("providers", "work_end")
    op.drop_column("providers", "work_start")
    op.drop_column("providers", "email")
