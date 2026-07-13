"""Program 2 patient journey foundation.

Revision ID: 0039_program2_journey
Revises: 0038_therapies
"""
from alembic import op
import sqlalchemy as sa

revision="0039_program2_journey";down_revision="0038_therapies";branch_labels=None;depends_on=None

def upgrade():
    op.create_table("patient_journeys",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("patient_id",sa.Integer(),sa.ForeignKey("patients.id"),nullable=False),sa.Column("appointment_id",sa.Integer(),sa.ForeignKey("appointments.id"),nullable=False),sa.Column("intake_channel",sa.String(30),nullable=False),sa.Column("current_stage",sa.String(50),nullable=False,server_default="requested"),sa.Column("document_status",sa.String(40),nullable=False,server_default="not_requested"),sa.Column("preparation_status",sa.String(40),nullable=False,server_default="not_assigned"),sa.Column("check_in_status",sa.String(40),nullable=False,server_default="not_arrived"),sa.Column("encounter_status",sa.String(40),nullable=False,server_default="not_started"),sa.Column("consumables_status",sa.String(40),nullable=False,server_default="not_ready"),sa.Column("billing_status",sa.String(40),nullable=False,server_default="not_ready"),sa.Column("payment_status",sa.String(40),nullable=False,server_default="not_due"),sa.Column("closed_at",sa.DateTime(timezone=True)),sa.Column("created_by",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("updated_by",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.UniqueConstraint("appointment_id",name="uq_patient_journeys_appointment_id"))
    for column in ("patient_id","appointment_id","intake_channel","current_stage","document_status","preparation_status","check_in_status","encounter_status","consumables_status","billing_status","payment_status","closed_at"): op.create_index(f"ix_patient_journeys_{column}","patient_journeys",[column])
    op.create_table("journey_events",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("journey_id",sa.Integer(),sa.ForeignKey("patient_journeys.id",ondelete="CASCADE"),nullable=False),sa.Column("event_type",sa.String(80),nullable=False),sa.Column("from_stage",sa.String(50)),sa.Column("to_stage",sa.String(50)),sa.Column("summary",sa.Text(),nullable=False),sa.Column("source_channel",sa.String(40),nullable=False),sa.Column("actor_user_id",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("actor_type",sa.String(40),nullable=False,server_default="user"),sa.Column("request_id",sa.String(80)),sa.Column("metadata_json",sa.JSON()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
    for column in ("journey_id","event_type","from_stage","to_stage","source_channel","request_id","created_at"): op.create_index(f"ix_journey_events_{column}","journey_events",[column])
    op.create_table("journey_blockers",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("journey_id",sa.Integer(),sa.ForeignKey("patient_journeys.id",ondelete="CASCADE"),nullable=False),sa.Column("blocker_key",sa.String(120),nullable=False),sa.Column("category",sa.String(60),nullable=False),sa.Column("title",sa.String(220),nullable=False),sa.Column("details",sa.Text()),sa.Column("is_clinical",sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column("status",sa.String(30),nullable=False,server_default="open"),sa.Column("created_by",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("resolved_by",sa.Integer(),sa.ForeignKey("users.id")),sa.Column("resolved_at",sa.DateTime(timezone=True)),sa.Column("resolution_note",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
    for column in ("journey_id","blocker_key","category","is_clinical","status"): op.create_index(f"ix_journey_blockers_{column}","journey_blockers",[column])

def downgrade():
    op.drop_table("journey_blockers");op.drop_table("journey_events");op.drop_table("patient_journeys")
