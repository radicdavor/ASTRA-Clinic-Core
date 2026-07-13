"""Add structured patient therapies.

Revision ID: 0038_therapies
Revises: 0037_seed_gastroenterology_operational_protocols
"""
from alembic import op
import sqlalchemy as sa
revision="0038_therapies";down_revision="0037_seed_gastroenterology_operational_protocols";branch_labels=None;depends_on=None
def upgrade():
    op.create_table("therapies",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("patient_id",sa.Integer(),sa.ForeignKey("patients.id"),nullable=False),sa.Column("episode_id",sa.Integer(),sa.ForeignKey("clinical_episodes.id")),sa.Column("parent_therapy_id",sa.Integer(),sa.ForeignKey("therapies.id")),sa.Column("name",sa.String(180),nullable=False),sa.Column("instructions",sa.Text(),nullable=False),sa.Column("start_date",sa.Date(),nullable=False),sa.Column("end_date",sa.Date()),sa.Column("status",sa.String(30),nullable=False,server_default="active"),sa.Column("prescriber",sa.String(160)),sa.Column("notes",sa.Text()),sa.Column("stopped_at",sa.DateTime(timezone=True)),sa.Column("stopped_by",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("stop_reason",sa.Text()),sa.Column("completed_at",sa.DateTime(timezone=True)),sa.Column("completed_by",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("completion_note",sa.Text()),sa.Column("created_by",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    for column in ("patient_id","episode_id","parent_therapy_id","name","start_date","end_date","status"): op.create_index(f"ix_therapies_{column}","therapies",[column])
def downgrade(): op.drop_table("therapies")
