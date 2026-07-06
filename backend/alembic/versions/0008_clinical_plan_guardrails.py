"""clinical plan guardrails

Revision ID: 0008_clinical_plan_guardrails
Revises: 0007_clinical_plans
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_clinical_plan_guardrails"
down_revision = "0007_clinical_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clinical_plans", sa.Column("physician_conclusion", sa.Text(), nullable=True))
    op.create_index(
        "uq_clinical_plans_one_active_per_episode",
        "clinical_plans",
        ["episode_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND physician_confirmed IS TRUE"),
    )


def downgrade() -> None:
    op.drop_index("uq_clinical_plans_one_active_per_episode", table_name="clinical_plans")
    op.drop_column("clinical_plans", "physician_conclusion")
