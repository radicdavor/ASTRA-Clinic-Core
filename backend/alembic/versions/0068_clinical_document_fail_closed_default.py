"""Make future clinical-document classification fail closed.

Revision ID: 0068_document_classification_default
Revises: 0067_audit_aggregation
"""

from alembic import op
import sqlalchemy as sa


revision = "0068_document_classification_default"
down_revision = "0067_audit_aggregation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "clinical_documents",
        "record_classification",
        existing_type=sa.String(length=40),
        server_default="unclassified",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "clinical_documents",
        "record_classification",
        existing_type=sa.String(length=40),
        server_default="clinical",
        existing_nullable=False,
    )
