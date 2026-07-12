"""workflow engine

Revision ID: 0021_workflow_engine
Revises: 0020_provider_contact_working_hours
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa

revision = "0021_workflow_engine"
down_revision = "0020_provider_contact_working_hours"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("default_priority", sa.String(40), nullable=False, server_default="routine"),
        sa.Column("checklist_items", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workflow_templates_key", "workflow_templates", ["key"], unique=True)
    op.create_index("ix_workflow_templates_name", "workflow_templates", ["name"])
    op.create_index("ix_workflow_templates_active", "workflow_templates", ["active"])
    op.create_table(
        "workflow_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(40), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(40), nullable=False, server_default="routine"),
        sa.Column("due_date", sa.Date()),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("episode_id", sa.Integer(), sa.ForeignKey("clinical_episodes.id")),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id")),
        sa.Column("assignee_provider_id", sa.Integer(), sa.ForeignKey("providers.id")),
        sa.Column("responsible_role", sa.String(60)),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("workflow_templates.id")),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("title", "status", "priority", "due_date", "patient_id", "episode_id", "appointment_id", "assignee_provider_id", "responsible_role"):
        op.create_index(f"ix_workflow_tasks_{column}", "workflow_tasks", [column])
    op.create_table(
        "workflow_checklist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("workflow_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(220), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workflow_checklist_items_task_id", "workflow_checklist_items", ["task_id"])
    op.create_index("ix_workflow_checklist_items_completed", "workflow_checklist_items", ["completed"])


def downgrade() -> None:
    op.drop_table("workflow_checklist_items")
    op.drop_table("workflow_tasks")
    op.drop_table("workflow_templates")
