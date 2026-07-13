"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


# Frozen snapshot of the tables present when revision 0001 was authored.
# Never import application model metadata here: later models belong to later
# revisions and would otherwise be created prematurely on a clean database.
metadata = sa.MetaData()


def timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


roles = sa.Table(
    "roles", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("name", sa.String(80), nullable=False, unique=True),
    sa.Column("description", sa.Text()),
)
users = sa.Table(
    "users", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
    sa.Column("full_name", sa.String(160), nullable=False),
    sa.Column("password_hash", sa.String(255), nullable=False),
    sa.Column("active", sa.Boolean(), nullable=False),
    sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
    *timestamps(),
)
patients = sa.Table(
    "patients", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("first_name", sa.String(100), nullable=False, index=True),
    sa.Column("last_name", sa.String(100), nullable=False, index=True),
    sa.Column("date_of_birth", sa.Date()),
    sa.Column("email", sa.String(255)),
    sa.Column("phone", sa.String(80)),
    sa.Column("notes", sa.Text()),
    *timestamps(),
)
providers = sa.Table(
    "providers", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("full_name", sa.String(160), nullable=False, index=True),
    sa.Column("specialty", sa.String(120)),
    sa.Column("active", sa.Boolean(), nullable=False),
    *timestamps(),
)
rooms = sa.Table(
    "rooms", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("name", sa.String(120), nullable=False, unique=True),
    sa.Column("type", sa.String(80)),
    sa.Column("active", sa.Boolean(), nullable=False),
    *timestamps(),
)
modules = sa.Table(
    "modules", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("key", sa.String(80), nullable=False, unique=True),
    sa.Column("name", sa.String(120), nullable=False),
    sa.Column("description", sa.Text()),
    sa.Column("enabled", sa.Boolean(), nullable=False),
    *timestamps(),
)
services = sa.Table(
    "services", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("name", sa.String(160), nullable=False, index=True),
    sa.Column("code", sa.String(80), unique=True),
    sa.Column("duration_minutes", sa.Integer(), nullable=False),
    sa.Column("price", sa.Numeric(12, 2), nullable=False),
    sa.Column("module_id", sa.Integer(), sa.ForeignKey("modules.id")),
    sa.Column("active", sa.Boolean(), nullable=False),
    *timestamps(),
)
appointments = sa.Table(
    "appointments", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
    sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
    sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=False),
    sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
    sa.Column("date", sa.Date(), nullable=False, index=True),
    sa.Column("start_time", sa.Time(), nullable=False),
    sa.Column("end_time", sa.Time(), nullable=False),
    sa.Column("duration_minutes", sa.Integer(), nullable=False),
    sa.Column("status", sa.String(40), nullable=False, index=True),
    sa.Column("source", sa.String(40), nullable=False),
    sa.Column("notes", sa.Text()),
    sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    *timestamps(),
)
api_keys = sa.Table(
    "api_keys", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("name", sa.String(120), nullable=False),
    sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
    sa.Column("active", sa.Boolean(), nullable=False),
    *timestamps(),
)
audit_logs = sa.Table(
    "audit_logs", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id")),
    sa.Column("action", sa.String(40), nullable=False, index=True),
    sa.Column("entity_type", sa.String(120), nullable=False, index=True),
    sa.Column("entity_id", sa.Integer()),
    sa.Column("summary", sa.Text()),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
)
suppliers = sa.Table(
    "suppliers", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("name", sa.String(180), nullable=False, index=True),
    sa.Column("contact_person", sa.String(160)),
    sa.Column("email", sa.String(255)),
    sa.Column("phone", sa.String(80)),
    sa.Column("address", sa.Text()),
    sa.Column("vat_id", sa.String(80)),
    sa.Column("notes", sa.Text()),
    *timestamps(),
)
stock_locations = sa.Table(
    "stock_locations", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("name", sa.String(120), nullable=False, unique=True),
    sa.Column("type", sa.String(80), nullable=False),
    *timestamps(),
)
inventory_items = sa.Table(
    "inventory_items", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("sku", sa.String(80), nullable=False, unique=True, index=True),
    sa.Column("name", sa.String(180), nullable=False, index=True),
    sa.Column("category", sa.String(120)),
    sa.Column("unit_of_measure", sa.String(40), nullable=False),
    sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id")),
    sa.Column("current_stock", sa.Numeric(12, 2), nullable=False),
    sa.Column("minimum_stock", sa.Numeric(12, 2), nullable=False),
    sa.Column("reorder_point", sa.Numeric(12, 2), nullable=False),
    sa.Column("purchase_price", sa.Numeric(12, 2), nullable=False),
    sa.Column("selling_price", sa.Numeric(12, 2), nullable=False),
    sa.Column("expiration_tracking_enabled", sa.Boolean(), nullable=False),
    sa.Column("lot_tracking_enabled", sa.Boolean(), nullable=False),
    sa.Column("active", sa.Boolean(), nullable=False),
    *timestamps(),
)
inventory_batches = sa.Table(
    "inventory_batches", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("inventory_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id"), nullable=False),
    sa.Column("lot_number", sa.String(100), index=True),
    sa.Column("expiration_date", sa.Date(), index=True),
    sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
    sa.Column("location_id", sa.Integer(), sa.ForeignKey("stock_locations.id"), nullable=False),
    sa.Column("purchase_price", sa.Numeric(12, 2), nullable=False),
    sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id")),
    *timestamps(),
)
purchase_orders = sa.Table(
    "purchase_orders", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), nullable=False),
    sa.Column("status", sa.String(60), nullable=False),
    sa.Column("order_date", sa.Date(), nullable=False),
    sa.Column("expected_delivery_date", sa.Date()),
    sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
    sa.Column("notes", sa.Text()),
    *timestamps(),
)
purchase_order_lines = sa.Table(
    "purchase_order_lines", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("purchase_orders.id"), nullable=False),
    sa.Column("inventory_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id"), nullable=False),
    sa.Column("quantity_ordered", sa.Numeric(12, 2), nullable=False),
    sa.Column("quantity_received", sa.Numeric(12, 2), nullable=False),
    sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
    sa.Column("vat_rate", sa.Numeric(5, 2), nullable=False),
)
invoices = sa.Table(
    "invoices", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
    sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id")),
    sa.Column("invoice_number", sa.String(80), nullable=False, unique=True, index=True),
    sa.Column("invoice_date", sa.Date(), nullable=False),
    sa.Column("status", sa.String(60), nullable=False),
    sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
    sa.Column("payment_status", sa.String(60), nullable=False),
    sa.Column("payment_method", sa.String(80)),
    sa.Column("notes", sa.Text()),
    *timestamps(),
)
invoice_lines = sa.Table(
    "invoice_lines", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
    sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id")),
    sa.Column("inventory_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id")),
    sa.Column("description", sa.String(255), nullable=False),
    sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
    sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
    sa.Column("vat_rate", sa.Numeric(5, 2), nullable=False),
    sa.Column("total", sa.Numeric(12, 2), nullable=False),
)
stock_movements = sa.Table(
    "stock_movements", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("inventory_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id"), nullable=False),
    sa.Column("batch_id", sa.Integer(), sa.ForeignKey("inventory_batches.id")),
    sa.Column("from_location_id", sa.Integer(), sa.ForeignKey("stock_locations.id")),
    sa.Column("to_location_id", sa.Integer(), sa.ForeignKey("stock_locations.id")),
    sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
    sa.Column("movement_type", sa.String(60), nullable=False, index=True),
    sa.Column("reason", sa.Text()),
    sa.Column("related_appointment_id", sa.Integer(), sa.ForeignKey("appointments.id")),
    sa.Column("related_invoice_id", sa.Integer(), sa.ForeignKey("invoices.id")),
    sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
)
service_material_templates = sa.Table(
    "service_material_templates", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
    sa.Column("inventory_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id"), nullable=False),
    sa.Column("default_quantity", sa.Numeric(12, 2), nullable=False),
    sa.Column("required", sa.Boolean(), nullable=False),
    sa.Column("variable_quantity_allowed", sa.Boolean(), nullable=False),
    sa.Column("notes", sa.Text()),
    *timestamps(),
)


def upgrade() -> None:
    metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    metadata.drop_all(bind=op.get_bind())
