from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.domain import (
    Appointment,
    InventoryBatch,
    InventoryItem,
    Module,
    Patient,
    Permission,
    Provider,
    Role,
    Room,
    Service,
    ServiceMaterialTemplate,
    StockLocation,
    Supplier,
    User,
)

PERMISSIONS = [
    "patients.read",
    "patients.write",
    "appointments.read",
    "appointments.write",
    "appointments.cancel",
    "services.read",
    "services.write",
    "modules.read",
    "inventory.read",
    "inventory.write",
    "inventory.adjust",
    "inventory.write_off",
    "procurement.read",
    "procurement.write",
    "billing.read",
    "billing.write",
    "billing.mark_paid",
    "audit.read",
    "admin.manage_users",
    "ai.appointments.create",
    "ai.patients.create",
    "ai.free_slots.read",
]

ROLE_PERMISSIONS = {
    "admin": PERMISSIONS,
    "physician": ["patients.read", "patients.write", "appointments.read", "appointments.write", "services.read", "inventory.read", "billing.read"],
    "nurse": ["patients.read", "appointments.read", "appointments.write", "inventory.read", "inventory.write"],
    "receptionist": ["patients.read", "patients.write", "appointments.read", "appointments.write", "services.read", "billing.read"],
    "inventory_manager": ["inventory.read", "inventory.write", "inventory.adjust", "inventory.write_off", "procurement.read", "procurement.write"],
    "billing": ["billing.read", "billing.write", "billing.mark_paid", "patients.read", "appointments.read"],
    "ai_agent": ["ai.appointments.create", "ai.patients.create", "ai.free_slots.read"],
}

MODULE_SEEDS = [
    {"key": "scheduling", "name": "Narucivanje", "description": "Pacijenti, termini i dnevni raspored"},
    {"key": "inventory", "name": "Inventar", "description": "Zalihe, LOT i rokovi trajanja"},
    {"key": "procurement", "name": "Nabava", "description": "Dobavljaci i narudzbenice"},
    {"key": "billing", "name": "Naplata", "description": "Priprema racuna i stavki"},
    {"key": "ai_agents", "name": "AI agenti", "description": "API rute za automatizaciju"},
]

GASTRO_SERVICE_SEEDS = [
    {"name": "Prvi gastroenteroloski pregled", "code": "GASTRO-FIRST-EXAM", "duration": 30, "price": "90.00"},
    {"name": "Kontrolni pregled", "code": "GASTRO-CHECK", "duration": 30, "price": "70.00"},
    {"name": "Ultrazvuk abdomena", "code": "GASTRO-ABDOMEN-US", "duration": 30, "price": "80.00"},
    {"name": "Pregled + ultrazvuk abdomena", "code": "GASTRO-EXAM-ABDOMEN-US", "duration": 45, "price": "140.00"},
    {"name": "Ezofagogastroduodenoskopija", "code": "GASTRO-EGD", "duration": 30, "price": "150.00"},
    {"name": "Ezofagogastroduodenoskopija u analgosedaciji", "code": "GASTRO-EGD-SED", "duration": 45, "price": "220.00"},
    {"name": "Totalna kolonoskopija bez anestezije", "code": "GASTRO-COL-NO-AN", "duration": 45, "price": "260.00"},
    {"name": "Kolonoskopija sa sedacijom", "code": "GASTRO-COL-SED", "duration": 45, "price": "220.00"},
    {"name": "Totalna kolonoskopija - ileoskopija", "code": "GASTRO-COL-ILEO", "duration": 45, "price": "300.00"},
    {"name": "Totalna kolonoskopija - ileoskopija u sedaciji", "code": "GASTRO-COL-ILEO-SED", "duration": 75, "price": "400.00"},
    {"name": "Doppler hemoroidalnih arterija", "code": "GASTRO-HEM-DOPPLER", "duration": 30, "price": "100.00"},
    {"name": "Polipektomija osnovna / do 2 polipa", "code": "GASTRO-POLYPECTOMY-BASIC", "duration": 15, "price": "250.00"},
    {"name": "PH / biopsija, prvi uzorak", "code": "GASTRO-PH-BIOPSY-FIRST", "duration": 30, "price": "130.00"},
    {"name": "H. pylori ureaza test", "code": "GASTRO-HP-UREASE", "duration": 30, "price": "35.00"},
    {"name": "H. pylori antigen test", "code": "GASTRO-HP-ANTIGEN", "duration": 20, "price": "40.00"},
    {"name": "UBT izdisajni test", "code": "GASTRO-UBT", "duration": 120, "price": "85.00"},
    {"name": "Rektoskopija", "code": "GASTRO-RECTOSCOPY", "duration": 30, "price": "100.00"},
    {"name": "Rektosigmoidoskopija", "code": "GASTRO-RECTOSIGMOIDOSCOPY", "duration": 30, "price": "125.00"},
    {"name": "Parcijalna kolonoskopija", "code": "GASTRO-PARTIAL-COL", "duration": 45, "price": "160.00"},
    {"name": "Gastroskopija", "code": "GASTRO-GASTRO", "duration": 30, "price": "120.00"},
    {"name": "HarmonyCa tretman", "code": "AEST-HARMONYCA", "duration": 50, "price": "450.00"},
]


def seed_catalog(db: Session) -> None:
    modules: dict[str, Module] = {}
    for module_seed in MODULE_SEEDS:
        module = db.scalar(select(Module).where(Module.key == module_seed["key"]))
        if module is None:
            module = Module(**module_seed)
            db.add(module)
        else:
            module.name = module_seed["name"]
            module.description = module_seed["description"]
            module.enabled = True
        modules[module_seed["key"]] = module
    db.flush()

    scheduling = modules["scheduling"]
    for service_seed in GASTRO_SERVICE_SEEDS:
        service = db.scalar(select(Service).where(Service.code == service_seed["code"]))
        values = {
            "name": service_seed["name"],
            "duration_minutes": service_seed["duration"],
            "price": Decimal(service_seed["price"]),
            "module_id": scheduling.id,
            "active": True,
        }
        if service is None:
            db.add(Service(code=service_seed["code"], **values))
        else:
            for field, value in values.items():
                setattr(service, field, value)
    db.flush()


def seed(db: Session) -> None:
    if db.scalar(select(User).limit(1)):
        seed_catalog(db)
        db.commit()
        return

    permissions = {name: Permission(name=name, description=name) for name in PERMISSIONS}
    db.add_all(permissions.values())
    db.flush()

    roles = {
        name: Role(name=name, description=name.replace("_", " ").title())
        for name in ROLE_PERMISSIONS
    }
    for role_name, permission_names in ROLE_PERMISSIONS.items():
        roles[role_name].permissions = [permissions[name] for name in permission_names]
    db.add_all(roles.values())
    db.flush()

    admin = User(email="admin@astra.local", full_name="ASTRA Administrator", password_hash=hash_password("astra123"), role_id=roles["admin"].id)
    provider = Provider(full_name="dr. Ana Kovač", specialty="Gastroenterologija")
    room = Room(name="Endoskopska sala 1", type="endoscopy_room")
    db.add_all([admin, provider, room])

    modules = [
        Module(key="scheduling", name="Naručivanje", description="Pacijenti, termini i dnevni raspored"),
        Module(key="inventory", name="Inventar", description="Zalihe, LOT i rokovi trajanja"),
        Module(key="procurement", name="Nabava", description="Dobavljači i narudžbenice"),
        Module(key="billing", name="Naplata", description="Priprema računa i stavki"),
        Module(key="ai_agents", name="AI agenti", description="API rute za automatizaciju"),
    ]
    db.add_all(modules)
    db.flush()
    gastro = modules[0]

    services = [
        Service(name="Kolonoskopija sa sedacijom", code="GASTRO-COL-SED", duration_minutes=45, price=Decimal("220.00"), module_id=gastro.id),
        Service(name="Gastroskopija", code="GASTRO-GASTRO", duration_minutes=30, price=Decimal("120.00"), module_id=gastro.id),
        Service(name="Kontrolni pregled gastroenterologa", code="GASTRO-CHECK", duration_minutes=20, price=Decimal("70.00"), module_id=gastro.id),
        Service(name="HarmonyCa tretman", code="AEST-HARMONYCA", duration_minutes=50, price=Decimal("450.00"), module_id=gastro.id),
    ]
    db.add_all(services)
    db.flush()
    seed_catalog(db)

    patient = Patient(first_name="Ivana", last_name="Horvat", date_of_birth=date(1984, 5, 12), phone="+385 91 234 5678", email="ivana.horvat@example.com")
    db.add(patient)
    db.flush()

    db.add(
        Appointment(
            patient_id=patient.id,
            service_id=services[0].id,
            provider_id=provider.id,
            room_id=room.id,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(9, 45),
            duration_minutes=45,
            status="confirmed",
            source="manual",
            notes="Prvi termin u danu",
            created_by=admin.id,
        )
    )

    supplier = Supplier(name="MedSupply Hrvatska d.o.o.", contact_person="Marko Babić", email="prodaja@medsupply.test", phone="+385 1 555 0101")
    locations = [
        StockLocation(name="Glavno skladište", type="main_storage"),
        StockLocation(name="Endoskopska sala", type="endoscopy_room"),
        StockLocation(name="Estetska ordinacija", type="aesthetic_room"),
    ]
    db.add(supplier)
    db.add_all(locations)
    db.flush()

    item_names = [
        ("PROP", "Propofol", "lijek", "ml"),
        ("IV-CAN", "IV kanila", "potrošni materijal", "kom"),
        ("BIO-FOR", "Biopsijska kliješta", "endoskopija", "kom"),
        ("POL-SNA", "Polipektomijska omča", "endoskopija", "kom"),
        ("GLOVE", "Pregledne rukavice", "potrošni materijal", "kom"),
        ("SYR", "Šprice", "potrošni materijal", "kom"),
        ("NEED", "Igle", "potrošni materijal", "kom"),
        ("DIS", "Dezinficijens", "higijena", "ml"),
        ("HAR", "HarmonyCa", "estetika", "kom"),
        ("SUN", "Sunekos", "estetika", "kom"),
        ("MESO", "Meso-Wharton", "estetika", "kom"),
        ("PLI", "Plinest", "estetika", "kom"),
        ("REJ", "Rejuran", "estetika", "kom"),
        ("PBS", "PB Serum", "estetika", "kom"),
    ]
    items: dict[str, InventoryItem] = {}
    for sku, name, category, unit in item_names:
        item = InventoryItem(
            sku=sku,
            name=name,
            category=category,
            unit_of_measure=unit,
            supplier_id=supplier.id,
            current_stock=Decimal("25"),
            minimum_stock=Decimal("5"),
            reorder_point=Decimal("10"),
            purchase_price=Decimal("3.50"),
            selling_price=Decimal("6.00"),
            expiration_tracking_enabled=True,
            lot_tracking_enabled=True,
        )
        db.add(item)
        items[name] = item
    db.flush()

    for item in items.values():
        db.add(InventoryBatch(inventory_item_id=item.id, lot_number=f"LOT-{item.sku}-001", expiration_date=date.today() + timedelta(days=90), quantity=Decimal("25"), location_id=locations[0].id, purchase_price=item.purchase_price, supplier_id=supplier.id))

    templates = [
        (services[0], "IV kanila", 1, True, False),
        (services[0], "Pregledne rukavice", 2, True, False),
        (services[0], "Propofol", 20, True, True),
        (services[0], "Biopsijska kliješta", 1, False, False),
        (services[0], "Polipektomijska omča", 1, False, False),
        (services[1], "Pregledne rukavice", 2, True, False),
        (services[1], "Biopsijska kliješta", 1, False, False),
        (services[3], "HarmonyCa", 1, True, False),
        (services[3], "IV kanila", 1, True, False),
        (services[3], "Igle", 1, True, False),
        (services[3], "Pregledne rukavice", 2, True, False),
    ]
    for service, item_name, qty, required, variable in templates:
        db.add(ServiceMaterialTemplate(service_id=service.id, inventory_item_id=items[item_name].id, default_quantity=Decimal(qty), required=required, variable_quantity_allowed=variable))

    db.commit()
