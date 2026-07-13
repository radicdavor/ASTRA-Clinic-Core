"""Program 2 timeline and source-linked AI summary.

Revision ID: 0042_program2_summary
Revises: 0041_program2_documents
"""

from alembic import op
import sqlalchemy as sa


revision = "0042_program2_summary"
down_revision = "0041_program2_documents"
branch_labels = None
depends_on = None


def timestamp_columns():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def upgrade():
    op.create_table(
        "journey_ai_summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("journey_id", sa.Integer(), sa.ForeignKey("patient_journeys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model_name", sa.String(120), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="pending_review"),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("source_refs_json", sa.JSON(), nullable=False),
        sa.Column("limitations_json", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
    )
    for column in ("journey_id", "status", "generated_at"):
        op.create_index(f"ix_journey_ai_summaries_{column}", "journey_ai_summaries", [column])
    op.create_table(
        "journey_ai_summary_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("summary_id", sa.Integer(), sa.ForeignKey("journey_ai_summaries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("fact_type", sa.String(40), nullable=False),
        sa.Column("source_document_id", sa.Integer(), sa.ForeignKey("clinical_documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("limitation", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(40), nullable=False, server_default="pending_review"),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
    )
    for column in ("summary_id", "fact_type", "source_document_id", "review_status"):
        op.create_index(f"ix_journey_ai_summary_facts_{column}", "journey_ai_summary_facts", [column])


def downgrade():
    op.drop_table("journey_ai_summary_facts")
    op.drop_table("journey_ai_summaries")
