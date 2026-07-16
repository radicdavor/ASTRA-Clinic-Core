"""Immutable signed clinical reports, printing and delivery history.

Revision ID: 0050_signed_reports
Revises: 0049_pathology
"""
from alembic import op
import sqlalchemy as sa

revision = "0050_signed_reports"
down_revision = "0049_pathology"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "signed_clinical_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("form_instance_id", sa.Integer(), sa.ForeignKey("clinical_form_instances.id"), nullable=False),
        sa.Column("form_version_id", sa.Integer(), sa.ForeignKey("clinical_form_versions.id"), nullable=False),
        sa.Column("clinical_document_id", sa.Integer(), sa.ForeignKey("clinical_documents.id"), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("journey_activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("journey_id", sa.Integer(), sa.ForeignKey("patient_journeys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("document_type", sa.String(80), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("structured_data_json", sa.JSON(), nullable=False),
        sa.Column("rendered_content", sa.Text(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("signer_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("signer_name", sa.String(160), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes_report_id", sa.Integer(), sa.ForeignKey("signed_clinical_reports.id", ondelete="SET NULL")),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("form_instance_id", name="uq_signed_clinical_reports_form_instance"),
        sa.UniqueConstraint("clinical_document_id", name="uq_signed_clinical_reports_document"),
    )
    for column in ("form_instance_id", "clinical_document_id", "activity_id", "journey_id", "patient_id", "document_type", "signed_at"):
        op.create_index(f"ix_signed_clinical_reports_{column}", "signed_clinical_reports", [column])
    op.create_table(
        "report_print_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("signed_clinical_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("printed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("printed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("request_id", sa.String(120)),
    )
    op.create_index("ix_report_print_events_report_id", "report_print_events", ["report_id"])
    op.create_table(
        "report_delivery_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("signed_clinical_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="queued_stub"),
        sa.Column("provider_mode", sa.String(60), nullable=False, server_default="local_demo"),
        sa.Column("initiated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("correlation_id", sa.String(120), nullable=False, unique=True),
        sa.CheckConstraint("status in ('queued_stub','sent','delivered','failed','cancelled')", name="ck_report_delivery_status"),
    )
    op.create_index("ix_report_delivery_events_report_id", "report_delivery_events", ["report_id"])
    op.create_index("ix_report_delivery_events_status", "report_delivery_events", ["status"])


def downgrade():
    op.drop_table("report_delivery_events")
    op.drop_table("report_print_events")
    op.drop_table("signed_clinical_reports")
