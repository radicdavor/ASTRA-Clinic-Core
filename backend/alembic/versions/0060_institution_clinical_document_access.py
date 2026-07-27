"""Add institution clinical document access metadata.

Revision ID: 0060_institution_clinical_document_access
Revises: 0059_user_sessions
"""

from alembic import op
import sqlalchemy as sa


revision = "0060_institution_clinical_document_access"
down_revision = "0059_user_sessions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("roles", sa.Column("professional_category", sa.String(length=60), nullable=False, server_default="administrative"))
    op.create_index("ix_roles_professional_category", "roles", ["professional_category"])
    op.add_column("clinics", sa.Column("institution_key", sa.String(length=120), nullable=False, server_default="default"))
    op.create_index("ix_clinics_institution_key", "clinics", ["institution_key"])
    op.add_column("clinical_documents", sa.Column("author_user_id", sa.Integer(), nullable=True))
    op.add_column("clinical_documents", sa.Column("author_professional_role", sa.String(length=80), nullable=True))
    op.add_column("clinical_documents", sa.Column("is_clinical_record", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_foreign_key("fk_clinical_documents_author_user_id_users", "clinical_documents", "users", ["author_user_id"], ["id"])
    op.create_index("ix_clinical_documents_author_user_id", "clinical_documents", ["author_user_id"])
    op.create_index("ix_clinical_documents_is_clinical_record", "clinical_documents", ["is_clinical_record"])
    op.create_table(
        "clinical_document_addenda",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_document_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["original_document_id"], ["clinical_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clinical_document_addenda_original_document_id", "clinical_document_addenda", ["original_document_id"])
    op.create_index("ix_clinical_document_addenda_author_user_id", "clinical_document_addenda", ["author_user_id"])
    op.create_index("ix_clinical_document_addenda_status", "clinical_document_addenda", ["status"])
    op.create_index("ix_clinical_document_addenda_signed_at", "clinical_document_addenda", ["signed_at"])
    op.execute("UPDATE roles SET professional_category = 'medical_staff' WHERE name IN ('physician', 'nurse', 'document_reviewer')")


def downgrade():
    op.drop_index("ix_clinical_document_addenda_signed_at", table_name="clinical_document_addenda")
    op.drop_index("ix_clinical_document_addenda_status", table_name="clinical_document_addenda")
    op.drop_index("ix_clinical_document_addenda_author_user_id", table_name="clinical_document_addenda")
    op.drop_index("ix_clinical_document_addenda_original_document_id", table_name="clinical_document_addenda")
    op.drop_table("clinical_document_addenda")
    op.drop_index("ix_clinical_documents_is_clinical_record", table_name="clinical_documents")
    op.drop_index("ix_clinical_documents_author_user_id", table_name="clinical_documents")
    op.drop_constraint("fk_clinical_documents_author_user_id_users", "clinical_documents", type_="foreignkey")
    op.drop_column("clinical_documents", "is_clinical_record")
    op.drop_column("clinical_documents", "author_professional_role")
    op.drop_column("clinical_documents", "author_user_id")
    op.drop_index("ix_clinics_institution_key", table_name="clinics")
    op.drop_column("clinics", "institution_key")
    op.drop_index("ix_roles_professional_category", table_name="roles")
    op.drop_column("roles", "professional_category")
