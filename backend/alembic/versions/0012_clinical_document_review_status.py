"""clinical document review status

Revision ID: 0012_clinical_document_review_status
Revises: 0011_reception_resource_scheduling
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_clinical_document_review_status"
down_revision = "0011_reception_resource_scheduling"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clinical_documents",
        sa.Column("review_status", sa.String(length=40), nullable=False, server_default="draft"),
    )
    op.create_index(op.f("ix_clinical_documents_review_status"), "clinical_documents", ["review_status"])

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE clinical_documents
            SET review_status = CASE
                WHEN physician_reviewed = true THEN 'reviewed'
                WHEN ai_summary IS NOT NULL OR key_findings IS NOT NULL OR recommendations IS NOT NULL THEN 'needs_physician_review'
                ELSE 'draft'
            END
            """
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_documents_review_status"), table_name="clinical_documents")
    op.drop_column("clinical_documents", "review_status")
