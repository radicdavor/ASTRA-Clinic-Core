"""Activity report policies.

Revision ID: 0054_activity_report_policies
Revises: 0053_form_reliability
"""
from alembic import op
import sqlalchemy as sa


revision = "0054_activity_report_policies"
down_revision = "0053_form_reliability"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "activity_report_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=True),
        sa.Column("specialty_key", sa.String(80), nullable=True),
        sa.Column("activity_kind", sa.String(60), nullable=True),
        sa.Column("report_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("signature_required_before_activity_completion", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("signature_required_before_billing", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_post_visit_signing", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("policy_source", sa.String(80), nullable=False, server_default="configured"),
        sa.Column("policy_version", sa.String(40), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("service_id is not null or activity_kind is not null", name="ck_activity_report_policy_scope"),
        sa.CheckConstraint("policy_version <> ''", name="ck_activity_report_policy_version_nonempty"),
    )
    op.create_index("ix_activity_report_policy_service", "activity_report_policies", ["service_id"])
    op.create_index("ix_activity_report_policy_specialty_kind", "activity_report_policies", ["specialty_key", "activity_kind"])
    op.create_index("ix_activity_report_policy_active", "activity_report_policies", ["active"])


def downgrade():
    op.drop_index("ix_activity_report_policy_active", table_name="activity_report_policies")
    op.drop_index("ix_activity_report_policy_specialty_kind", table_name="activity_report_policies")
    op.drop_index("ix_activity_report_policy_service", table_name="activity_report_policies")
    op.drop_table("activity_report_policies")
