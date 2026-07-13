"""Program 2 unified encounter workspace.

Revision ID: 0044_program2_encounter
Revises: 0043_program2_checkin
"""
from alembic import op
import sqlalchemy as sa

revision="0044_program2_encounter";down_revision="0043_program2_checkin";branch_labels=None;depends_on=None
def upgrade():
 op.create_table("journey_encounters",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("journey_id",sa.Integer(),sa.ForeignKey("patient_journeys.id",ondelete="CASCADE"),nullable=False,unique=True),sa.Column("clinical_episode_id",sa.Integer(),sa.ForeignKey("clinical_episodes.id",ondelete="SET NULL")),sa.Column("status",sa.String(40),nullable=False,server_default="in_progress"),sa.Column("anamnesis",sa.Text()),sa.Column("examination",sa.Text()),sa.Column("procedure_findings",sa.Text()),sa.Column("diagnosis",sa.Text()),sa.Column("treatment",sa.Text()),sa.Column("recommendations",sa.Text()),sa.Column("follow_up_plan",sa.Text()),sa.Column("opened_by",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("opened_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("completed_by",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("completed_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
 op.create_index("ix_journey_encounters_journey_id","journey_encounters",["journey_id"]);op.create_index("ix_journey_encounters_clinical_episode_id","journey_encounters",["clinical_episode_id"]);op.create_index("ix_journey_encounters_status","journey_encounters",["status"])
def downgrade(): op.drop_table("journey_encounters")
