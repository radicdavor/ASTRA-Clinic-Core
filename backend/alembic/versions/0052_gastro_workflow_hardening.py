"""Gastro workflow hardening foundations.

Revision ID: 0052_gastro_hardening
Revises: 0051_activity_billing
"""
from alembic import op
from hashlib import sha256
import json
import sqlalchemy as sa

revision = "0052_gastro_hardening"
down_revision = "0051_activity_billing"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("patients", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("patient_journeys", sa.Column("package_version_id", sa.Integer(), nullable=True))
    op.add_column("patient_journeys", sa.Column("package_booking_key", sa.String(160), nullable=True))
    op.create_foreign_key("fk_patient_journey_package_version", "patient_journeys", "service_package_versions", ["package_version_id"], ["id"])
    op.create_index("ix_patient_journey_package_booking_key", "patient_journeys", ["package_booking_key"], unique=True)
    op.create_table(
        "activity_preparation_requirements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("journey_activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requirement_key", sa.String(100), nullable=False),
        sa.Column("label", sa.String(220), nullable=False),
        sa.Column("patient_instruction", sa.Text(), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("state", sa.String(40), nullable=False, server_default="assigned"),
        sa.Column("source_template_key", sa.String(120), nullable=False),
        sa.Column("source_template_version", sa.String(40), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("activity_id", "requirement_key", name="uq_activity_preparation_requirement"),
    )
    op.create_index("ix_activity_preparation_activity", "activity_preparation_requirements", ["activity_id"])
    op.create_index("ix_activity_preparation_key", "activity_preparation_requirements", ["requirement_key"])

    op.add_column("signed_clinical_reports", sa.Column("content_hash", sa.String(128), nullable=True))
    op.add_column("signed_clinical_reports", sa.Column("hash_algorithm", sa.String(30), nullable=False, server_default="sha256"))
    connection = op.get_bind()
    reports = connection.execute(sa.text(
        "SELECT id, rendered_content, structured_data_json FROM signed_clinical_reports WHERE content_hash IS NULL"
    )).mappings()
    for report in reports:
        canonical = json.dumps(report["structured_data_json"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = sha256(f"{report['rendered_content']}\n{canonical}".encode()).hexdigest()
        connection.execute(
            sa.text("UPDATE signed_clinical_reports SET content_hash = :digest, hash_algorithm = 'sha256' WHERE id = :report_id"),
            {"digest": digest, "report_id": report["id"]},
        )
    op.alter_column("signed_clinical_reports", "content_hash", nullable=False)

    op.add_column("report_delivery_events", sa.Column("recipient_source", sa.String(40), nullable=False, server_default="patient_verified"))
    op.add_column("report_delivery_events", sa.Column("alternate_recipient_reason", sa.Text(), nullable=True))
    op.add_column("report_delivery_events", sa.Column("idempotency_key", sa.String(160), nullable=True))
    op.create_index("ix_report_delivery_idempotency", "report_delivery_events", ["idempotency_key"], unique=True)

    op.add_column("pathology_cases", sa.Column("communication_disposition", sa.String(80), nullable=True))
    op.add_column("pathology_cases", sa.Column("communication_note", sa.Text(), nullable=True))
    op.add_column("pathology_cases", sa.Column("communication_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("pathology_cases", sa.Column("communication_decided_by", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_pathology_communication_user", "pathology_cases", "users", ["communication_decided_by"], ["id"])
    op.add_column("pathology_cases", sa.Column("communication_decided_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("""
    CREATE FUNCTION prevent_signed_report_mutation() RETURNS trigger AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'signed clinical reports are immutable';
      END IF;
      IF NEW.form_instance_id IS DISTINCT FROM OLD.form_instance_id
         OR NEW.form_version_id IS DISTINCT FROM OLD.form_version_id
         OR NEW.clinical_document_id IS DISTINCT FROM OLD.clinical_document_id
         OR NEW.activity_id IS DISTINCT FROM OLD.activity_id
         OR NEW.journey_id IS DISTINCT FROM OLD.journey_id
         OR NEW.patient_id IS DISTINCT FROM OLD.patient_id
         OR NEW.document_type IS DISTINCT FROM OLD.document_type
         OR NEW.title IS DISTINCT FROM OLD.title
         OR NEW.structured_data_json IS DISTINCT FROM OLD.structured_data_json
         OR NEW.rendered_content IS DISTINCT FROM OLD.rendered_content
         OR NEW.version_number IS DISTINCT FROM OLD.version_number
         OR NEW.signer_user_id IS DISTINCT FROM OLD.signer_user_id
         OR NEW.signer_name IS DISTINCT FROM OLD.signer_name
         OR NEW.signed_at IS DISTINCT FROM OLD.signed_at
         OR NEW.supersedes_report_id IS DISTINCT FROM OLD.supersedes_report_id
         OR NEW.content_hash IS DISTINCT FROM OLD.content_hash
         OR NEW.hash_algorithm IS DISTINCT FROM OLD.hash_algorithm
      THEN
        RAISE EXCEPTION 'signed clinical reports are immutable';
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_signed_report_immutable
    BEFORE UPDATE OR DELETE ON signed_clinical_reports
    FOR EACH ROW EXECUTE FUNCTION prevent_signed_report_mutation();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_signed_report_immutable ON signed_clinical_reports; DROP FUNCTION IF EXISTS prevent_signed_report_mutation()")
    op.drop_column("pathology_cases", "communication_decided_at")
    op.drop_constraint("fk_pathology_communication_user", "pathology_cases", type_="foreignkey")
    op.drop_column("pathology_cases", "communication_decided_by")
    op.drop_column("pathology_cases", "communication_attempts")
    op.drop_column("pathology_cases", "communication_note")
    op.drop_column("pathology_cases", "communication_disposition")
    op.drop_index("ix_report_delivery_idempotency", table_name="report_delivery_events")
    op.drop_column("report_delivery_events", "idempotency_key")
    op.drop_column("report_delivery_events", "alternate_recipient_reason")
    op.drop_column("report_delivery_events", "recipient_source")
    op.drop_column("signed_clinical_reports", "hash_algorithm")
    op.drop_column("signed_clinical_reports", "content_hash")
    op.drop_index("ix_activity_preparation_key", table_name="activity_preparation_requirements")
    op.drop_index("ix_activity_preparation_activity", table_name="activity_preparation_requirements")
    op.drop_table("activity_preparation_requirements")
    op.drop_index("ix_patient_journey_package_booking_key", table_name="patient_journeys")
    op.drop_constraint("fk_patient_journey_package_version", "patient_journeys", type_="foreignkey")
    op.drop_column("patient_journeys", "package_booking_key")
    op.drop_column("patient_journeys", "package_version_id")
    op.drop_column("patients", "email_verified_at")
