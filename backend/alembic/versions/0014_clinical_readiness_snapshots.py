"""clinical readiness snapshots

Revision ID: 0014_clinical_readiness_snapshots
Revises: 0013_ai_extraction_lifecycle
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_clinical_readiness_snapshots"
down_revision = "0013_ai_extraction_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_readiness_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column("preview_generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("preview_status", sa.String(length=60), nullable=False),
        sa.Column("preview_summary", sa.Text(), nullable=False),
        sa.Column("template_key", sa.String(length=120), nullable=True),
        sa.Column("template_label", sa.String(length=180), nullable=True),
        sa.Column("template_version", sa.String(length=80), nullable=True),
        sa.Column("template_binding_status", sa.String(length=80), nullable=True),
        sa.Column("template_binding_warning", sa.Text(), nullable=True),
        sa.Column("is_preview_snapshot", sa.Boolean(), nullable=False),
        sa.Column("items_json", sa.JSON(), nullable=False),
        sa.Column("limitations_json", sa.JSON(), nullable=False),
        sa.Column("source_warnings_json", sa.JSON(), nullable=False),
        sa.Column("source_refs_json", sa.JSON(), nullable=False),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("snapshot_reason", sa.Text(), nullable=False),
        sa.Column("superseded_by_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_reason", sa.Text(), nullable=True),
        sa.CheckConstraint("length(trim(snapshot_reason)) > 0", name="ck_clinical_readiness_snapshots_reason_non_empty"),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.ForeignKeyConstraint(["superseded_by_snapshot_id"], ["clinical_readiness_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_readiness_snapshots_appointment_id"), "clinical_readiness_snapshots", ["appointment_id"])
    op.create_index(op.f("ix_clinical_readiness_snapshots_patient_id"), "clinical_readiness_snapshots", ["patient_id"])
    op.create_index(op.f("ix_clinical_readiness_snapshots_service_id"), "clinical_readiness_snapshots", ["service_id"])
    op.create_index(op.f("ix_clinical_readiness_snapshots_created_at"), "clinical_readiness_snapshots", ["created_at"])
    op.create_index(op.f("ix_clinical_readiness_snapshots_created_by_user_id"), "clinical_readiness_snapshots", ["created_by_user_id"])
    op.create_index(op.f("ix_clinical_readiness_snapshots_preview_generated_at"), "clinical_readiness_snapshots", ["preview_generated_at"])
    op.create_index(op.f("ix_clinical_readiness_snapshots_preview_status"), "clinical_readiness_snapshots", ["preview_status"])
    op.create_index(op.f("ix_clinical_readiness_snapshots_template_key"), "clinical_readiness_snapshots", ["template_key"])
    op.create_index(op.f("ix_clinical_readiness_snapshots_template_version"), "clinical_readiness_snapshots", ["template_version"])
    op.create_index(op.f("ix_clinical_readiness_snapshots_template_binding_status"), "clinical_readiness_snapshots", ["template_binding_status"])
    op.create_index(
        op.f("ix_clinical_readiness_snapshots_superseded_by_snapshot_id"),
        "clinical_readiness_snapshots",
        ["superseded_by_snapshot_id"],
    )
    op.create_index("ix_clinical_readiness_snapshots_appointment_created_at", "clinical_readiness_snapshots", ["appointment_id", "created_at"])
    op.create_index("ix_clinical_readiness_snapshots_patient_created_at", "clinical_readiness_snapshots", ["patient_id", "created_at"])
    op.create_index(
        "ix_clinical_readiness_snapshots_template_key_version",
        "clinical_readiness_snapshots",
        ["template_key", "template_version"],
    )


def downgrade() -> None:
    op.drop_index("ix_clinical_readiness_snapshots_template_key_version", table_name="clinical_readiness_snapshots")
    op.drop_index("ix_clinical_readiness_snapshots_patient_created_at", table_name="clinical_readiness_snapshots")
    op.drop_index("ix_clinical_readiness_snapshots_appointment_created_at", table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_superseded_by_snapshot_id"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_template_binding_status"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_template_version"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_template_key"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_preview_status"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_preview_generated_at"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_created_by_user_id"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_created_at"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_service_id"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_patient_id"), table_name="clinical_readiness_snapshots")
    op.drop_index(op.f("ix_clinical_readiness_snapshots_appointment_id"), table_name="clinical_readiness_snapshots")
    op.drop_table("clinical_readiness_snapshots")
