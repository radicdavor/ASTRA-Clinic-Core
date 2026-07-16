"""Multi-service journey activities and service packages.

Revision ID: 0047_multi_service
Revises: 0046_encounter_findings_opinion
"""
from alembic import op
import sqlalchemy as sa

revision = "0047_multi_service"
down_revision = "0046_encounter_findings_opinion"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "journey_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("journey_id", sa.Integer(), sa.ForeignKey("patient_journeys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("activity_key", sa.String(120), nullable=False),
        sa.Column("activity_kind", sa.String(60), nullable=False),
        sa.Column("specialty_key", sa.String(80), nullable=False),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=True),
        sa.Column("primary_provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("depends_on_activity_id", sa.Integer(), sa.ForeignKey("journey_activities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("planned_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("planned_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="planned"),
        sa.Column("not_performed_reason", sa.Text(), nullable=True),
        sa.Column("form_resolution_status", sa.String(40), nullable=False, server_default="unresolved"),
        sa.Column("billing_status", sa.String(40), nullable=False, server_default="not_ready"),
        sa.Column("consumables_status", sa.String(40), nullable=False, server_default="not_ready"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("started_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("completed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("sequence > 0", name="ck_journey_activities_sequence_positive"),
        sa.CheckConstraint("planned_end > planned_start", name="ck_journey_activities_planned_range"),
        sa.UniqueConstraint("appointment_id", name="uq_journey_activities_appointment_id"),
        sa.UniqueConstraint("journey_id", "activity_key", name="uq_journey_activities_key"),
        sa.UniqueConstraint("journey_id", "sequence", name="uq_journey_activities_sequence"),
    )
    for column in ("journey_id", "service_id", "activity_kind", "specialty_key", "clinic_id", "primary_provider_id", "room_id", "status", "planned_start"):
        op.create_index(f"ix_journey_activities_{column}", "journey_activities", [column])

    op.create_table(
        "journey_activity_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("journey_activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("role_key", sa.String(60), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(40), nullable=False, server_default="assigned"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("activity_id", "provider_id", "role_key", name="uq_journey_activity_participant_role"),
    )
    op.create_index("ix_journey_activity_participants_activity_id", "journey_activity_participants", ["activity_id"])
    op.create_index("ix_journey_activity_participants_provider_id", "journey_activity_participants", ["provider_id"])

    op.create_table(
        "service_packages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("package_key", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specialty_key", sa.String(80), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_service_packages_specialty_key", "service_packages", ["specialty_key"])

    op.create_table(
        "service_package_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("service_packages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("package_id", "version", name="uq_service_package_version"),
    )
    op.create_index("ix_service_package_versions_package_id", "service_package_versions", ["package_id"])
    op.create_index("ix_service_package_versions_status", "service_package_versions", ["status"])

    op.create_table(
        "service_package_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("package_version_id", sa.Integer(), sa.ForeignKey("service_package_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("activity_key", sa.String(120), nullable=False),
        sa.Column("activity_kind", sa.String(60), nullable=False),
        sa.Column("specialty_key", sa.String(80), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("relative_start_offset_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("default_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("preferred_clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=True),
        sa.Column("preferred_room_type", sa.String(80), nullable=True),
        sa.Column("depends_on_item_id", sa.Integer(), sa.ForeignKey("service_package_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("preparation_requirements_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("billing_inclusion_rule", sa.String(40), nullable=False, server_default="include"),
        sa.CheckConstraint("sequence > 0", name="ck_service_package_items_sequence_positive"),
        sa.CheckConstraint("default_duration_minutes > 0", name="ck_service_package_items_duration_positive"),
        sa.UniqueConstraint("package_version_id", "sequence", name="uq_service_package_item_sequence"),
        sa.UniqueConstraint("package_version_id", "activity_key", name="uq_service_package_item_key"),
    )
    op.create_index("ix_service_package_items_package_version_id", "service_package_items", ["package_version_id"])
    op.create_index("ix_service_package_items_service_id", "service_package_items", ["service_id"])

    # Every legacy journey receives one activity derived from its anchor appointment.
    op.execute(sa.text("""
        INSERT INTO journey_activities (
            journey_id, appointment_id, service_id, activity_key, activity_kind,
            specialty_key, clinic_id, primary_provider_id, room_id, sequence,
            required, planned_start, planned_end, status, form_resolution_status,
            billing_status, consumables_status, created_by, created_at, updated_at
        )
        SELECT
            j.id, a.id, a.service_id, 'primary', 'specialist_consultation',
            COALESCE(m.key, 'general'), r.clinic_id, a.provider_id, a.room_id, 1,
            TRUE, a.date + a.start_time, a.date + a.end_time,
            CASE WHEN j.encounter_status = 'completed' THEN 'completed'
                 WHEN j.encounter_status = 'in_progress' THEN 'in_progress'
                 ELSE 'planned' END,
            'legacy',
            j.billing_status, j.consumables_status, j.created_by, j.created_at, j.updated_at
        FROM patient_journeys j
        JOIN appointments a ON a.id = j.appointment_id
        JOIN services s ON s.id = a.service_id
        LEFT JOIN modules m ON m.id = s.module_id
        LEFT JOIN rooms r ON r.id = a.room_id
    """))

    op.add_column("journey_encounters", sa.Column("activity_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_journey_encounters_activity", "journey_encounters", "journey_activities", ["activity_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_journey_encounters_activity_id", "journey_encounters", ["activity_id"], unique=True)
    op.execute(sa.text("""
        UPDATE journey_encounters e
        SET activity_id = a.id
        FROM journey_activities a
        WHERE a.journey_id = e.journey_id AND a.activity_key = 'primary'
    """))
    op.drop_constraint("journey_encounters_journey_id_key", "journey_encounters", type_="unique")


def downgrade():
    op.create_unique_constraint("journey_encounters_journey_id_key", "journey_encounters", ["journey_id"])
    op.drop_index("ix_journey_encounters_activity_id", table_name="journey_encounters")
    op.drop_constraint("fk_journey_encounters_activity", "journey_encounters", type_="foreignkey")
    op.drop_column("journey_encounters", "activity_id")
    op.drop_table("service_package_items")
    op.drop_table("service_package_versions")
    op.drop_table("service_packages")
    op.drop_table("journey_activity_participants")
    op.drop_table("journey_activities")
