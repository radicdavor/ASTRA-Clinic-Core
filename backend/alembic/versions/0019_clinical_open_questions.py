"""clinical open questions persistence foundation

Revision ID: 0019_clinical_open_questions
Revises: 0018_clinical_findings
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_clinical_open_questions"
down_revision = "0018_clinical_findings"
branch_labels = None
depends_on = None


SAFE_OPEN_QUESTION_STATUS_CHECK = (
    "status in ('draft', 'suggested', 'awaiting_review', 'under_review', "
    "'needs_clinician_decision', 'decision_documented', 'deferred', "
    "'closed_for_now')"
)


def upgrade() -> None:
    op.create_table(
        "clinical_open_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("finding_id", sa.Integer(), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_label", sa.String(length=220), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=False),
        sa.Column("question_key", sa.String(length=160), nullable=False),
        sa.Column("label", sa.String(length=240), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("requires_clinician_review", sa.Boolean(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("limitations_json", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(trim(source_type)) > 0", name="ck_clinical_open_questions_source_type_non_empty"),
        sa.CheckConstraint("length(trim(source_label)) > 0", name="ck_clinical_open_questions_source_label_non_empty"),
        sa.CheckConstraint("length(trim(source_reference)) > 0", name="ck_clinical_open_questions_source_reference_non_empty"),
        sa.CheckConstraint("length(trim(question_key)) > 0", name="ck_clinical_open_questions_key_non_empty"),
        sa.CheckConstraint("length(trim(label)) > 0", name="ck_clinical_open_questions_label_non_empty"),
        sa.CheckConstraint("length(trim(schema_version)) > 0", name="ck_clinical_open_questions_schema_version_non_empty"),
        sa.CheckConstraint(SAFE_OPEN_QUESTION_STATUS_CHECK, name="ck_clinical_open_questions_status_safe"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["finding_id"], ["clinical_findings.id"]),
        sa.ForeignKeyConstraint(["source_document_id"], ["clinical_documents.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_open_questions_patient_id"), "clinical_open_questions", ["patient_id"], unique=False)
    op.create_index(op.f("ix_clinical_open_questions_finding_id"), "clinical_open_questions", ["finding_id"], unique=False)
    op.create_index(op.f("ix_clinical_open_questions_source_document_id"), "clinical_open_questions", ["source_document_id"], unique=False)
    op.create_index(op.f("ix_clinical_open_questions_status"), "clinical_open_questions", ["status"], unique=False)
    op.create_index(op.f("ix_clinical_open_questions_question_key"), "clinical_open_questions", ["question_key"], unique=False)
    op.create_index(op.f("ix_clinical_open_questions_source_type"), "clinical_open_questions", ["source_type"], unique=False)
    op.create_index(op.f("ix_clinical_open_questions_created_at"), "clinical_open_questions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_open_questions_created_at"), table_name="clinical_open_questions")
    op.drop_index(op.f("ix_clinical_open_questions_source_type"), table_name="clinical_open_questions")
    op.drop_index(op.f("ix_clinical_open_questions_question_key"), table_name="clinical_open_questions")
    op.drop_index(op.f("ix_clinical_open_questions_status"), table_name="clinical_open_questions")
    op.drop_index(op.f("ix_clinical_open_questions_source_document_id"), table_name="clinical_open_questions")
    op.drop_index(op.f("ix_clinical_open_questions_finding_id"), table_name="clinical_open_questions")
    op.drop_index(op.f("ix_clinical_open_questions_patient_id"), table_name="clinical_open_questions")
    op.drop_table("clinical_open_questions")
