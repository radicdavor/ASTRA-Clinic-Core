from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.domain import (
    Appointment,
    ClinicalFormDefinition,
    ClinicalFormVersion,
    Clinic,
    ClinicMembership,
    InventoryBatch,
    InventoryItem,
    Module,
    Patient,
    PatientClinicAssociation,
    Permission,
    Provider,
    Role,
    Room,
    Service,
    ServiceFormBinding,
    ServicePackage,
    ServicePackageItem,
    ServicePackageVersion,
    ServiceMaterialTemplate,
    StockLocation,
    Supplier,
    User,
    WorkflowTemplate,
)

PERMISSIONS = [
    "patients.read",
    "patients.write",
    "appointments.read",
    "appointments.write",
    "appointments.cancel",
    "episodes.read",
    "episodes.write",
    "clinical_plans.read",
    "clinical_plans.write",
    "clinical_documents.read",
    "clinical_documents.write",
    "clinical_documents.review",
    "services.read",
    "services.write",
    "modules.read",
    "inventory.read",
    "inventory.write",
    "inventory.adjust",
    "inventory.write_off",
    "inventory.transfer",
    "procurement.read",
    "procurement.write",
    "billing.read",
    "billing.write",
    "billing.mark_paid",
    "audit.read",
    "admin.manage_users",
    "system.admin",
    "clinical_readiness.snapshots.read",
    "clinical_readiness.snapshots.write",
    "clinical_readiness.snapshots.supersede",
    "clinical_readiness.acknowledgments.read",
    "clinical_findings.read",
    "clinical_open_questions.read",
    "clinical_evidence_timeline.read",
    "workflow_tasks.read",
    "workflow_tasks.write",
    "workflow_templates.manage",
    "knowledge_protocols.read",
    "knowledge_protocols.write",
    "knowledge_protocols.review",
    "ai.appointments.create",
    "ai.patients.create",
    "ai.free_slots.read",
    "journey.read",
    "journey.create",
    "journey.update_admin",
    "journey.transition",
    "preparation.assign",
    "preparation.review",
    "documents.request",
    "documents.upload",
    "documents.scan",
    "documents.view_source",
    "documents.review",
    "checkin.update",
    "checkin.clinical_review",
    "encounter.read",
    "encounter.write",
    "encounter.complete",
    "consumables.record",
    "payment.record",
    "summary.generate",
    "summary.review",
    "clinical_forms.read",
    "clinical_forms.manage",
    "clinical_forms.sign",
    "service_packages.read",
    "service_packages.schedule",
    "service_packages.manage",
    "activity_preparation.read",
    "activity_preparation.update",
    "activity_preparation.clinical_review",
    "procedure_interventions.read",
    "procedure_interventions.write",
    "pathology_cases.read",
    "pathology_cases.update",
    "pathology_results.receive",
    "pathology_results.review",
    "pathology_communication.decide",
    "reports.read",
    "reports.print",
    "reports.send",
    "reports.send_alternate_recipient",
    "reports.delivery_history",
]

ROLE_PERMISSIONS = {
    "admin": PERMISSIONS,
    "physician": ["patients.read", "patients.write", "appointments.read", "appointments.write", "episodes.read", "episodes.write", "clinical_plans.read", "clinical_plans.write", "clinical_documents.read", "clinical_documents.write", "clinical_documents.review", "services.read", "inventory.read", "billing.read", "clinical_readiness.snapshots.read", "clinical_readiness.snapshots.write", "clinical_readiness.snapshots.supersede", "clinical_readiness.acknowledgments.read", "clinical_findings.read", "clinical_open_questions.read", "clinical_evidence_timeline.read", "workflow_tasks.read", "workflow_tasks.write", "knowledge_protocols.read", "knowledge_protocols.write", "knowledge_protocols.review", "journey.read", "journey.transition", "preparation.assign", "preparation.review", "documents.request", "documents.upload", "documents.view_source", "documents.review", "checkin.clinical_review", "encounter.read", "encounter.write", "encounter.complete", "summary.generate", "summary.review", "clinical_forms.read", "clinical_forms.sign", "activity_preparation.read", "activity_preparation.update", "activity_preparation.clinical_review", "procedure_interventions.read", "procedure_interventions.write", "pathology_cases.read", "pathology_cases.update", "pathology_results.receive", "pathology_results.review", "pathology_communication.decide", "reports.read", "reports.print", "reports.send", "reports.delivery_history"],
    "nurse": ["patients.read", "appointments.read", "appointments.write", "episodes.read", "clinical_plans.read", "clinical_documents.read", "clinical_documents.write", "clinical_documents.review", "inventory.read", "inventory.write", "clinical_readiness.snapshots.read", "workflow_tasks.read", "workflow_tasks.write", "journey.read", "journey.transition", "preparation.assign", "documents.request", "documents.upload", "documents.scan", "documents.view_source", "documents.review", "checkin.update", "encounter.read", "consumables.record", "activity_preparation.read", "activity_preparation.update", "procedure_interventions.read", "pathology_cases.read", "reports.read"],
    "receptionist": ["patients.read", "patients.write", "appointments.read", "appointments.write", "episodes.read", "clinical_plans.read", "clinical_documents.read", "services.read", "billing.read", "workflow_tasks.read", "workflow_tasks.write", "journey.read", "journey.create", "journey.transition", "preparation.assign", "documents.request", "documents.upload", "documents.scan", "documents.view_source", "checkin.update", "service_packages.read", "service_packages.schedule", "activity_preparation.read", "activity_preparation.update"],
    "inventory_manager": ["inventory.read", "inventory.write", "inventory.adjust", "inventory.write_off", "inventory.transfer", "procurement.read", "procurement.write"],
    "billing": ["billing.read", "billing.write", "billing.mark_paid", "patients.read", "appointments.read", "journey.read", "journey.transition", "payment.record"],
    "ai_agent": ["ai.appointments.create", "ai.patients.create", "ai.free_slots.read", "journey.read", "journey.create"],
    "document_reviewer": ["patients.read", "clinical_documents.read", "clinical_documents.review", "journey.read", "documents.view_source", "documents.review", "pathology_cases.read", "pathology_results.receive", "reports.read"],
}

MODULE_SEEDS = [
    {"key": "scheduling", "name": "Narucivanje", "description": "Pacijenti, termini i dnevni raspored"},
    {"key": "inventory", "name": "Inventar", "description": "Zalihe, LOT i rokovi trajanja"},
    {"key": "procurement", "name": "Nabava", "description": "Dobavljaci i narudzbenice"},
    {"key": "billing", "name": "Naplata", "description": "Priprema racuna i stavki"},
    {"key": "ai_agents", "name": "AI agenti", "description": "API rute za automatizaciju"},
    {"key": "workflow", "name": "Radni tokovi", "description": "Zadaci, odgovornost, rokovi i checkliste"},
    {"key": "knowledge", "name": "Klinicka knjižnica", "description": "Izvorno povezani i liječnički pregledani protokoli"},
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
    gastro_clinic = db.scalar(select(Clinic).where(Clinic.name == "Gastroenterologija")) or Clinic(name="Gastroenterologija")
    aesthetic_clinic = db.scalar(select(Clinic).where(Clinic.name == "Estetika")) or Clinic(name="Estetika")
    gastro_clinic.active = True
    aesthetic_clinic.active = True
    db.add_all([gastro_clinic, aesthetic_clinic])
    db.flush()

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

    for room in db.scalars(select(Room)).all():
        if room.clinic_id is None:
            room.clinic_id = aesthetic_clinic.id if "estet" in f"{room.name} {room.type}".lower() else gastro_clinic.id
    for provider in db.scalars(select(Provider)).all():
        provider.staff_role = provider.staff_role or "physician"
        if provider.clinic_id is None:
            provider.clinic_id = gastro_clinic.id
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


def seed_clinical_forms(db: Session) -> None:
    approver = db.scalar(select(User).join(Role).where(Role.name == "admin").limit(1))
    published_at = datetime.now(timezone.utc)
    def fields(keys, *, required=()):
        labels = {key: key.replace("_", " ").capitalize() for key in keys}
        list_types = {"diagnoses": "diagnosis_list", "therapy": "medication_list", "interventions": "procedure_intervention_list", "biopsy_specimens": "specimen_list", "polypectomies": "procedure_intervention_list", "anatomical_regions": "anatomical_site"}
        return [{"field_key": key, "label": labels[key], "type": list_types.get(key, "long_text"), "required": key in required, "help_text": None, "default": None, "options": [], "visibility_condition": None, "validation": {}, "print_behavior": "when_present"} for key in keys]

    consultation = ["reason_for_visit", "anamnesis", "examination_status", "opinion_and_recommendations", "diagnoses", "therapy", "follow_up"]
    catalogs = [
        ("generic-specialist-consultation", "Specijalistički pregled", "general", "specialist_consultation", consultation, {"reason_for_visit", "anamnesis", "opinion_and_recommendations"}),
        ("gastroenterology-consultation", "Gastroenterološki pregled", "gastroenterology", "specialist_consultation", consultation, {"reason_for_visit", "anamnesis", "opinion_and_recommendations"}),
        ("gynecology-consultation", "Ginekološki pregled", "gynecology", "specialist_consultation", consultation, {"reason_for_visit", "anamnesis", "opinion_and_recommendations"}),
        ("aesthetic-consultation", "Estetski pregled", "aesthetic", "specialist_consultation", ["anamnesis", "examination", "opinion", "proposed_plan", "contraindications_review", "patient_information_given"], {"anamnesis", "opinion"}),
        ("gastroscopy-report", "Gastroskopija", "gastroenterology", "gastroscopy", ["indication", "preparation", "sedation", "instrument", "extent_of_examination", "esophagus_findings", "stomach_findings", "duodenum_findings", "overall_findings", "interventions", "biopsy_specimens", "complications", "diagnoses", "recommendations", "follow_up"], {"indication", "extent_of_examination", "overall_findings", "complications", "recommendations"}),
        ("colonoscopy-report", "Kolonoskopija", "gastroenterology", "colonoscopy", ["indication", "bowel_preparation_quality", "sedation", "instrument", "extent_of_examination", "terminal_ileum", "segment_findings", "overall_findings", "polyps", "interventions", "biopsy_specimens", "polypectomies", "clips", "withdrawal_time", "complications", "diagnoses", "recommendations", "follow_up"], {"indication", "bowel_preparation_quality", "extent_of_examination", "overall_findings", "complications", "recommendations"}),
        ("harmonyca-treatment", "HarmonyCa tretman", "aesthetic", "harmonyca_treatment", ["treatment_indication", "product_name", "quantity", "unit", "lot_number", "expiration_date", "anatomical_regions", "technique", "local_anesthesia", "immediate_tolerance", "complications", "findings", "aftercare_instructions", "clinician_signature"], {"treatment_indication", "product_name", "quantity", "unit", "lot_number", "anatomical_regions", "immediate_tolerance", "complications", "aftercare_instructions"}),
    ]
    versions = {}
    for form_key, name, specialty, kind, keys, required in catalogs:
        definition = db.scalar(select(ClinicalFormDefinition).where(ClinicalFormDefinition.form_key == form_key))
        if not definition:
            definition = ClinicalFormDefinition(form_key=form_key, name=name, specialty_key=specialty, activity_kind=kind, description=f"Kontrolirani klinički obrazac: {name}", active=True)
            db.add(definition); db.flush()
        version = db.scalar(select(ClinicalFormVersion).where(ClinicalFormVersion.definition_id == definition.id, ClinicalFormVersion.version == 1))
        if not version:
            version = ClinicalFormVersion(definition_id=definition.id, version=1, status="published", sections_json=[{"section_key": "clinical", "title": name, "fields": fields(keys, required=required)}], validation_schema_json={}, print_layout_json={"layout": "clinical_report"}, output_document_type="clinical_report", approved_by=approver.id if approver else None, approved_at=published_at, published_at=published_at)
            db.add(version); db.flush()
        versions[form_key] = version

    defaults = [
        (None, None, "general", "specialist_consultation", "generic-specialist-consultation"),
        (None, None, "gastroenterology", "specialist_consultation", "gastroenterology-consultation"),
        (None, None, "gynecology", "specialist_consultation", "gynecology-consultation"),
        (None, None, "aesthetic", "specialist_consultation", "aesthetic-consultation"),
        (None, None, "gastroenterology", "gastroscopy", "gastroscopy-report"),
        (None, None, "gastroenterology", "colonoscopy", "colonoscopy-report"),
        (None, None, "aesthetic", "harmonyca_treatment", "harmonyca-treatment"),
    ]
    for service_id, clinic_id, specialty, kind, form_key in defaults:
        existing = db.scalar(select(ServiceFormBinding).where(ServiceFormBinding.service_id.is_(None), ServiceFormBinding.clinic_id.is_(None), ServiceFormBinding.specialty_key == specialty, ServiceFormBinding.activity_kind == kind))
        if not existing:
            db.add(ServiceFormBinding(service_id=service_id, clinic_id=clinic_id, specialty_key=specialty, activity_kind=kind, form_version_id=versions[form_key].id, active=True))

    service_forms = {
        "GASTRO-FIRST-EXAM": "gastroenterology-consultation", "GASTRO-CHECK": "gastroenterology-consultation",
        "GASTRO-EGD": "gastroscopy-report", "GASTRO-EGD-SED": "gastroscopy-report", "GASTRO-GASTRO": "gastroscopy-report",
        "GASTRO-COL-NO-AN": "colonoscopy-report", "GASTRO-COL-SED": "colonoscopy-report", "GASTRO-COL-ILEO": "colonoscopy-report", "GASTRO-COL-ILEO-SED": "colonoscopy-report",
        "AEST-HARMONYCA": "harmonyca-treatment",
    }
    for code, form_key in service_forms.items():
        service = db.scalar(select(Service).where(Service.code == code))
        if service and not db.scalar(select(ServiceFormBinding).where(ServiceFormBinding.service_id == service.id, ServiceFormBinding.clinic_id.is_(None))):
            db.add(ServiceFormBinding(service_id=service.id, form_version_id=versions[form_key].id, active=True))

    structured_catalog = {
        "gastroscopy-report": [
            *fields(["indication", "preparation", "sedation", "instrument", "extent_of_examination", "esophagus_findings", "stomach_findings", "duodenum_findings", "overall_findings"], required={"indication", "extent_of_examination", "overall_findings"}),
            {"field_key": "biopsies", "label": "Biopsije", "type": "structured_biopsy_list", "required": False, "item_fields": [{"field_key": "site", "label": "Mjesto", "type": "short_text", "required": True}, {"field_key": "description", "label": "Opis", "type": "short_text", "required": True}, {"field_key": "specimen_label", "label": "Oznaka uzorka", "type": "short_text", "required": True}], "max_items": 20},
            {"field_key": "interventions", "label": "Intervencije", "type": "structured_intervention_list", "required": False, "item_fields": [{"field_key": "type", "label": "Vrsta", "type": "select", "required": True, "options": ["biopsy", "clip_placement", "hemostasis", "other"]}, {"field_key": "site", "label": "Mjesto", "type": "short_text", "required": True}, {"field_key": "technique", "label": "Tehnika", "type": "short_text"}], "max_items": 20},
            *fields(["complications", "diagnoses", "recommendations", "follow_up"], required={"complications", "recommendations"}),
        ],
        "colonoscopy-report": [
            *fields(["indication", "bowel_preparation_quality", "sedation", "instrument", "extent_of_examination", "terminal_ileum"], required={"indication", "bowel_preparation_quality", "extent_of_examination"}),
            {"field_key": "segment_findings", "label": "Nalazi po segmentima", "type": "structured_segment_findings", "required": True, "item_fields": [{"field_key": "segment", "label": "Segment", "type": "select", "required": True, "options": ["rektum", "sigmoidni kolon", "descendentni kolon", "transverzum", "ascendentni kolon", "cekum", "terminalni ileum"]}, {"field_key": "finding", "label": "Nalaz", "type": "short_text", "required": True}], "max_items": 20},
            {"field_key": "polyps", "label": "Polipi", "type": "structured_polyp_list", "required": False, "item_fields": [{"field_key": "site", "label": "Mjesto", "type": "short_text", "required": True}, {"field_key": "size_mm", "label": "Veličina mm", "type": "decimal", "required": True}, {"field_key": "morphology", "label": "Morfologija", "type": "short_text"}, {"field_key": "removal", "label": "Postupak", "type": "select", "required": True, "options": ["biopsija", "hladna omča", "vruća omča", "nije uklonjen"]}, {"field_key": "retrieved", "label": "Dohvaćen", "type": "select", "required": True, "options": ["da", "ne"]}, {"field_key": "specimen_label", "label": "Oznaka uzorka", "type": "short_text"}], "max_items": 30},
            {"field_key": "clips", "label": "Klipovi", "type": "repeatable_group", "required": False, "item_fields": [{"field_key": "site", "label": "Mjesto", "type": "short_text", "required": True}, {"field_key": "count", "label": "Broj", "type": "integer", "required": True}, {"field_key": "reason", "label": "Razlog", "type": "short_text", "required": True}], "max_items": 20},
            *fields(["overall_findings", "withdrawal_time", "complications", "diagnoses", "recommendations", "follow_up"], required={"overall_findings", "withdrawal_time", "complications", "recommendations"}),
        ],
    }
    for form_key, structured_fields in structured_catalog.items():
        definition = db.scalar(select(ClinicalFormDefinition).where(ClinicalFormDefinition.form_key == form_key))
        version = db.scalar(select(ClinicalFormVersion).where(ClinicalFormVersion.definition_id == definition.id, ClinicalFormVersion.version == 2))
        if not version:
            version = ClinicalFormVersion(definition_id=definition.id, version=2, status="published", sections_json=[{"section_key": "clinical", "title": definition.name, "fields": structured_fields}], validation_schema_json={"structured": True}, print_layout_json={"layout": "clinical_report"}, output_document_type="gastroscopy_report" if form_key == "gastroscopy-report" else "colonoscopy_report", approved_by=approver.id if approver else None, approved_at=published_at, published_at=published_at, supersedes_version_id=versions[form_key].id)
            db.add(version); db.flush()
        versions[form_key] = version
    for binding in db.scalars(select(ServiceFormBinding).where(ServiceFormBinding.active.is_(True))).all():
        form_key = binding.form_version.definition.form_key
        if form_key in structured_catalog and binding.form_version_id != versions[form_key].id:
            binding.active = False
            db.add(ServiceFormBinding(service_id=binding.service_id, clinic_id=binding.clinic_id, specialty_key=binding.specialty_key, activity_kind=binding.activity_kind, form_version_id=versions[form_key].id, active=True))
    db.flush()


def seed_gastro_package(db: Session) -> None:
    package = db.scalar(select(ServicePackage).where(ServicePackage.package_key == "gastro-consult-gastroscopy-colonoscopy"))
    if not package:
        package = ServicePackage(package_key="gastro-consult-gastroscopy-colonoscopy", name="Gastro pregled + gastroskopija + kolonoskopija", description="Jedan dolazak s tri odvojene kliničke aktivnosti.", specialty_key="gastroenterology", active=True)
        db.add(package); db.flush()
    version = db.scalar(select(ServicePackageVersion).where(ServicePackageVersion.package_id == package.id, ServicePackageVersion.version == 1))
    if not version:
        version = ServicePackageVersion(package_id=package.id, version=1, status="published", published_at=datetime.now(timezone.utc))
        db.add(version); db.flush()
    if not db.scalar(select(ServicePackageItem.id).where(ServicePackageItem.package_version_id == version.id).limit(1)):
        services = {service.code: service for service in db.scalars(select(Service).where(Service.code.in_(["GASTRO-FIRST-EXAM", "GASTRO-GASTRO", "GASTRO-COL-SED"]))).all()}
        specifications = [
            ("consultation", "GASTRO-FIRST-EXAM", "specialist_consultation", 1, 0, 30, [{"requirement_key": "medication_review", "label": "Pregled terapije", "patient_instruction": "Ponijeti popis aktualne terapije.", "category": "medication_review"}]),
            ("gastroscopy", "GASTRO-GASTRO", "gastroscopy", 2, 40, 30, [{"requirement_key": "fasting", "label": "Natašte", "patient_instruction": "Slijediti odobrene upute klinike za dolazak natašte.", "category": "fasting"}]),
            ("colonoscopy", "GASTRO-COL-SED", "colonoscopy", 3, 80, 45, [{"requirement_key": "bowel_preparation", "label": "Priprema crijeva", "patient_instruction": "Slijediti odobreni plan pripreme crijeva.", "category": "bowel_preparation"}, {"requirement_key": "escort", "label": "Pratnja", "patient_instruction": "Osigurati pratnju nakon sedacije.", "category": "escort"}]),
        ]
        for key, code, kind, sequence, offset, duration, preparation in specifications:
            service = services.get(code)
            if service:
                db.add(ServicePackageItem(package_version_id=version.id, service_id=service.id, activity_key=key, activity_kind=kind, specialty_key="gastroenterology", sequence=sequence, required=True, relative_start_offset_minutes=offset, default_duration_minutes=duration, preparation_requirements_json=preparation, billing_inclusion_rule="include"))
    db.flush()


def seed_security(db: Session) -> None:
    permissions = {permission.name: permission for permission in db.scalars(select(Permission)).all()}
    for name in PERMISSIONS:
        if name not in permissions:
            permission = Permission(name=name, description=name)
            db.add(permission)
            permissions[name] = permission
    db.flush()

    roles = {role.name: role for role in db.scalars(select(Role)).all()}
    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = roles.get(role_name)
        if role is None:
            role = Role(name=role_name, description=role_name.replace("_", " ").title())
            db.add(role)
            roles[role_name] = role
        role.permissions = [permissions[name] for name in permission_names]
    db.flush()


def seed_demo_memberships(db: Session) -> None:
    clinics = db.scalars(select(Clinic)).all()
    if not clinics:
        return
    admins = db.scalars(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where((Role.name == "admin") | (Role.name.like("demo_%")))
    ).all()
    for admin in admins:
        for clinic in clinics:
            membership = db.scalar(
                select(ClinicMembership).where(
                    ClinicMembership.user_id == admin.id,
                    ClinicMembership.clinic_id == clinic.id,
                )
            )
            if membership is None:
                db.add(ClinicMembership(user_id=admin.id, clinic_id=clinic.id, active=True, created_by_user_id=admin.id))
            else:
                membership.active = True
    db.flush()


def seed(db: Session) -> None:
    if db.scalar(select(User).limit(1)):
        seed_security(db)
        seed_catalog(db)
        seed_demo_memberships(db)
        seed_clinical_forms(db)
        seed_gastro_package(db)
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

    gastro_clinic = db.scalar(select(Clinic).where(Clinic.name == "Gastroenterologija")) or Clinic(name="Gastroenterologija")
    aesthetic_clinic = db.scalar(select(Clinic).where(Clinic.name == "Estetika")) or Clinic(name="Estetika")
    db.add_all([gastro_clinic, aesthetic_clinic])
    db.flush()

    for room in db.scalars(select(Room)).all():
        if not room.allowed_services:
            prefix = "AEST-%" if room.clinic_id == aesthetic_clinic.id else "GASTRO-%"
            room.allowed_services = list(db.scalars(select(Service).where(Service.active.is_(True), Service.code.like(prefix))).all())
    workflow_templates = [
        {"key": "review-result", "name": "Pregled nalaza", "description": "Sigurna operativna checklista za pregled pristiglog nalaza.", "default_priority": "important", "checklist_items": ["Provjeri identitet pacijenta", "Otvori izvorni dokument", "Evidentiraj da je nalaz pregledan", "Odredi sljedeci ljudski korak"]},
        {"key": "prepare-appointment", "name": "Priprema termina", "description": "Priprema tima i prostora prije dolaska pacijenta.", "default_priority": "routine", "checklist_items": ["Provjeri termin i uslugu", "Provjeri prostoriju", "Provjeri potrebne materijale"]},
        {"key": "follow-up", "name": "Organiziraj kontrolu", "description": "Operativna organizacija kontrole bez automatske klinicke odluke.", "default_priority": "routine", "checklist_items": ["Provjeri lijecnicku uputu", "Kontaktiraj pacijenta", "Evidentiraj dogovoreni termin"]},
    ]
    for values in workflow_templates:
        template = db.scalar(select(WorkflowTemplate).where(WorkflowTemplate.key == values["key"]))
        if template is None:
            db.add(WorkflowTemplate(**values))
        else:
            for field, value in values.items():
                setattr(template, field, value)
            template.active = True
    db.flush()
    admin = User(email="admin@astra.local", full_name="ASTRA Administrator", password_hash=hash_password("astra123"), role_id=roles["admin"].id)
    provider = Provider(full_name="dr. Ana Kovač", specialty="Gastroenterologija", clinic_id=gastro_clinic.id)
    room = Room(name="Endoskopska sala 1", type="endoscopy_room", clinic_id=gastro_clinic.id)
    db.add_all([admin, provider, room])
    db.flush()
    db.add_all(
        [
            ClinicMembership(user_id=admin.id, clinic_id=gastro_clinic.id, active=True, created_by_user_id=admin.id),
            ClinicMembership(user_id=admin.id, clinic_id=aesthetic_clinic.id, active=True, created_by_user_id=admin.id),
        ]
    )

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
    room.allowed_services = services
    seed_catalog(db)
    seed_clinical_forms(db)
    seed_gastro_package(db)

    patient = Patient(first_name="Ivana", last_name="Horvat", date_of_birth=date(1984, 5, 12), phone="+385 91 234 5678", email="ivana.horvat@example.com")
    db.add(patient)
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=gastro_clinic.id, active=True, created_by_user_id=admin.id))

    db.add(
        Appointment(
            patient_id=patient.id,
            service_id=services[0].id,
            provider_id=provider.id,
            room_id=room.id,
            clinic_id=gastro_clinic.id,
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
