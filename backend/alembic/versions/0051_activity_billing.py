"""Activity provenance for consumables and coordinated visit billing.

Revision ID: 0051_activity_billing
Revises: 0050_signed_reports
"""
from alembic import op
import sqlalchemy as sa

revision = "0051_activity_billing"
down_revision = "0050_signed_reports"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stock_movements", sa.Column("related_activity_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_stock_movements_activity", "stock_movements", "journey_activities", ["related_activity_id"], ["id"])
    op.create_index("ix_stock_movements_related_activity_id", "stock_movements", ["related_activity_id"])
    op.add_column("invoices", sa.Column("journey_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_invoices_journey", "invoices", "patient_journeys", ["journey_id"], ["id"])
    op.create_index("ix_invoices_journey_id", "invoices", ["journey_id"], unique=True)
    op.add_column("invoice_lines", sa.Column("activity_id", sa.Integer(), nullable=True))
    op.add_column("invoice_lines", sa.Column("source_key", sa.String(160), nullable=True))
    op.create_foreign_key("fk_invoice_lines_activity", "invoice_lines", "journey_activities", ["activity_id"], ["id"])
    op.create_index("ix_invoice_lines_activity_id", "invoice_lines", ["activity_id"])
    op.create_index("ix_invoice_lines_source_key", "invoice_lines", ["source_key"], unique=True)
    op.execute("""
        UPDATE invoices i SET journey_id = j.id
        FROM patient_journeys j WHERE j.appointment_id = i.appointment_id AND i.journey_id IS NULL
    """)
    op.execute("""
        UPDATE invoice_lines il SET activity_id = a.id, source_key = concat('activity', chr(58), a.id, chr(58), 'service')
        FROM invoices i JOIN journey_activities a ON a.appointment_id = i.appointment_id
        WHERE il.invoice_id = i.id AND il.service_id = a.service_id AND il.activity_id IS NULL
    """)
    op.execute("""
        UPDATE stock_movements sm SET related_activity_id = a.id
        FROM journey_activities a
        WHERE sm.related_appointment_id = a.appointment_id AND sm.related_activity_id IS NULL
    """)


def downgrade():
    op.drop_index("ix_invoice_lines_source_key", table_name="invoice_lines")
    op.drop_index("ix_invoice_lines_activity_id", table_name="invoice_lines")
    op.drop_constraint("fk_invoice_lines_activity", "invoice_lines", type_="foreignkey")
    op.drop_column("invoice_lines", "source_key")
    op.drop_column("invoice_lines", "activity_id")
    op.drop_index("ix_invoices_journey_id", table_name="invoices")
    op.drop_constraint("fk_invoices_journey", "invoices", type_="foreignkey")
    op.drop_column("invoices", "journey_id")
    op.drop_index("ix_stock_movements_related_activity_id", table_name="stock_movements")
    op.drop_constraint("fk_stock_movements_activity", "stock_movements", type_="foreignkey")
    op.drop_column("stock_movements", "related_activity_id")
