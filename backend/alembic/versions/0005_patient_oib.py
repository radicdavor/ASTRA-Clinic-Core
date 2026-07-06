"""patient oib

Revision ID: 0005_patient_oib
Revises: 0004_fiscalization_metadata
Create Date: 2026-07-06
"""

from alembic import op


revision = "0005_patient_oib"
down_revision = "0004_fiscalization_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS oib VARCHAR(11)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_patients_oib ON patients (oib) WHERE oib IS NOT NULL")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_patients_oib")
    op.execute("ALTER TABLE patients DROP COLUMN IF EXISTS oib")
