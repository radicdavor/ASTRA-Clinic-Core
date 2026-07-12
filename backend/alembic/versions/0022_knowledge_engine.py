"""knowledge engine

Revision ID: 0022_knowledge_engine
Revises: 0021_workflow_engine
"""
from alembic import op
import sqlalchemy as sa

revision = "0022_knowledge_engine"
down_revision = "0021_workflow_engine"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("knowledge_protocols", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("key", sa.String(100), nullable=False), sa.Column("title", sa.String(220), nullable=False), sa.Column("specialty", sa.String(100), nullable=False), sa.Column("version", sa.String(40), nullable=False), sa.Column("summary", sa.Text(), nullable=False), sa.Column("source_title", sa.String(260), nullable=False), sa.Column("source_url", sa.Text(), nullable=False), sa.Column("status", sa.String(40), nullable=False, server_default="draft"), sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("reviewed_at", sa.DateTime(timezone=True)), sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_knowledge_protocols_key", "knowledge_protocols", ["key"], unique=True)
    for col in ("title", "specialty", "status"): op.create_index(f"ix_knowledge_protocols_{col}", "knowledge_protocols", [col])
    op.create_table("knowledge_rules", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("protocol_id", sa.Integer(), sa.ForeignKey("knowledge_protocols.id", ondelete="CASCADE"), nullable=False), sa.Column("label", sa.String(220), nullable=False), sa.Column("condition_text", sa.Text(), nullable=False), sa.Column("guidance_text", sa.Text(), nullable=False), sa.Column("evidence_level", sa.String(80)), sa.Column("position", sa.Integer(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_knowledge_rules_protocol_id", "knowledge_rules", ["protocol_id"])

def downgrade() -> None:
    op.drop_table("knowledge_rules")
    op.drop_table("knowledge_protocols")
