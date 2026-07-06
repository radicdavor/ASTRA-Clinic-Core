"""clinical documents

Revision ID: 0009_clinical_documents
Revises: 0008_clinical_plan_guardrails
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_clinical_documents"
down_revision = "0008_clinical_plan_guardrails"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("document_type", sa.String(length=60), nullable=False),
        sa.Column("origin", sa.String(length=180), nullable=True),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("author", sa.String(length=160), nullable=True),
        sa.Column("institution", sa.String(length=180), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("key_findings", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("physician_reviewed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attachment_path", sa.Text(), nullable=True),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_documents_document_date"), "clinical_documents", ["document_date"])
    op.create_index(op.f("ix_clinical_documents_document_type"), "clinical_documents", ["document_type"])
    op.create_index(op.f("ix_clinical_documents_patient_id"), "clinical_documents", ["patient_id"])
    op.create_index(op.f("ix_clinical_documents_physician_reviewed"), "clinical_documents", ["physician_reviewed"])
    op.create_index(op.f("ix_clinical_documents_source_type"), "clinical_documents", ["source_type"])
    op.create_index(op.f("ix_clinical_documents_title"), "clinical_documents", ["title"])


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_documents_title"), table_name="clinical_documents")
    op.drop_index(op.f("ix_clinical_documents_source_type"), table_name="clinical_documents")
    op.drop_index(op.f("ix_clinical_documents_physician_reviewed"), table_name="clinical_documents")
    op.drop_index(op.f("ix_clinical_documents_patient_id"), table_name="clinical_documents")
    op.drop_index(op.f("ix_clinical_documents_document_type"), table_name="clinical_documents")
    op.drop_index(op.f("ix_clinical_documents_document_date"), table_name="clinical_documents")
    op.drop_table("clinical_documents")
