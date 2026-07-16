"""Versioned clinician form engine.

Revision ID: 0048_clinical_forms
Revises: 0047_multi_service
"""
from alembic import op
import sqlalchemy as sa


revision = "0048_clinical_forms"
down_revision = "0047_multi_service"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "clinical_form_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("form_key", sa.String(120), nullable=False, unique=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("specialty_key", sa.String(80), nullable=False),
        sa.Column("activity_kind", sa.String(60), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("owner_clinic_id", sa.Integer(), sa.ForeignKey("clinics.id")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_clinical_form_definitions_specialty_kind", "clinical_form_definitions", ["specialty_key", "activity_kind"])

    op.create_table(
        "clinical_form_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("definition_id", sa.Integer(), sa.ForeignKey("clinical_form_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("sections_json", sa.JSON(), nullable=False),
        sa.Column("validation_schema_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("print_layout_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("output_document_type", sa.String(80), nullable=False),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("supersedes_version_id", sa.Integer(), sa.ForeignKey("clinical_form_versions.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("definition_id", "version", name="uq_clinical_form_definition_version"),
        sa.CheckConstraint("status in ('draft','published','retired')", name="ck_clinical_form_versions_status"),
    )
    op.create_index("ix_clinical_form_versions_definition_id", "clinical_form_versions", ["definition_id"])
    op.create_index("ix_clinical_form_versions_status", "clinical_form_versions", ["status"])

    op.create_table(
        "service_form_bindings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id")),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id")),
        sa.Column("specialty_key", sa.String(80)),
        sa.Column("activity_kind", sa.String(60)),
        sa.Column("form_version_id", sa.Integer(), sa.ForeignKey("clinical_form_versions.id"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("service_id is not null or (specialty_key is not null and activity_kind is not null)", name="ck_service_form_binding_scope"),
    )
    op.create_index("ix_service_form_bindings_service_clinic", "service_form_bindings", ["service_id", "clinic_id"])
    op.create_index("ix_service_form_bindings_specialty_kind", "service_form_bindings", ["specialty_key", "activity_kind"])

    op.create_table(
        "clinical_form_instances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("journey_activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("form_version_id", sa.Integer(), sa.ForeignKey("clinical_form_versions.id"), nullable=False),
        sa.Column("purpose", sa.String(60), nullable=False, server_default="clinical_report"),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("data_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("rendered_summary", sa.Text()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("last_edited_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("completed_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("signed_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("signed_at", sa.DateTime(timezone=True)),
        sa.Column("amended_from_instance_id", sa.Integer(), sa.ForeignKey("clinical_form_instances.id", ondelete="SET NULL")),
        sa.Column("binding_source", sa.String(80), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("activity_id", "purpose", "amended_from_instance_id", name="uq_clinical_form_instance_lineage"),
        sa.CheckConstraint("status in ('draft','in_progress','completed','signed','amended','void')", name="ck_clinical_form_instances_status"),
    )
    op.create_index("ix_clinical_form_instances_activity_id", "clinical_form_instances", ["activity_id"])
    op.create_index("ix_clinical_form_instances_status", "clinical_form_instances", ["status"])

    op.create_table(
        "clinical_form_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("instance_id", sa.Integer(), sa.ForeignKey("clinical_form_instances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("data_json", sa.JSON(), nullable=False),
        sa.Column("rendered_summary", sa.Text()),
        sa.Column("edited_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("instance_id", "revision_number", name="uq_clinical_form_revision_number"),
    )
    op.create_index("ix_clinical_form_revisions_instance_id", "clinical_form_revisions", ["instance_id"])

    op.add_column("service_package_items", sa.Column("form_binding_override_version_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_package_item_form_override", "service_package_items", "clinical_form_versions", ["form_binding_override_version_id"], ["id"], ondelete="SET NULL")
    op.add_column("journey_activities", sa.Column("package_item_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_journey_activity_package_item", "journey_activities", "service_package_items", ["package_item_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_journey_activities_package_item_id", "journey_activities", ["package_item_id"])


def downgrade():
    op.drop_index("ix_journey_activities_package_item_id", table_name="journey_activities")
    op.drop_constraint("fk_journey_activity_package_item", "journey_activities", type_="foreignkey")
    op.drop_column("journey_activities", "package_item_id")
    op.drop_constraint("fk_package_item_form_override", "service_package_items", type_="foreignkey")
    op.drop_column("service_package_items", "form_binding_override_version_id")
    op.drop_table("clinical_form_revisions")
    op.drop_table("clinical_form_instances")
    op.drop_table("service_form_bindings")
    op.drop_table("clinical_form_versions")
    op.drop_table("clinical_form_definitions")
