"""Bind API keys to one clinic and institution.

Revision ID: 0066_api_key_tenant_scope
Revises: 0065_patient_clinical_child_scope
"""

from alembic import op
import sqlalchemy as sa


revision = "0066_api_key_tenant_scope"
down_revision = "0065_patient_clinical_child_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("api_keys", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.add_column("api_keys", sa.Column("institution_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_api_keys_clinic_id", "api_keys", "clinics", ["clinic_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_api_keys_institution_id", "api_keys", "institutions", ["institution_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_api_keys_clinic_id", "api_keys", ["clinic_id"])
    op.create_index("ix_api_keys_institution_id", "api_keys", ["institution_id"])


def downgrade() -> None:
    op.drop_index("ix_api_keys_institution_id", table_name="api_keys")
    op.drop_index("ix_api_keys_clinic_id", table_name="api_keys")
    op.drop_constraint("fk_api_keys_institution_id", "api_keys", type_="foreignkey")
    op.drop_constraint("fk_api_keys_clinic_id", "api_keys", type_="foreignkey")
    op.drop_column("api_keys", "institution_id")
    op.drop_column("api_keys", "clinic_id")
