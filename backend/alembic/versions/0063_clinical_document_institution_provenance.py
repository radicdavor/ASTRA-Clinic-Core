"""Add canonical institution provenance to clinical documents.

Revision ID: 0063_clinical_document_institution_provenance
Revises: 0062_signed_report_addendum_integrity
"""

from alembic import op
import sqlalchemy as sa


revision = "0063_clinical_document_institution_provenance"
down_revision = "0062_signed_report_addendum_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("clinical_documents", sa.Column("institution_id", sa.Integer(), nullable=True))
    op.create_index("ix_clinical_documents_institution_id", "clinical_documents", ["institution_id"])
    op.create_foreign_key(
        "fk_clinical_documents_institution_id_institutions",
        "clinical_documents",
        "institutions",
        ["institution_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.execute(
        """
        WITH provenance_candidates AS (
            SELECT document.id AS document_id, clinic.institution_id
            FROM clinical_documents AS document
            JOIN clinics AS clinic ON clinic.id = document.clinic_id
            WHERE clinic.institution_id IS NOT NULL
            UNION
            SELECT document.id AS document_id, clinic.institution_id
            FROM clinical_documents AS document
            JOIN appointments AS appointment ON appointment.id = document.appointment_id
            JOIN clinics AS clinic ON clinic.id = appointment.clinic_id
            WHERE clinic.institution_id IS NOT NULL
            UNION
            SELECT document.id AS document_id, clinic.institution_id
            FROM clinical_documents AS document
            JOIN patient_journeys AS journey ON journey.id = document.journey_id
            JOIN clinics AS clinic ON clinic.id = journey.clinic_id
            WHERE clinic.institution_id IS NOT NULL
        ), resolved AS (
            SELECT document_id, min(institution_id) AS institution_id
            FROM provenance_candidates
            GROUP BY document_id
            HAVING count(DISTINCT institution_id) = 1
        )
        UPDATE clinical_documents AS document
        SET institution_id = resolved.institution_id
        FROM resolved
        WHERE document.id = resolved.document_id
        """
    )


def downgrade():
    op.drop_constraint(
        "fk_clinical_documents_institution_id_institutions",
        "clinical_documents",
        type_="foreignkey",
    )
    op.drop_index("ix_clinical_documents_institution_id", table_name="clinical_documents")
    op.drop_column("clinical_documents", "institution_id")
