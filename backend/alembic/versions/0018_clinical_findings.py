"""clinical findings persistence foundation

Revision ID: 0018_clinical_findings
Revises: 0017_acknowledgment_persistence_foundation
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_clinical_findings"
down_revision = "0017_acknowledgment_persistence_foundation"
branch_labels = None
depends_on = None


SAFE_LIFECYCLE_STATUS_CHECK = (
    "lifecycle_status in ('received', 'linked_to_patient', 'awaiting_review', "
    "'review_in_progress', 'reviewed', 'needs_clinician_decision', "
    "'decision_documented', 'follow_up_recommended', "
    "'external_referral_recommended', 'closed_for_now')"
)


def upgrade() -> None:
    op.create_table(
        "clinical_findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_label", sa.String(length=220), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=False),
        sa.Column("finding_key", sa.String(length=160), nullable=False),
        sa.Column("label", sa.String(length=240), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=80), nullable=False),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("limitations_json", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(trim(source_type)) > 0", name="ck_clinical_findings_source_type_non_empty"),
        sa.CheckConstraint("length(trim(source_label)) > 0", name="ck_clinical_findings_source_label_non_empty"),
        sa.CheckConstraint("length(trim(source_reference)) > 0", name="ck_clinical_findings_source_reference_non_empty"),
        sa.CheckConstraint("length(trim(finding_key)) > 0", name="ck_clinical_findings_key_non_empty"),
        sa.CheckConstraint("length(trim(label)) > 0", name="ck_clinical_findings_label_non_empty"),
        sa.CheckConstraint("length(trim(schema_version)) > 0", name="ck_clinical_findings_schema_version_non_empty"),
        sa.CheckConstraint(SAFE_LIFECYCLE_STATUS_CHECK, name="ck_clinical_findings_lifecycle_status_safe"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["source_document_id"], ["clinical_documents.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_findings_patient_id"), "clinical_findings", ["patient_id"], unique=False)
    op.create_index(op.f("ix_clinical_findings_lifecycle_status"), "clinical_findings", ["lifecycle_status"], unique=False)
    op.create_index(op.f("ix_clinical_findings_finding_key"), "clinical_findings", ["finding_key"], unique=False)
    op.create_index(op.f("ix_clinical_findings_category"), "clinical_findings", ["category"], unique=False)
    op.create_index(op.f("ix_clinical_findings_source_type"), "clinical_findings", ["source_type"], unique=False)
    op.create_index(op.f("ix_clinical_findings_source_document_id"), "clinical_findings", ["source_document_id"], unique=False)
    op.create_index(op.f("ix_clinical_findings_created_at"), "clinical_findings", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_findings_created_at"), table_name="clinical_findings")
    op.drop_index(op.f("ix_clinical_findings_source_document_id"), table_name="clinical_findings")
    op.drop_index(op.f("ix_clinical_findings_source_type"), table_name="clinical_findings")
    op.drop_index(op.f("ix_clinical_findings_category"), table_name="clinical_findings")
    op.drop_index(op.f("ix_clinical_findings_finding_key"), table_name="clinical_findings")
    op.drop_index(op.f("ix_clinical_findings_lifecycle_status"), table_name="clinical_findings")
    op.drop_index(op.f("ix_clinical_findings_patient_id"), table_name="clinical_findings")
    op.drop_table("clinical_findings")

