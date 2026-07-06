"""patient clinical summaries

Revision ID: 0010_patient_clinical_summaries
Revises: 0009_clinical_documents
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_patient_clinical_summaries"
down_revision = "0009_clinical_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_clinical_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("known_conditions", sa.JSON(), nullable=True),
        sa.Column("key_findings", sa.JSON(), nullable=True),
        sa.Column("open_items", sa.JSON(), nullable=True),
        sa.Column("risks", sa.JSON(), nullable=True),
        sa.Column("last_recommendations", sa.JSON(), nullable=True),
        sa.Column("source_document_ids", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="needs_review"),
        sa.Column("generated_by", sa.String(length=80), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patient_clinical_summaries_patient_id"), "patient_clinical_summaries", ["patient_id"])
    op.create_index(op.f("ix_patient_clinical_summaries_status"), "patient_clinical_summaries", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_patient_clinical_summaries_status"), table_name="patient_clinical_summaries")
    op.drop_index(op.f("ix_patient_clinical_summaries_patient_id"), table_name="patient_clinical_summaries")
    op.drop_table("patient_clinical_summaries")
