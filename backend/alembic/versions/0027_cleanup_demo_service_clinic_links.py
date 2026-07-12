"""Clean demo service links that crossed clinic boundaries.

Revision ID: 0027_cleanup_demo_service_clinic_links
Revises: 0026_provider_availability
"""

from alembic import op
import sqlalchemy as sa


revision = "0027_cleanup_demo_service_clinic_links"
down_revision = "0026_provider_availability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        DELETE FROM room_services rs
        USING services s, rooms r, clinics c
        WHERE rs.service_id = s.id
          AND rs.room_id = r.id
          AND r.clinic_id = c.id
          AND ((s.code LIKE 'GASTRO-%' AND lower(c.name) LIKE '%estetik%')
            OR (s.code LIKE 'AEST-%' AND lower(c.name) LIKE '%gastro%'))
    """))


def downgrade() -> None:
    pass
