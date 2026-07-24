"""Add provenance for episodes, derived clinical data, and audit events.

Revision ID: 0064_pr3_scope_provenance
Revises: 0063_clinical_document_institution_provenance
"""

from alembic import op
import sqlalchemy as sa


revision = "0064_pr3_scope_provenance"
down_revision = "0063_clinical_document_institution_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clinical_episodes", sa.Column("institution_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_clinical_episodes_institution_id",
        "clinical_episodes",
        "institutions",
        ["institution_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_clinical_episodes_institution_id", "clinical_episodes", ["institution_id"])

    op.add_column("clinical_findings", sa.Column("institution_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_clinical_findings_institution_id",
        "clinical_findings",
        "institutions",
        ["institution_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_clinical_findings_institution_id", "clinical_findings", ["institution_id"])

    op.add_column("clinical_open_questions", sa.Column("institution_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_clinical_open_questions_institution_id",
        "clinical_open_questions",
        "institutions",
        ["institution_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_clinical_open_questions_institution_id", "clinical_open_questions", ["institution_id"])

    op.add_column("audit_logs", sa.Column("scope_type", sa.String(length=40), nullable=True))
    op.add_column("audit_logs", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.add_column("audit_logs", sa.Column("institution_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_audit_logs_clinic_id",
        "audit_logs",
        "clinics",
        ["clinic_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_audit_logs_institution_id",
        "audit_logs",
        "institutions",
        ["institution_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_audit_logs_scope_type", "audit_logs", ["scope_type"])
    op.create_index("ix_audit_logs_clinic_id", "audit_logs", ["clinic_id"])
    op.create_index("ix_audit_logs_institution_id", "audit_logs", ["institution_id"])

    op.execute(
        """
        WITH candidates AS (
            SELECT e.id AS episode_id, c.institution_id
            FROM clinical_episodes e
            JOIN appointments a ON a.episode_id = e.id
            JOIN clinics c ON c.id = a.clinic_id
            WHERE c.institution_id IS NOT NULL
            UNION
            SELECT e.id, d.institution_id
            FROM clinical_episodes e
            JOIN clinical_documents d ON d.clinical_episode_id = e.id
            WHERE d.institution_id IS NOT NULL
            UNION
            SELECT e.id, c.institution_id
            FROM clinical_episodes e
            JOIN journey_encounters je ON je.clinical_episode_id = e.id
            JOIN clinics c ON c.id = je.clinic_id
            WHERE c.institution_id IS NOT NULL
        ), resolved AS (
            SELECT episode_id, min(institution_id) AS institution_id
            FROM candidates
            GROUP BY episode_id
            HAVING count(DISTINCT institution_id) = 1
        )
        UPDATE clinical_episodes e
        SET institution_id = resolved.institution_id
        FROM resolved
        WHERE e.id = resolved.episode_id
        """
    )
    op.execute(
        """
        UPDATE clinical_findings f
        SET institution_id = d.institution_id
        FROM clinical_documents d
        WHERE f.source_document_id = d.id
          AND d.institution_id IS NOT NULL
        """
    )
    op.execute(
        """
        WITH candidates AS (
            SELECT q.id AS question_id, d.institution_id
            FROM clinical_open_questions q
            JOIN clinical_documents d ON d.id = q.source_document_id
            WHERE d.institution_id IS NOT NULL
            UNION
            SELECT q.id, f.institution_id
            FROM clinical_open_questions q
            JOIN clinical_findings f ON f.id = q.finding_id
            WHERE f.institution_id IS NOT NULL
        ), resolved AS (
            SELECT question_id, min(institution_id) AS institution_id
            FROM candidates
            GROUP BY question_id
            HAVING count(DISTINCT institution_id) = 1
        )
        UPDATE clinical_open_questions q
        SET institution_id = resolved.institution_id
        FROM resolved
        WHERE q.id = resolved.question_id
        """
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_institution_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_clinic_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_scope_type", table_name="audit_logs")
    op.drop_constraint("fk_audit_logs_institution_id", "audit_logs", type_="foreignkey")
    op.drop_constraint("fk_audit_logs_clinic_id", "audit_logs", type_="foreignkey")
    op.drop_column("audit_logs", "institution_id")
    op.drop_column("audit_logs", "clinic_id")
    op.drop_column("audit_logs", "scope_type")

    op.drop_index("ix_clinical_open_questions_institution_id", table_name="clinical_open_questions")
    op.drop_constraint("fk_clinical_open_questions_institution_id", "clinical_open_questions", type_="foreignkey")
    op.drop_column("clinical_open_questions", "institution_id")

    op.drop_index("ix_clinical_findings_institution_id", table_name="clinical_findings")
    op.drop_constraint("fk_clinical_findings_institution_id", "clinical_findings", type_="foreignkey")
    op.drop_column("clinical_findings", "institution_id")

    op.drop_index("ix_clinical_episodes_institution_id", table_name="clinical_episodes")
    op.drop_constraint("fk_clinical_episodes_institution_id", "clinical_episodes", type_="foreignkey")
    op.drop_column("clinical_episodes", "institution_id")
