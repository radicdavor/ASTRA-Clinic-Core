"""provider weekly working hours

Revision ID: 0025_provider_weekly_working_hours
Revises: 0024_clinic_room_visibility
"""
from alembic import op
import sqlalchemy as sa
revision = "0025_provider_weekly_working_hours"
down_revision = "0024_clinic_room_visibility"
branch_labels = None
depends_on = None
DEFAULT = '{"0":{"enabled":true,"start":"07:00","end":"15:00"},"1":{"enabled":true,"start":"07:00","end":"15:00"},"2":{"enabled":true,"start":"07:00","end":"15:00"},"3":{"enabled":true,"start":"07:00","end":"15:00"},"4":{"enabled":true,"start":"07:00","end":"15:00"},"5":{"enabled":false,"start":"07:00","end":"15:00"},"6":{"enabled":false,"start":"07:00","end":"15:00"}}'
def upgrade() -> None:
    op.add_column("providers", sa.Column("weekly_working_hours", sa.JSON(), nullable=True))
    op.get_bind().execute(sa.text("UPDATE providers SET weekly_working_hours = CAST(:schedule AS JSON)").bindparams(schedule=DEFAULT))
    op.alter_column("providers", "weekly_working_hours", nullable=False)
def downgrade() -> None:
    op.drop_column("providers", "weekly_working_hours")
