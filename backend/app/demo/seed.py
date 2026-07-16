from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.domain import (
    Appointment,
    Clinic,
    ClinicalDocument,
    ClinicalEpisode,
    ClinicalPlan,
    InventoryBatch,
    InventoryItem,
    JourneyActivity,
    Patient,
    PatientJourney,
    PatientClinicalSummaryRecord,
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
    "nurse": "demo.nurse@astra.local",
    "billing": "demo.billing@astra.local",
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

        gastro_clinic = db.scalar(select(Clinic).where(Clinic.name == "Gastroenterologija")) or Clinic(name="Gastroenterologija")
        aesthetic_clinic = db.scalar(select(Clinic).where(Clinic.name == "Estetika")) or Clinic(name="Estetika")
        db.add_all([gastro_clinic, aesthetic_clinic])
        db.flush()
        patient = db.scalar(select(Patient).where(Patient.email.in_([DEMO_PATIENT_EMAIL, LEGACY_DEMO_PATIENT_EMAIL]))) or Patient(first_name="Demo", last_name="Pacijent", email=DEMO_PATIENT_EMAIL)
        patient.email = DEMO_PATIENT_EMAIL
        provider = db.scalar(select(Provider).where(Provider.full_name == "dr. Demo Gastro")) or Provider(full_name="dr. Demo Gastro", specialty="Gastroenterologija")
        provider.clinic_id = provider.clinic_id or gastro_clinic.id
        provider.email = DEMO_EMAILS["physician"]
        provider.staff_role = provider.staff_role or "physician"
        room = db.scalar(select(Room).where(Room.name == "Demo ordinacija 1")) or Room(name="Demo ordinacija 1", type="ordinacija")
        room.clinic_id = room.clinic_id or gastro_clinic.id
        service = db.scalar(select(Service).where(Service.code == "DEMO-GASTRO")) or Service(name="Demo gastroskopija", code="DEMO-GASTRO", duration_minutes=30, price=Decimal("120"))
        location = db.scalar(select(StockLocation).where(StockLocation.name == "Demo skladiste")) or StockLocation(name="Demo skladiste", type="main")
        item = db.scalar(select(InventoryItem).where(InventoryItem.sku == "DEMO-MAT")) or InventoryItem(sku="DEMO-MAT", name="Demo potrosni materijal", current_stock=Decimal("0"), minimum_stock=Decimal("2"), reorder_point=Decimal("2"), purchase_price=Decimal("5"))
        supplier = db.scalar(select(Supplier).where(Supplier.name == "Demo dobavljac")) or Supplier(name="Demo dobavljac")
        db.add_all([patient, provider, room, service, location, item, supplier])
        db.flush()
        if service not in room.allowed_services:
            room.allowed_services.append(service)

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

        journey_variants = [
            ("web", "booked", "requested", "assigned", "not_arrived", "not_started", "not_ready", "not_ready", "not_due"),
            ("ai_secretary", "awaiting_documents", "partial", "acknowledged", "not_arrived", "not_started", "not_ready", "not_ready", "not_due"),
            ("manual", "preparation_in_progress", "complete", "in_progress", "not_arrived", "not_started", "not_ready", "not_ready", "not_due"),
            ("web", "ready_for_arrival", "complete", "complete", "not_arrived", "not_started", "not_ready", "not_ready", "not_due"),
            ("manual", "arrived", "complete", "complete", "arrived", "not_started", "not_ready", "not_ready", "not_due"),
            ("ai_secretary", "check_in_review", "review_required", "complete", "in_review", "not_started", "not_ready", "not_ready", "not_due"),
            ("manual", "ready_for_clinician", "complete", "complete", "ready", "not_started", "not_ready", "not_ready", "not_due"),
            ("web", "in_encounter", "complete", "complete", "ready", "in_progress", "not_ready", "not_ready", "not_due"),
            ("manual", "procedure_completed", "complete", "complete", "ready", "completed", "pending", "not_ready", "not_due"),
            ("ai_secretary", "awaiting_billing", "complete", "complete", "ready", "completed", "confirmed", "ready", "not_due"),
            ("manual", "awaiting_payment", "complete", "complete", "ready", "completed", "not_applicable", "invoice_created", "unpaid"),
            ("web", "cancelled", "requested", "assigned", "not_arrived", "aborted", "not_applicable", "closed", "cancelled"),
        ]
        for index, variant in enumerate(journey_variants, start=1):
            email = f"synthetic.journey.{index:02d}@example.invalid"
            synthetic = db.scalar(select(Patient).where(Patient.email == email))
            if synthetic is None:
                synthetic = Patient(first_name=f"Sintetički {index:02d}", last_name="Pacijent", email=email)
                db.add(synthetic); db.flush()
            appointment = db.scalar(select(Appointment).where(Appointment.patient_id == synthetic.id, Appointment.date == date.today()))
            if appointment is None:
                start = time(7 + index // 2, 30 if index % 2 else 0)
                end_dt = datetime.combine(date.today(), start) + timedelta(minutes=30)
                appointment = Appointment(patient_id=synthetic.id, provider_id=provider.id, room_id=room.id, service_id=service.id, date=date.today(), start_time=start, end_time=end_dt.time(), duration_minutes=30, status="cancelled" if variant[1] == "cancelled" else "scheduled", source=variant[0])
                db.add(appointment); db.flush()
            journey = db.scalar(select(PatientJourney).where(PatientJourney.appointment_id == appointment.id))
            if journey is None:
                journey = PatientJourney(patient_id=synthetic.id, appointment_id=appointment.id, intake_channel=variant[0])
                db.add(journey)
            journey.current_stage, journey.document_status, journey.preparation_status, journey.check_in_status, journey.encounter_status, journey.consumables_status, journey.billing_status, journey.payment_status = variant[1:]
            journey.closed_at = datetime.now(timezone.utc) if variant[1] == "cancelled" else None

        multi_patient_email = "synthetic.multi.gastro@example.invalid"
        multi_patient = db.scalar(select(Patient).where(Patient.email == multi_patient_email))
        if multi_patient is None:
            multi_patient = Patient(first_name="Sintetički", last_name="Višestruki dolazak", email=multi_patient_email)
            db.add(multi_patient)
            db.flush()

        consultation_service = db.scalar(select(Service).where(Service.code == "GASTRO-FIRST-EXAM"))
        gastroscopy_service = db.scalar(select(Service).where(Service.code == "GASTRO-GASTRO"))
        endoscopy_room = db.scalar(select(Room).where(Room.name == "Demo endoskopija 1"))
        if endoscopy_room is None:
            endoscopy_room = Room(name="Demo endoskopija 1", type="endoskopija", clinic_id=gastro_clinic.id)
            db.add(endoscopy_room)
            db.flush()
        if consultation_service and consultation_service not in room.allowed_services:
            room.allowed_services.append(consultation_service)
        if gastroscopy_service and gastroscopy_service not in endoscopy_room.allowed_services:
            endoscopy_room.allowed_services.append(gastroscopy_service)

        if consultation_service and gastroscopy_service:
            consultation_appointment = db.scalar(
                select(Appointment).where(
                    Appointment.patient_id == multi_patient.id,
                    Appointment.date == date.today(),
                    Appointment.service_id == consultation_service.id,
                )
            )
            if consultation_appointment is None:
                consultation_appointment = Appointment(
                    patient_id=multi_patient.id,
                    provider_id=provider.id,
                    room_id=room.id,
                    service_id=consultation_service.id,
                    date=date.today(),
                    start_time=time(15, 0),
                    end_time=time(15, 30),
                    duration_minutes=30,
                    status="scheduled",
                    source="manual",
                    arrived_at=datetime.now(timezone.utc),
                )
                db.add(consultation_appointment)
                db.flush()
            else:
                consultation_appointment.arrived_at = consultation_appointment.arrived_at or datetime.now(timezone.utc)

            gastroscopy_appointment = db.scalar(
                select(Appointment).where(
                    Appointment.patient_id == multi_patient.id,
                    Appointment.date == date.today(),
                    Appointment.service_id == gastroscopy_service.id,
                )
            )
            if gastroscopy_appointment is None:
                gastroscopy_appointment = Appointment(
                    patient_id=multi_patient.id,
                    provider_id=provider.id,
                    room_id=endoscopy_room.id,
                    service_id=gastroscopy_service.id,
                    date=date.today(),
                    start_time=time(15, 30),
                    end_time=time(16, 0),
                    duration_minutes=30,
                    status="scheduled",
                    source="manual",
                )
                db.add(gastroscopy_appointment)
                db.flush()

            multi_journey = db.scalar(
                select(PatientJourney).where(PatientJourney.appointment_id == consultation_appointment.id)
            )
            if multi_journey is None:
                multi_journey = PatientJourney(
                    patient_id=multi_patient.id,
                    appointment_id=consultation_appointment.id,
                    intake_channel="manual",
                )
                db.add(multi_journey)
                db.flush()
            multi_journey.current_stage = "ready_for_clinician"
            multi_journey.document_status = "complete"
            multi_journey.preparation_status = "complete"
            multi_journey.check_in_status = "ready"
            multi_journey.encounter_status = "not_started"
            multi_journey.consumables_status = "not_ready"
            multi_journey.billing_status = "not_ready"
            multi_journey.payment_status = "not_due"
            multi_journey.closed_at = None

            activity_specs = [
                (
                    "first-gastroenterology-consultation",
                    consultation_appointment,
                    consultation_service,
                    room,
                    1,
                    "specialist_consultation",
                    "ready",
                ),
                (
                    "gastroscopy",
                    gastroscopy_appointment,
                    gastroscopy_service,
                    endoscopy_room,
                    2,
                    "gastroscopy",
                    "planned",
                ),
            ]
            for activity_key, activity_appointment, activity_service, activity_room, sequence, activity_kind, activity_status in activity_specs:
                activity = db.scalar(
                    select(JourneyActivity).where(
                        JourneyActivity.journey_id == multi_journey.id,
                        JourneyActivity.activity_key == activity_key,
                    )
                )
                planned_start = datetime.combine(date.today(), activity_appointment.start_time)
                planned_end = datetime.combine(date.today(), activity_appointment.end_time)
                if activity is None:
                    activity = JourneyActivity(
                        journey_id=multi_journey.id,
                        activity_key=activity_key,
                        sequence=sequence,
                        required=True,
                    )
                    db.add(activity)
                activity.appointment_id = activity_appointment.id
                activity.service_id = activity_service.id
                activity.activity_kind = activity_kind
                activity.specialty_key = "gastroenterology"
                activity.clinic_id = gastro_clinic.id
                activity.primary_provider_id = provider.id
                activity.room_id = activity_room.id
                activity.planned_start = planned_start
                activity.planned_end = planned_end
                activity.status = activity_status
                activity.form_resolution_status = "resolved"
                activity.billing_status = "not_ready"
                activity.consumables_status = "not_ready"

        demo_documents = [
            {
                "title": "Vanjska gastroskopija 03/2025",
                "source_type": "external",
                "document_type": "gastroscopy",
                "origin": "Privatna poliklinika",
                "document_date": date(2025, 3, 12),
                "institution": "Privatna poliklinika",
                "raw_text": "Demo vanjski nalaz: gastroskopija opisuje refluks/GERB. H. pylori negativan. Terapija esomeprazol.",
                "ai_summary": "AI prijedlog pregledan od lijecnika: vanjski nalaz navodi GERB/refluks i H. pylori negativan status.",
                "key_findings": ["GERB/refluks naveden u dokumentu", "H. pylori status naveden u dokumentu", "Terapija inhibitorom protonske pumpe spomenuta u dokumentu"],
                "recommendations": ["Nastaviti pracenje simptoma i terapiju prema odluci lijecnika"],
            },
            {
                "title": "Demo patologija polipa",
                "source_type": "uploaded",
                "document_type": "pathology",
                "origin": "Uploaded by patient",
                "document_date": date.today() - timedelta(days=7),
                "institution": "Demo laboratorij",
                "raw_text": "Demo patologija: tubularni adenom. Preporucena kontrola prema lijecnickoj procjeni.",
                "ai_summary": "AI prijedlog pregledan od lijecnika: dokument navodi tubularni adenom i potrebu kontrole.",
                "key_findings": ["Prethodni polip/adenom naveden u dokumentu", "Patologija/biopsija spomenuta u dokumentu"],
                "recommendations": ["Dokument sadrzi preporuku ili kontrolu koju treba lijecnik pregledati"],
            },
            {
                "title": "Demo laboratorij ceka pregled",
                "source_type": "uploaded",
                "document_type": "laboratory",
                "origin": "Uploaded by patient",
                "document_date": date.today(),
                "institution": "Demo laboratorij",
                "raw_text": "Demo laboratorijski nalaz ceka se lijecnicki pregled.",
                "ai_summary": "AI prijedlog jos nije pregledan.",
                "key_findings": ["Laboratorijski nalaz je zaprimljen"],
                "recommendations": ["Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled"],
                "physician_reviewed": False,
            },
        ]
        for values in demo_documents:
            document = db.scalar(select(ClinicalDocument).where(ClinicalDocument.patient_id == patient.id, ClinicalDocument.title == values["title"]))
            reviewed = values.pop("physician_reviewed", True)
            review_status = "reviewed" if reviewed else "needs_physician_review"
            extraction_status = "accepted" if reviewed else "generated"
            extraction_timestamp = datetime.now(timezone.utc)
            if document is None:
                document = ClinicalDocument(
                    patient_id=patient.id,
                    review_status=review_status,
                    ai_extraction_status=extraction_status,
                    ai_extraction_generated_at=extraction_timestamp,
                    ai_extraction_updated_at=extraction_timestamp,
                    physician_reviewed=reviewed,
                    reviewed_by=None,
                    reviewed_at=extraction_timestamp if reviewed else None,
                    **values,
                )
                db.add(document)
            else:
                for field, value in values.items():
                    setattr(document, field, value)
                document.review_status = review_status
                document.ai_extraction_status = extraction_status
                document.ai_extraction_generated_at = document.ai_extraction_generated_at or extraction_timestamp
                document.ai_extraction_updated_at = extraction_timestamp
                document.physician_reviewed = reviewed
                document.reviewed_at = extraction_timestamp if reviewed else None

        reviewed_document_ids = [
            document.id
            for document in db.scalars(select(ClinicalDocument).where(ClinicalDocument.patient_id == patient.id, ClinicalDocument.physician_reviewed.is_(True), ClinicalDocument.review_status == "reviewed")).all()
        ]
        summary = db.scalar(select(PatientClinicalSummaryRecord).where(PatientClinicalSummaryRecord.patient_id == patient.id, PatientClinicalSummaryRecord.status == "reviewed"))
        summary_values = {
            "summary_text": "Demo pregledani sazetak: poznat GERB/refluks, raniji polip/adenom i potreba pracenja prema izvorima.",
            "known_conditions": ["GERB/refluks naveden u dokumentu", "Prethodni polip/adenom naveden u dokumentu"],
            "key_findings": ["H. pylori status naveden u dokumentu"],
            "open_items": ["Pregledati dokumente koji cekaju lijecnicki pregled"],
            "risks": [],
            "last_recommendations": ["Nastaviti pracenje simptoma i kontrolu prema odluci lijecnika"],
            "source_document_ids": reviewed_document_ids,
            "status": "reviewed",
            "generated_by": "demo_seed",
            "reviewed_at": datetime.now(timezone.utc),
        }
        if summary is None:
            db.add(PatientClinicalSummaryRecord(patient_id=patient.id, **summary_values))
        else:
            for field, value in summary_values.items():
                setattr(summary, field, value)

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
