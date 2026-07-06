from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.domain import (
    Appointment,
    ClinicalEpisode,
    ClinicalPlan,
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

        gerb_episode = db.scalar(select(ClinicalEpisode).where(ClinicalEpisode.patient_id == patient.id, ClinicalEpisode.title == "GERB/refluks pracenje"))
        if gerb_episode is None:
            gerb_episode = ClinicalEpisode(
                patient_id=patient.id,
                title="GERB/refluks pracenje",
                episode_type="gastroenterology",
                status="active",
                priority="routine",
                start_date=date.today(),
                summary="Demo epizoda za pracenje refluksa i kontrolu simptoma.",
                clinical_notes="Demo podaci, ne unositi stvarne medicinske podatke.",
                owner_provider_id=provider.id,
            )
            db.add(gerb_episode)
            db.flush()
        demo_plan_values = {
            "source": "physician",
            "status": "active",
            "proposed_episode_status": "waiting",
            "next_action": "wait_for_pathology",
            "due_date": date.today() + timedelta(days=14),
            "priority": "important",
            "rationale": "Demo aktivni plan: cekati patologiju i zatim odrediti daljnji interval pracenja.",
            "suggested_follow_up": "Pregledati patologiju nakon dolaska nalaza.",
            "physician_conclusion": "Demo zakljucak: kontrolirati PH nalaz i nastaviti pracenje refluksa.",
            "physician_confirmed": True,
        }
        demo_plan = db.scalar(select(ClinicalPlan).where(ClinicalPlan.episode_id == gerb_episode.id, ClinicalPlan.status == "active"))
        if demo_plan is None:
            db.add(ClinicalPlan(episode_id=gerb_episode.id, **demo_plan_values))
        else:
            for field, value in demo_plan_values.items():
                setattr(demo_plan, field, value)
        if db.scalar(select(ClinicalEpisode).where(ClinicalEpisode.patient_id == patient.id, ClinicalEpisode.title == "Nadzor polipa debelog crijeva")) is None:
            db.add(ClinicalEpisode(patient_id=patient.id, title="Nadzor polipa debelog crijeva", episode_type="endoscopy", status="open", priority="routine", start_date=date.today(), summary="Demo epizoda za kontrolu nakon polipektomije.", owner_provider_id=provider.id))
        if db.scalar(select(ClinicalEpisode).where(ClinicalEpisode.patient_id == patient.id, ClinicalEpisode.title == "Estetski tretman plan")) is None:
            db.add(ClinicalEpisode(patient_id=patient.id, title="Estetski tretman plan", episode_type="dermatology_aesthetics", status="open", priority="routine", start_date=date.today(), summary="Demo epizoda za planiranje estetskog tretmana.", owner_provider_id=provider.id))

        if db.scalar(select(Appointment).where(Appointment.patient_id == patient.id, Appointment.date == date.today())) is None:
            db.add(Appointment(patient_id=patient.id, provider_id=provider.id, room_id=room.id, service_id=service.id, episode_id=gerb_episode.id, date=date.today(), start_time=time(9, 0), end_time=time(9, 30), duration_minutes=30, status="scheduled", source="manual"))

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
