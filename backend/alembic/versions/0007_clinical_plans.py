"""clinical plans

Revision ID: 0007_clinical_plans
Revises: 0006_clinical_episodes
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_clinical_plans"
down_revision = "0006_clinical_episodes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("episode_id", sa.Integer(), sa.ForeignKey("clinical_episodes.id"), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("proposed_episode_status", sa.String(length=40), nullable=True),
        sa.Column("next_action", sa.String(length=80), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("priority", sa.String(length=40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("suggested_follow_up", sa.Text(), nullable=True),
        sa.Column("ai_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("physician_confirmed", sa.Boolean(), nullable=False),
        sa.Column("confirmed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_clinical_plans_episode_id", "clinical_plans", ["episode_id"])
    op.create_index("ix_clinical_plans_source", "clinical_plans", ["source"])
    op.create_index("ix_clinical_plans_status", "clinical_plans", ["status"])
    op.create_index("ix_clinical_plans_next_action", "clinical_plans", ["next_action"])
    op.create_index("ix_clinical_plans_priority", "clinical_plans", ["priority"])
    op.create_index("ix_clinical_plans_physician_confirmed", "clinical_plans", ["physician_confirmed"])


def downgrade() -> None:
    op.drop_index("ix_clinical_plans_physician_confirmed", table_name="clinical_plans")
    op.drop_index("ix_clinical_plans_priority", table_name="clinical_plans")
    op.drop_index("ix_clinical_plans_next_action", table_name="clinical_plans")
    op.drop_index("ix_clinical_plans_status", table_name="clinical_plans")
    op.drop_index("ix_clinical_plans_source", table_name="clinical_plans")
    op.drop_index("ix_clinical_plans_episode_id", table_name="clinical_plans")
    op.drop_table("clinical_plans")
