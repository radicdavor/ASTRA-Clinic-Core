from datetime import date, time
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.domain import (
    Appointment,
    InventoryBatch,
    InventoryItem,
    Patient,
    Permission,
    Provider,
    PurchaseOrder,
    PurchaseOrderLine,
    Role,
    Room,
    Service,
    ServiceMaterialTemplate,
    StockLocation,
    Supplier,
    User,
)
from app.services.seed import PERMISSIONS, ROLE_PERMISSIONS


DEMO_EMAILS = {
    "admin": "demo.admin@astra.local",
    "physician": "demo.physician@astra.local",
    "receptionist": "demo.reception@astra.local",
    "inventory_manager": "demo.inventory@astra.local",
}

DEMO_PATIENT_EMAIL = "demo.patient@astra-clinic-core.com"
LEGACY_DEMO_PATIENT_EMAIL = "demo.patient@astra.local"


def ensure_permissions(db):
    existing = {permission.name: permission for permission in db.scalars(select(Permission)).all()}
    for name in PERMISSIONS:
        existing.setdefault(name, Permission(name=name, description=name))
        db.add(existing[name])
    db.flush()
    return existing


def ensure_demo_user(db, role_name: str, email: str, permissions_by_name):
    role = db.scalar(select(Role).where(Role.name == f"demo_{role_name}"))
    if role is None:
        role = Role(name=f"demo_{role_name}", description=f"Demo {role_name}")
        db.add(role)
    role.permissions = [permissions_by_name[name] for name in ROLE_PERMISSIONS[role_name] if name in permissions_by_name]
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, full_name=f"Demo {role_name.title()}", password_hash=hash_password("demo123"), role=role)
        db.add(user)
    user.role = role
    user.active = True
    return user


def main() -> None:
    with SessionLocal() as db:
        permissions = ensure_permissions(db)
        for role_name, email in DEMO_EMAILS.items():
            ensure_demo_user(db, role_name, email, permissions)

        patient = db.scalar(select(Patient).where(Patient.email.in_([DEMO_PATIENT_EMAIL, LEGACY_DEMO_PATIENT_EMAIL]))) or Patient(first_name="Demo", last_name="Pacijent", email=DEMO_PATIENT_EMAIL)
        patient.email = DEMO_PATIENT_EMAIL
        provider = db.scalar(select(Provider).where(Provider.full_name == "dr. Demo Gastro")) or Provider(full_name="dr. Demo Gastro", specialty="Gastroenterologija")
        room = db.scalar(select(Room).where(Room.name == "Demo ordinacija 1")) or Room(name="Demo ordinacija 1", type="ordinacija")
        service = db.scalar(select(Service).where(Service.code == "DEMO-GASTRO")) or Service(name="Demo gastroskopija", code="DEMO-GASTRO", duration_minutes=30, price=Decimal("120"))
        location = db.scalar(select(StockLocation).where(StockLocation.name == "Demo skladiste")) or StockLocation(name="Demo skladiste", type="main")
        item = db.scalar(select(InventoryItem).where(InventoryItem.sku == "DEMO-MAT")) or InventoryItem(sku="DEMO-MAT", name="Demo potrosni materijal", current_stock=Decimal("0"), minimum_stock=Decimal("2"), reorder_point=Decimal("2"), purchase_price=Decimal("5"))
        supplier = db.scalar(select(Supplier).where(Supplier.name == "Demo dobavljac")) or Supplier(name="Demo dobavljac")
        db.add_all([patient, provider, room, service, location, item, supplier])
        db.flush()

        if db.scalar(select(InventoryBatch).where(InventoryBatch.inventory_item_id == item.id)) is None:
            db.add(InventoryBatch(inventory_item_id=item.id, quantity=Decimal("10"), location_id=location.id, purchase_price=Decimal("5")))
            item.current_stock = Decimal("10")

        template = db.scalar(select(ServiceMaterialTemplate).where(ServiceMaterialTemplate.service_id == service.id, ServiceMaterialTemplate.inventory_item_id == item.id))
        if template is None:
            db.add(ServiceMaterialTemplate(service_id=service.id, inventory_item_id=item.id, default_quantity=Decimal("1"), required=True, variable_quantity_allowed=False))

        if db.scalar(select(Appointment).where(Appointment.patient_id == patient.id, Appointment.date == date.today())) is None:
            db.add(Appointment(patient_id=patient.id, provider_id=provider.id, room_id=room.id, service_id=service.id, date=date.today(), start_time=time(9, 0), end_time=time(9, 30), duration_minutes=30, status="scheduled", source="manual"))

        order = db.scalar(select(PurchaseOrder).where(PurchaseOrder.supplier_id == supplier.id, PurchaseOrder.notes == "DEMO_DATA"))
        if order is None:
            order = PurchaseOrder(supplier_id=supplier.id, status="ordered", notes="DEMO_DATA")
            db.add(order)
            db.flush()
            db.add(PurchaseOrderLine(purchase_order_id=order.id, inventory_item_id=item.id, quantity_ordered=Decimal("5"), unit_price=Decimal("5")))

        db.commit()
    print("Demo data seeded. Login: demo.admin@astra.local / demo123")


if __name__ == "__main__":
    main()
