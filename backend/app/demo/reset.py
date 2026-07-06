from sqlalchemy import delete, or_, select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.domain import Appointment, ClinicalEpisode, InventoryBatch, InventoryItem, Invoice, InvoiceLine, Patient, PaymentTransaction, PurchaseOrder, PurchaseOrderLine, Provider, Room, Service, ServiceMaterialTemplate, StockMovement, Supplier


def demo_patient_filter():
    return Patient.email.in_(["demo.patient@astra.local", "demo.patient@astra-clinic-core.com"])


def main() -> None:
    settings = get_settings()
    if settings.app_env == "production":
        raise SystemExit("Demo reset is disabled in production.")
    with SessionLocal() as db:
        demo_patients = db.scalars(select(Patient.id).where(demo_patient_filter())).all()
        demo_items = db.scalars(select(InventoryItem.id).where(InventoryItem.sku.like("DEMO-%"))).all()
        demo_services = db.scalars(select(Service.id).where(Service.code.like("DEMO-%"))).all()
        demo_suppliers = db.scalars(select(Supplier.id).where(Supplier.name.like("Demo%"))).all()
        demo_providers = db.scalars(select(Provider.id).where(Provider.full_name.like("dr. Demo%"))).all()
        demo_rooms = db.scalars(select(Room.id).where(Room.name.like("Demo%"))).all()
        appointment_filters = []
        if demo_patients:
            appointment_filters.append(Appointment.patient_id.in_(demo_patients))
        if demo_services:
            appointment_filters.append(Appointment.service_id.in_(demo_services))
        if demo_providers:
            appointment_filters.append(Appointment.provider_id.in_(demo_providers))
        if demo_rooms:
            appointment_filters.append(Appointment.room_id.in_(demo_rooms))
        demo_appointments = db.scalars(select(Appointment.id).where(or_(*appointment_filters)) if appointment_filters else select(Appointment.id).where(False)).all()
        demo_invoices = db.scalars(select(Invoice.id).where(Invoice.appointment_id.in_(demo_appointments)) if demo_appointments else select(Invoice.id).where(False)).all()
        demo_orders = db.scalars(select(PurchaseOrder.id).where(PurchaseOrder.supplier_id.in_(demo_suppliers)) if demo_suppliers else select(PurchaseOrder.id).where(False)).all()

        if demo_invoices:
            db.execute(delete(PaymentTransaction).where(PaymentTransaction.invoice_id.in_(demo_invoices)))
            db.execute(delete(InvoiceLine).where(InvoiceLine.invoice_id.in_(demo_invoices)))
            db.execute(delete(Invoice).where(Invoice.id.in_(demo_invoices)))
        if demo_appointments:
            db.execute(delete(StockMovement).where(StockMovement.related_appointment_id.in_(demo_appointments)))
            db.execute(delete(Appointment).where(Appointment.id.in_(demo_appointments)))
        if demo_orders:
            db.execute(delete(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id.in_(demo_orders)))
            db.execute(delete(PurchaseOrder).where(PurchaseOrder.id.in_(demo_orders)))
        if demo_items:
            db.execute(delete(ServiceMaterialTemplate).where(ServiceMaterialTemplate.inventory_item_id.in_(demo_items)))
            db.execute(delete(InventoryBatch).where(InventoryBatch.inventory_item_id.in_(demo_items)))
            db.execute(delete(InventoryItem).where(InventoryItem.id.in_(demo_items)))
        if demo_services:
            db.execute(delete(ServiceMaterialTemplate).where(ServiceMaterialTemplate.service_id.in_(demo_services)))
            db.execute(delete(Service).where(Service.id.in_(demo_services)))
        if demo_suppliers:
            db.execute(delete(Supplier).where(Supplier.id.in_(demo_suppliers)))
        if demo_patients:
            db.execute(delete(ClinicalEpisode).where(ClinicalEpisode.patient_id.in_(demo_patients)))
        db.execute(delete(Room).where(Room.name.like("Demo%")))
        db.execute(delete(Provider).where(Provider.full_name.like("dr. Demo%")))
        db.execute(delete(Patient).where(demo_patient_filter()))
        db.commit()
    print("Demo data reset complete.")


if __name__ == "__main__":
    main()
