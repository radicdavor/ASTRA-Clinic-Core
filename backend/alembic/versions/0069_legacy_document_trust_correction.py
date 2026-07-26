"""Demote legacy clinical documents without trusted review provenance.

Revision ID: 0069_legacy_document_trust
Revises: 0068_document_classification_default
"""

from alembic import op
import sqlalchemy as sa


revision = "0069_legacy_document_trust"
down_revision = "0068_document_classification_default"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clinical_documents", sa.Column("classification_reviewed_by", sa.Integer(), nullable=True))
    op.add_column("clinical_documents", sa.Column("classification_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_clinical_documents_classification_reviewed_by_users",
        "clinical_documents",
        "users",
        ["classification_reviewed_by"],
        ["id"],
    )
    op.create_index(
        "ix_clinical_documents_classification_reviewed_by",
        "clinical_documents",
        ["classification_reviewed_by"],
    )
    op.execute(
        """
        UPDATE clinical_documents
        SET
            classification_reviewed_by = reviewed_by,
            classification_reviewed_at = reviewed_at
        WHERE record_classification = 'clinical'
          AND physician_reviewed = true
          AND reviewed_by IS NOT NULL
          AND reviewed_at IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE clinical_documents
        SET record_classification = 'unclassified'
        WHERE record_classification = 'clinical'
          AND NOT (
            is_clinical_record = true
            AND classification_reviewed_by IS NOT NULL
            AND classification_reviewed_at IS NOT NULL
            AND clinic_id IS NOT NULL
            AND institution_id IS NOT NULL
            AND EXISTS (
                SELECT 1
                FROM clinics
                WHERE clinics.id = clinical_documents.clinic_id
                  AND clinics.active = true
                  AND clinics.institution_id = clinical_documents.institution_id
            )
            AND EXISTS (
                SELECT 1
                FROM patient_clinic_associations
                WHERE patient_clinic_associations.patient_id = clinical_documents.patient_id
                  AND patient_clinic_associations.clinic_id = clinical_documents.clinic_id
                  AND patient_clinic_associations.active = true
            )
            AND EXISTS (
                SELECT 1
                FROM users
                JOIN roles ON roles.id = users.role_id
                WHERE users.id = clinical_documents.classification_reviewed_by
                  AND users.active = true
                  AND roles.professional_category = 'medical_staff'
            )
          )
        """
    )


def downgrade() -> None:
    # The prior trusted classification cannot be reconstructed safely. A
    # downgrade intentionally preserves the fail-closed data correction.
    op.drop_index("ix_clinical_documents_classification_reviewed_by", table_name="clinical_documents")
    op.drop_constraint(
        "fk_clinical_documents_classification_reviewed_by_users",
        "clinical_documents",
        type_="foreignkey",
    )
    op.drop_column("clinical_documents", "classification_reviewed_at")
    op.drop_column("clinical_documents", "classification_reviewed_by")
