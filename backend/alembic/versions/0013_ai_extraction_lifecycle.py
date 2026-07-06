"""ai extraction lifecycle

Revision ID: 0013_ai_extraction_lifecycle
Revises: 0012_clinical_document_review_status
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_ai_extraction_lifecycle"
down_revision = "0012_clinical_document_review_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clinical_documents",
        sa.Column("ai_extraction_status", sa.String(length=40), nullable=False, server_default="not_run"),
    )
    op.add_column("clinical_documents", sa.Column("ai_extraction_generated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("clinical_documents", sa.Column("ai_extraction_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_clinical_documents_ai_extraction_status"), "clinical_documents", ["ai_extraction_status"])

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE clinical_documents
            SET
                ai_extraction_status = CASE
                    WHEN review_status = 'rejected' THEN 'rejected'
                    WHEN review_status = 'reviewed'
                        AND (ai_summary IS NOT NULL OR key_findings IS NOT NULL OR recommendations IS NOT NULL)
                        THEN 'accepted'
                    WHEN ai_summary IS NOT NULL OR key_findings IS NOT NULL OR recommendations IS NOT NULL
                        THEN 'generated'
                    ELSE 'not_run'
                END,
                ai_extraction_generated_at = CASE
                    WHEN ai_summary IS NOT NULL OR key_findings IS NOT NULL OR recommendations IS NOT NULL
                        THEN updated_at
                    ELSE NULL
                END,
                ai_extraction_updated_at = CASE
                    WHEN review_status = 'rejected'
                        OR ai_summary IS NOT NULL OR key_findings IS NOT NULL OR recommendations IS NOT NULL
                        THEN updated_at
                    ELSE NULL
                END
            """
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_documents_ai_extraction_status"), table_name="clinical_documents")
    op.drop_column("clinical_documents", "ai_extraction_updated_at")
    op.drop_column("clinical_documents", "ai_extraction_generated_at")
    op.drop_column("clinical_documents", "ai_extraction_status")
