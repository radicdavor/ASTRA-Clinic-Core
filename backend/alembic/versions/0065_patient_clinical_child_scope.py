"""Add institution provenance to patient clinical child records.

Revision ID: 0065_patient_clinical_child_scope
Revises: 0064_pr3_scope_provenance
"""

from alembic import op
import sqlalchemy as sa


revision = "0065_patient_clinical_child_scope"
down_revision = "0064_pr3_scope_provenance"
branch_labels = None
depends_on = None


TABLES = ("lab_orders", "therapies", "workflow_tasks")


def _add_institution_scope(table: str) -> None:
    op.add_column(table, sa.Column("institution_id", sa.Integer(), nullable=True))
    op.create_foreign_key(f"fk_{table}_institution_id", table, "institutions", ["institution_id"], ["id"], ondelete="RESTRICT")
    op.create_index(f"ix_{table}_institution_id", table, ["institution_id"])


def upgrade() -> None:
    for table in TABLES:
        _add_institution_scope(table)

    op.execute(
        """
        WITH candidates AS (
            SELECT o.id AS object_id, e.institution_id FROM lab_orders o
            JOIN clinical_episodes e ON e.id = o.episode_id WHERE e.institution_id IS NOT NULL
            UNION
            SELECT o.id, c.institution_id FROM lab_orders o
            JOIN appointments a ON a.id = o.appointment_id
            JOIN clinics c ON c.id = a.clinic_id WHERE c.institution_id IS NOT NULL
        ), resolved AS (
            SELECT object_id, min(institution_id) AS institution_id FROM candidates
            GROUP BY object_id HAVING count(DISTINCT institution_id) = 1
        )
        UPDATE lab_orders o SET institution_id = resolved.institution_id
        FROM resolved WHERE o.id = resolved.object_id
        """
    )
    op.execute(
        """
        UPDATE therapies t SET institution_id = e.institution_id
        FROM clinical_episodes e
        WHERE t.episode_id = e.id AND e.institution_id IS NOT NULL
        """
    )
    op.execute(
        """
        WITH candidates AS (
            SELECT t.id AS object_id, e.institution_id FROM workflow_tasks t
            JOIN clinical_episodes e ON e.id = t.episode_id WHERE e.institution_id IS NOT NULL
            UNION
            SELECT t.id, c.institution_id FROM workflow_tasks t
            JOIN appointments a ON a.id = t.appointment_id
            JOIN clinics c ON c.id = a.clinic_id WHERE c.institution_id IS NOT NULL
        ), resolved AS (
            SELECT object_id, min(institution_id) AS institution_id FROM candidates
            GROUP BY object_id HAVING count(DISTINCT institution_id) = 1
        )
        UPDATE workflow_tasks t SET institution_id = resolved.institution_id
        FROM resolved WHERE t.id = resolved.object_id
        """
    )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_institution_id", table_name=table)
        op.drop_constraint(f"fk_{table}_institution_id", table, type_="foreignkey")
        op.drop_column(table, "institution_id")
