"""Add institution model and clinical record metadata.

Revision ID: 0061_institution_model_clinical_record
Revises: 0060_institution_clinical_document_access
"""

from alembic import op
import sqlalchemy as sa


revision = "0061_institution_model_clinical_record"
down_revision = "0060_institution_clinical_document_access"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "institutions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_institutions_active", "institutions", ["active"])
    op.create_index("ix_institutions_code", "institutions", ["code"])
    op.create_index("ix_institutions_name", "institutions", ["name"])

    op.execute(
        """
        INSERT INTO institutions (code, name, active)
        SELECT DISTINCT
            clinics.institution_key,
            CASE
                WHEN clinics.institution_key = 'default' THEN 'ASTRA'
                ELSE clinics.institution_key
            END,
            true
        FROM clinics
        WHERE clinics.institution_key IS NOT NULL
        """
    )
    op.execute(
        """
        INSERT INTO institutions (code, name, active)
        SELECT 'default', 'ASTRA', true
        WHERE NOT EXISTS (SELECT 1 FROM institutions)
        """
    )

    op.add_column("clinics", sa.Column("institution_id", sa.Integer(), nullable=True))
    op.create_index("ix_clinics_institution_id", "clinics", ["institution_id"])
    op.create_foreign_key("fk_clinics_institution_id_institutions", "clinics", "institutions", ["institution_id"], ["id"])
    op.execute(
        """
        UPDATE clinics
        SET institution_id = institutions.id
        FROM institutions
        WHERE clinics.institution_key = institutions.code
        """
    )
    op.execute(
        """
        UPDATE clinics
        SET institution_id = (SELECT id FROM institutions WHERE code = 'default' LIMIT 1)
        WHERE institution_id IS NULL
        """
    )

    op.add_column("clinical_documents", sa.Column("record_classification", sa.String(length=40), nullable=False, server_default="clinical"))
    op.create_index("ix_clinical_documents_record_classification", "clinical_documents", ["record_classification"])

    op.add_column("clinical_document_addenda", sa.Column("original_document_type", sa.String(length=80), nullable=False, server_default="clinical_document"))
    op.add_column("clinical_document_addenda", sa.Column("patient_id", sa.Integer(), nullable=True))
    op.add_column("clinical_document_addenda", sa.Column("institution_id", sa.Integer(), nullable=True))
    op.add_column("clinical_document_addenda", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.add_column("clinical_document_addenda", sa.Column("signed_by_user_id", sa.Integer(), nullable=True))
    op.create_index("ix_clinical_document_addenda_original_document_type", "clinical_document_addenda", ["original_document_type"])
    op.create_index("ix_clinical_document_addenda_patient_id", "clinical_document_addenda", ["patient_id"])
    op.create_index("ix_clinical_document_addenda_institution_id", "clinical_document_addenda", ["institution_id"])
    op.create_index("ix_clinical_document_addenda_clinic_id", "clinical_document_addenda", ["clinic_id"])
    op.create_index("ix_clinical_document_addenda_signed_by_user_id", "clinical_document_addenda", ["signed_by_user_id"])
    op.create_foreign_key("fk_clinical_document_addenda_patient_id_patients", "clinical_document_addenda", "patients", ["patient_id"], ["id"])
    op.create_foreign_key("fk_clinical_document_addenda_institution_id_institutions", "clinical_document_addenda", "institutions", ["institution_id"], ["id"])
    op.create_foreign_key("fk_clinical_document_addenda_clinic_id_clinics", "clinical_document_addenda", "clinics", ["clinic_id"], ["id"])
    op.create_foreign_key("fk_clinical_document_addenda_signed_by_user_id_users", "clinical_document_addenda", "users", ["signed_by_user_id"], ["id"])
    op.execute(
        """
        UPDATE clinical_document_addenda
        SET
            patient_id = clinical_documents.patient_id,
            clinic_id = clinical_documents.clinic_id,
            institution_id = clinics.institution_id,
            signed_by_user_id = clinical_document_addenda.author_user_id
        FROM clinical_documents
        LEFT JOIN clinics ON clinics.id = clinical_documents.clinic_id
        WHERE clinical_document_addenda.original_document_id = clinical_documents.id
        """
    )


def downgrade():
    op.drop_constraint("fk_clinical_document_addenda_signed_by_user_id_users", "clinical_document_addenda", type_="foreignkey")
    op.drop_constraint("fk_clinical_document_addenda_clinic_id_clinics", "clinical_document_addenda", type_="foreignkey")
    op.drop_constraint("fk_clinical_document_addenda_institution_id_institutions", "clinical_document_addenda", type_="foreignkey")
    op.drop_constraint("fk_clinical_document_addenda_patient_id_patients", "clinical_document_addenda", type_="foreignkey")
    op.drop_index("ix_clinical_document_addenda_signed_by_user_id", table_name="clinical_document_addenda")
    op.drop_index("ix_clinical_document_addenda_clinic_id", table_name="clinical_document_addenda")
    op.drop_index("ix_clinical_document_addenda_institution_id", table_name="clinical_document_addenda")
    op.drop_index("ix_clinical_document_addenda_patient_id", table_name="clinical_document_addenda")
    op.drop_index("ix_clinical_document_addenda_original_document_type", table_name="clinical_document_addenda")
    op.drop_column("clinical_document_addenda", "signed_by_user_id")
    op.drop_column("clinical_document_addenda", "clinic_id")
    op.drop_column("clinical_document_addenda", "institution_id")
    op.drop_column("clinical_document_addenda", "patient_id")
    op.drop_column("clinical_document_addenda", "original_document_type")

    op.drop_index("ix_clinical_documents_record_classification", table_name="clinical_documents")
    op.drop_column("clinical_documents", "record_classification")

    op.drop_constraint("fk_clinics_institution_id_institutions", "clinics", type_="foreignkey")
    op.drop_index("ix_clinics_institution_id", table_name="clinics")
    op.drop_column("clinics", "institution_id")

    op.drop_index("ix_institutions_name", table_name="institutions")
    op.drop_index("ix_institutions_code", table_name="institutions")
    op.drop_index("ix_institutions_active", table_name="institutions")
    op.drop_table("institutions")
