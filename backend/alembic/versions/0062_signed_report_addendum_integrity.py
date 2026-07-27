"""Link addenda to the exact signed report version.

Revision ID: 0062_signed_report_addendum_integrity
Revises: 0061_institution_model_clinical_record
"""

from alembic import op
import sqlalchemy as sa


revision = "0062_signed_report_addendum_integrity"
down_revision = "0061_institution_model_clinical_record"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("clinical_document_addenda", sa.Column("signed_report_id", sa.Integer(), nullable=True))
    op.create_index("ix_clinical_document_addenda_signed_report_id", "clinical_document_addenda", ["signed_report_id"])
    op.create_foreign_key(
        "fk_clinical_document_addenda_signed_report_id_signed_reports",
        "clinical_document_addenda",
        "signed_clinical_reports",
        ["signed_report_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.execute(
        """
        UPDATE clinical_document_addenda AS addendum
        SET
            signed_report_id = report.id,
            original_document_type = 'signed_clinical_report'
        FROM signed_clinical_reports AS report
        WHERE addendum.original_document_id = report.clinical_document_id
          AND addendum.signed_report_id IS NULL
        """
    )


def downgrade():
    op.drop_constraint(
        "fk_clinical_document_addenda_signed_report_id_signed_reports",
        "clinical_document_addenda",
        type_="foreignkey",
    )
    op.drop_index("ix_clinical_document_addenda_signed_report_id", table_name="clinical_document_addenda")
    op.drop_column("clinical_document_addenda", "signed_report_id")
