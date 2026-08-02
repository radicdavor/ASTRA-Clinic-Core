"""Add controlled patient identity reconciliation.

Revision ID: 0072_patient_identity_reconciliation
Revises: 0071_membership_taxonomy
"""

from alembic import op
import sqlalchemy as sa

revision = "0072_patient_identity_reconciliation"
down_revision = "0071_membership_taxonomy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_identity_reconciliation_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("requesting_institution_id", sa.Integer(), sa.ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("requesting_clinic_id", sa.Integer(), sa.ForeignKey("clinics.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("requested_by_api_key_id", sa.Integer(), sa.ForeignKey("api_keys.id", ondelete="RESTRICT")),
        sa.Column("status", sa.String(48), nullable=False, server_default="pending_review"),
        sa.Column("submitted_identity_snapshot", sa.JSON(), nullable=False),
        sa.Column("submitted_identity_fingerprint", sa.String(64), nullable=False),
        sa.Column("candidate_patient_ids", sa.JSON(), nullable=False),
        sa.Column("match_reasons", sa.JSON(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("decision_reason", sa.Text()),
        sa.Column("result_patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="RESTRICT")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status in ('pending_review','approved_link','confirmed_distinct','rejected_insufficient_evidence','cancelled')", name="ck_patient_identity_reconciliation_status"),
    )
    for name, columns in (
        ("ix_patient_reconcile_status", ["status"]),
        ("ix_patient_reconcile_clinic", ["requesting_clinic_id"]),
        ("ix_patient_reconcile_institution", ["requesting_institution_id"]),
        ("ix_patient_reconcile_requester_user", ["requested_by_user_id"]),
        ("ix_patient_reconcile_requester_key", ["requested_by_api_key_id"]),
        ("ix_patient_reconcile_reviewer", ["reviewed_by_user_id"]),
        ("ix_patient_reconcile_fingerprint", ["submitted_identity_fingerprint"]),
        ("ix_patient_reconcile_result", ["result_patient_id"]),
    ):
        op.create_index(name, "patient_identity_reconciliation_requests", columns)
    op.create_index("uq_patient_identity_reconciliation_active", "patient_identity_reconciliation_requests", ["requesting_clinic_id", "submitted_identity_fingerprint"], unique=True, postgresql_where=sa.text("status = 'pending_review'"))
    op.execute("INSERT INTO permissions (name, description) VALUES ('patients.identity_reconciliation.review', 'Review controlled Patient identity reconciliation requests.') ON CONFLICT (name) DO NOTHING")
    op.execute("INSERT INTO roles (name, professional_category, description) VALUES ('identity_reviewer', 'administrative', 'Explicit Patient identity reconciliation reviewer.') ON CONFLICT (name) DO NOTHING")
    op.execute("INSERT INTO role_permissions (role_id, permission_id) SELECT roles.id, permissions.id FROM roles CROSS JOIN permissions WHERE roles.name = 'identity_reviewer' AND permissions.name = 'patients.identity_reconciliation.review' ON CONFLICT DO NOTHING")


def downgrade() -> None:
    op.execute("DELETE FROM role_permissions USING roles, permissions WHERE role_permissions.role_id = roles.id AND role_permissions.permission_id = permissions.id AND roles.name = 'identity_reviewer' AND permissions.name = 'patients.identity_reconciliation.review'")
    op.execute("DELETE FROM roles WHERE name = 'identity_reviewer'")
    op.execute("DELETE FROM permissions WHERE name = 'patients.identity_reconciliation.review'")
    op.drop_index("uq_patient_identity_reconciliation_active", table_name="patient_identity_reconciliation_requests")
    for name in (
        "ix_patient_reconcile_result",
        "ix_patient_reconcile_fingerprint",
        "ix_patient_reconcile_reviewer",
        "ix_patient_reconcile_requester_key",
        "ix_patient_reconcile_requester_user",
        "ix_patient_reconcile_institution",
        "ix_patient_reconcile_clinic",
        "ix_patient_reconcile_status",
    ):
        op.drop_index(name, table_name="patient_identity_reconciliation_requests")
    op.drop_table("patient_identity_reconciliation_requests")
