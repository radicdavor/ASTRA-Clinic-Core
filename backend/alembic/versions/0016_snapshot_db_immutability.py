"""snapshot db immutability trigger

Revision ID: 0016_snapshot_db_immutability
Revises: 0015_snapshot_idempotency
Create Date: 2026-07-08
"""

from alembic import op


revision = "0016_snapshot_db_immutability"
down_revision = "0015_snapshot_idempotency"
branch_labels = None
depends_on = None


PROTECTED_FIELDS = [
    "id",
    "appointment_id",
    "patient_id",
    "service_id",
    "created_at",
    "created_by_user_id",
    "schema_version",
    "preview_generated_at",
    "preview_status",
    "preview_summary",
    "template_key",
    "template_label",
    "template_version",
    "template_binding_status",
    "template_binding_warning",
    "is_preview_snapshot",
    "items_json",
    "limitations_json",
    "source_warnings_json",
    "source_refs_json",
    "disclaimer",
    "snapshot_reason",
    "idempotency_key",
    "idempotency_fingerprint",
]


def _protected_fields_same_sql() -> str:
    return "\n        AND ".join(f"NEW.{field} IS NOT DISTINCT FROM OLD.{field}" for field in PROTECTED_FIELDS)


def upgrade() -> None:
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION astra_prevent_clinical_readiness_snapshot_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            protected_fields_same boolean;
            first_supersession_transition boolean;
            unchanged_row boolean;
        BEGIN
            protected_fields_same := {_protected_fields_same_sql()};

            unchanged_row :=
                protected_fields_same
                AND NEW.superseded_by_snapshot_id IS NOT DISTINCT FROM OLD.superseded_by_snapshot_id
                AND NEW.superseded_at IS NOT DISTINCT FROM OLD.superseded_at
                AND NEW.superseded_reason IS NOT DISTINCT FROM OLD.superseded_reason;

            IF unchanged_row THEN
                RETURN NEW;
            END IF;

            first_supersession_transition :=
                protected_fields_same
                AND OLD.superseded_by_snapshot_id IS NULL
                AND OLD.superseded_at IS NULL
                AND OLD.superseded_reason IS NULL
                AND NEW.superseded_by_snapshot_id IS NOT NULL
                AND NEW.superseded_at IS NOT NULL
                AND NEW.superseded_reason IS NOT NULL;

            IF first_supersession_transition THEN
                RETURN NEW;
            END IF;

            RAISE EXCEPTION
                'Clinical Readiness Snapshot is immutable after insert except first-time additive supersession metadata';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_clinical_readiness_snapshots_immutable_update
        BEFORE UPDATE ON clinical_readiness_snapshots
        FOR EACH ROW
        EXECUTE FUNCTION astra_prevent_clinical_readiness_snapshot_mutation();
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION astra_prevent_clinical_readiness_snapshot_delete()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'Clinical Readiness Snapshot rows cannot be deleted';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_clinical_readiness_snapshots_immutable_delete
        BEFORE DELETE ON clinical_readiness_snapshots
        FOR EACH ROW
        EXECUTE FUNCTION astra_prevent_clinical_readiness_snapshot_delete();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_clinical_readiness_snapshots_immutable_delete ON clinical_readiness_snapshots")
    op.execute("DROP FUNCTION IF EXISTS astra_prevent_clinical_readiness_snapshot_delete()")
    op.execute("DROP TRIGGER IF EXISTS trg_clinical_readiness_snapshots_immutable_update ON clinical_readiness_snapshots")
    op.execute("DROP FUNCTION IF EXISTS astra_prevent_clinical_readiness_snapshot_mutation()")
