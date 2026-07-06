"""reception resource scheduling

Revision ID: 0011_reception_resource_scheduling
Revises: 0010_patient_clinical_summaries
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_reception_resource_scheduling"
down_revision = "0010_patient_clinical_summaries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_clinics_active"), "clinics", ["active"])
    op.create_index(op.f("ix_clinics_name"), "clinics", ["name"])
    op.add_column("providers", sa.Column("staff_role", sa.String(length=60), nullable=False, server_default="physician"))
    op.add_column("providers", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_providers_staff_role"), "providers", ["staff_role"])
    op.create_foreign_key("fk_providers_clinic_id_clinics", "providers", "clinics", ["clinic_id"], ["id"])
    op.add_column("rooms", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_rooms_clinic_id_clinics", "rooms", "clinics", ["clinic_id"], ["id"])
    op.create_table(
        "room_services",
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.PrimaryKeyConstraint("room_id", "service_id"),
    )
    op.add_column("appointments", sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("appointments", sa.Column("identity_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("appointments", sa.Column("identity_verified_by", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_appointments_identity_verified_by_users", "appointments", "users", ["identity_verified_by"], ["id"])

    bind = op.get_bind()
    bind.execute(sa.text("INSERT INTO clinics (name, active) VALUES ('Gastroenterologija', true) ON CONFLICT (name) DO NOTHING"))
    clinic_id = bind.execute(sa.text("SELECT id FROM clinics WHERE name = 'Gastroenterologija'")).scalar()
    if clinic_id:
        bind.execute(sa.text("UPDATE rooms SET clinic_id = :clinic_id WHERE clinic_id IS NULL"), {"clinic_id": clinic_id})
        bind.execute(sa.text("UPDATE providers SET clinic_id = :clinic_id WHERE clinic_id IS NULL"), {"clinic_id": clinic_id})
    bind.execute(sa.text("INSERT INTO room_services (room_id, service_id) SELECT r.id, s.id FROM rooms r CROSS JOIN services s ON CONFLICT DO NOTHING"))


def downgrade() -> None:
    op.drop_constraint("fk_appointments_identity_verified_by_users", "appointments", type_="foreignkey")
    op.drop_column("appointments", "identity_verified_by")
    op.drop_column("appointments", "identity_verified_at")
    op.drop_column("appointments", "arrived_at")
    op.drop_table("room_services")
    op.drop_constraint("fk_rooms_clinic_id_clinics", "rooms", type_="foreignkey")
    op.drop_column("rooms", "clinic_id")
    op.drop_constraint("fk_providers_clinic_id_clinics", "providers", type_="foreignkey")
    op.drop_index(op.f("ix_providers_staff_role"), table_name="providers")
    op.drop_column("providers", "clinic_id")
    op.drop_column("providers", "staff_role")
    op.drop_index(op.f("ix_clinics_name"), table_name="clinics")
    op.drop_index(op.f("ix_clinics_active"), table_name="clinics")
    op.drop_table("clinics")
