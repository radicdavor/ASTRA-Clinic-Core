"""Program 2 document ingestion and OCR boundary.

Revision ID: 0041_program2_documents
Revises: 0040_program2_preparation
"""

from alembic import op
import sqlalchemy as sa


revision = "0041_program2_documents"
down_revision = "0040_program2_preparation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("clinical_documents", sa.Column("journey_id", sa.Integer(), nullable=True))
    op.add_column("clinical_documents", sa.Column("clinical_episode_id", sa.Integer(), nullable=True))
    op.add_column("clinical_documents", sa.Column("upload_channel", sa.String(60), nullable=True))
    op.add_column("clinical_documents", sa.Column("original_filename", sa.String(255), nullable=True))
    op.add_column("clinical_documents", sa.Column("mime_type", sa.String(120), nullable=True))
    op.add_column("clinical_documents", sa.Column("checksum_sha256", sa.String(64), nullable=True))
    op.add_column("clinical_documents", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.add_column("clinical_documents", sa.Column("lifecycle_status", sa.String(50), nullable=False, server_default="received"))
    op.add_column("clinical_documents", sa.Column("ocr_text", sa.Text(), nullable=True))
    op.add_column("clinical_documents", sa.Column("extraction_confidence", sa.Numeric(5, 4), nullable=True))
    op.add_column("clinical_documents", sa.Column("classification_confidence", sa.Numeric(5, 4), nullable=True))
    op.add_column("clinical_documents", sa.Column("provenance_json", sa.JSON(), nullable=True))
    op.add_column("clinical_documents", sa.Column("received_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_clinical_documents_journey", "clinical_documents", "patient_journeys", ["journey_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_clinical_documents_episode", "clinical_documents", "clinical_episodes", ["clinical_episode_id"], ["id"], ondelete="SET NULL")
    for column in ("journey_id", "clinical_episode_id", "upload_channel", "checksum_sha256", "lifecycle_status", "received_at"):
        op.create_index(f"ix_clinical_documents_{column}", "clinical_documents", [column])

    op.create_table(
        "document_processing_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinical_document_id", sa.Integer(), sa.ForeignKey("clinical_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(40), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_metadata_json", sa.JSON(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_document_processing_jobs_clinical_document_id", "document_processing_jobs", ["clinical_document_id"])
    op.create_index("ix_document_processing_jobs_job_type", "document_processing_jobs", ["job_type"])
    op.create_index("ix_document_processing_jobs_status", "document_processing_jobs", ["status"])


def downgrade():
    op.drop_table("document_processing_jobs")
    op.drop_constraint("fk_clinical_documents_episode", "clinical_documents", type_="foreignkey")
    op.drop_constraint("fk_clinical_documents_journey", "clinical_documents", type_="foreignkey")
    for column in ("received_at", "lifecycle_status", "checksum_sha256", "upload_channel", "clinical_episode_id", "journey_id"):
        op.drop_index(f"ix_clinical_documents_{column}", table_name="clinical_documents")
    for column in (
        "received_at", "provenance_json", "classification_confidence", "extraction_confidence", "ocr_text",
        "lifecycle_status", "file_size_bytes", "checksum_sha256", "mime_type", "original_filename",
        "upload_channel", "clinical_episode_id", "journey_id",
    ):
        op.drop_column("clinical_documents", column)
