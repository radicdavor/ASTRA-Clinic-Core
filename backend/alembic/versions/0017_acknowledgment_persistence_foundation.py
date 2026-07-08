"""acknowledgment persistence foundation

Revision ID: 0017_acknowledgment_persistence_foundation
Revises: 0016_snapshot_db_immutability
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_acknowledgment_persistence_foundation"
down_revision = "0016_snapshot_db_immutability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_readiness_review_acknowledgments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=True),
        sa.Column("advisory_signal_key", sa.String(length=160), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_role", sa.String(length=80), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("limitations_json", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column("not_decision_disclaimer", sa.Text(), nullable=False),
        sa.Column("is_decision", sa.Boolean(), nullable=False),
        sa.Column("is_clearance", sa.Boolean(), nullable=False),
        sa.Column("is_override", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(trim(reason)) > 0", name="ck_clinical_readiness_review_acknowledgments_reason_non_empty"),
        sa.CheckConstraint("is_decision = false", name="ck_clinical_readiness_review_acknowledgments_not_decision"),
        sa.CheckConstraint("is_clearance = false", name="ck_clinical_readiness_review_acknowledgments_not_clearance"),
        sa.CheckConstraint("is_override = false", name="ck_clinical_readiness_review_acknowledgments_not_override"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["snapshot_id"], ["clinical_readiness_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_readiness_review_acknowledgments_actor_role"), "clinical_readiness_review_acknowledgments", ["actor_role"], unique=False)
    op.create_index(op.f("ix_clinical_readiness_review_acknowledgments_actor_user_id"), "clinical_readiness_review_acknowledgments", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_clinical_readiness_review_acknowledgments_advisory_signal_key"), "clinical_readiness_review_acknowledgments", ["advisory_signal_key"], unique=False)
    op.create_index(op.f("ix_clinical_readiness_review_acknowledgments_appointment_id"), "clinical_readiness_review_acknowledgments", ["appointment_id"], unique=False)
    op.create_index(op.f("ix_clinical_readiness_review_acknowledgments_created_at"), "clinical_readiness_review_acknowledgments", ["created_at"], unique=False)
    op.create_index(op.f("ix_clinical_readiness_review_acknowledgments_patient_id"), "clinical_readiness_review_acknowledgments", ["patient_id"], unique=False)
    op.create_index(op.f("ix_clinical_readiness_review_acknowledgments_snapshot_id"), "clinical_readiness_review_acknowledgments", ["snapshot_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_readiness_review_acknowledgments_snapshot_id"), table_name="clinical_readiness_review_acknowledgments")
    op.drop_index(op.f("ix_clinical_readiness_review_acknowledgments_patient_id"), table_name="clinical_readiness_review_acknowledgments")
    op.drop_index(op.f("ix_clinical_readiness_review_acknowledgments_created_at"), table_name="clinical_readiness_review_acknowledgments")
    op.drop_index(op.f("ix_clinical_readiness_review_acknowledgments_appointment_id"), table_name="clinical_readiness_review_acknowledgments")
    op.drop_index(op.f("ix_clinical_readiness_review_acknowledgments_advisory_signal_key"), table_name="clinical_readiness_review_acknowledgments")
    op.drop_index(op.f("ix_clinical_readiness_review_acknowledgments_actor_user_id"), table_name="clinical_readiness_review_acknowledgments")
    op.drop_index(op.f("ix_clinical_readiness_review_acknowledgments_actor_role"), table_name="clinical_readiness_review_acknowledgments")
    op.drop_table("clinical_readiness_review_acknowledgments")
