"""clinical episodes

Revision ID: 0006_clinical_episodes
Revises: 0005_patient_oib
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_clinical_episodes"
down_revision = "0005_patient_oib"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_episodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("episode_type", sa.String(length=80), nullable=False, server_default="general"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(length=40), nullable=False, server_default="routine"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("clinical_notes", sa.Text(), nullable=True),
        sa.Column("owner_provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_clinical_episodes_patient_id", "clinical_episodes", ["patient_id"])
    op.create_index("ix_clinical_episodes_title", "clinical_episodes", ["title"])
    op.create_index("ix_clinical_episodes_episode_type", "clinical_episodes", ["episode_type"])
    op.create_index("ix_clinical_episodes_status", "clinical_episodes", ["status"])
    op.create_index("ix_clinical_episodes_priority", "clinical_episodes", ["priority"])
    op.create_index("ix_clinical_episodes_start_date", "clinical_episodes", ["start_date"])
    op.execute("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS episode_id INTEGER REFERENCES clinical_episodes(id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_appointments_episode_id ON appointments (episode_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_appointments_episode_id")
    op.execute("ALTER TABLE appointments DROP COLUMN IF EXISTS episode_id")
    op.drop_index("ix_clinical_episodes_start_date", table_name="clinical_episodes")
    op.drop_index("ix_clinical_episodes_priority", table_name="clinical_episodes")
    op.drop_index("ix_clinical_episodes_status", table_name="clinical_episodes")
    op.drop_index("ix_clinical_episodes_episode_type", table_name="clinical_episodes")
    op.drop_index("ix_clinical_episodes_title", table_name="clinical_episodes")
    op.drop_index("ix_clinical_episodes_patient_id", table_name="clinical_episodes")
    op.drop_table("clinical_episodes")
