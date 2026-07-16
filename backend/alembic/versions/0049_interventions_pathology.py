"""Procedure interventions, specimens and pathology lifecycle.

Revision ID: 0049_pathology
Revises: 0048_clinical_forms
"""
from alembic import op
import sqlalchemy as sa


revision = "0049_pathology"
down_revision = "0048_clinical_forms"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "procedure_interventions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("journey_activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intervention_type", sa.String(60), nullable=False),
        sa.Column("anatomical_site", sa.String(220)),
        sa.Column("description", sa.Text()),
        sa.Column("technique", sa.String(220)),
        sa.Column("device", sa.String(220)),
        sa.Column("size", sa.String(80)),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("retrieval_status", sa.String(60)),
        sa.Column("complication", sa.Text()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("intervention_type in ('biopsy','polypectomy','injection','clip_placement','dilation','hemostasis','foreign_body_removal','other')", name="ck_procedure_intervention_type"),
        sa.CheckConstraint("count > 0", name="ck_procedure_intervention_count"),
    )
    op.create_index("ix_procedure_interventions_activity_id", "procedure_interventions", ["activity_id"])

    op.create_table(
        "pathology_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("journey_id", sa.Integer(), sa.ForeignKey("patient_journeys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_activity_id", sa.Integer(), sa.ForeignKey("journey_activities.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False, unique=True),
        sa.Column("status", sa.String(60), nullable=False, server_default="draft"),
        sa.Column("external_lab", sa.String(220)),
        sa.Column("external_case_number", sa.String(160)),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("collected_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("lab_received_at", sa.DateTime(timezone=True)),
        sa.Column("result_received_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("patient_notified_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("patient_id", "journey_id", "source_activity_id", "status"):
        op.create_index(f"ix_pathology_cases_{column}", "pathology_cases", [column])

    op.create_table(
        "pathology_specimens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("pathology_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("specimen_label", sa.String(160), nullable=False),
        sa.Column("anatomical_site", sa.String(220), nullable=False),
        sa.Column("specimen_type", sa.String(100), nullable=False),
        sa.Column("source_intervention_id", sa.Integer(), sa.ForeignKey("procedure_interventions.id", ondelete="SET NULL")),
        sa.Column("container", sa.String(120)),
        sa.Column("fixation", sa.String(120)),
        sa.Column("collection_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("case_id", "specimen_label", name="uq_pathology_specimen_label"),
    )
    op.create_index("ix_pathology_specimens_case_id", "pathology_specimens", ["case_id"])

    op.create_table(
        "pathology_report_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("pathology_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clinical_document_id", sa.Integer(), sa.ForeignKey("clinical_documents.id"), nullable=False),
        sa.Column("linked_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("case_id", "clinical_document_id", name="uq_pathology_report_link"),
    )
    op.create_index("ix_pathology_report_links_case_id", "pathology_report_links", ["case_id"])


def downgrade():
    op.drop_table("pathology_report_links")
    op.drop_table("pathology_specimens")
    op.drop_table("pathology_cases")
    op.drop_table("procedure_interventions")
