from __future__ import annotations

import json
import os
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.domain import (
    Appointment,
    ClinicalDocument,
    ClinicalDocumentAddendum,
    ClinicalEpisode,
    ClinicalFinding,
    ClinicalFormDefinition,
    ClinicalFormInstance,
    ClinicalFormVersion,
    ClinicalOpenQuestion,
    Clinic,
    ClinicMembership,
    Invoice,
    InvoiceLine,
    Institution,
    JourneyActivity,
    Patient,
    PatientClinicAssociation,
    PatientJourney,
    PaymentTransaction,
    Permission,
    Provider,
    Role,
    Room,
    Service,
    SignedClinicalReport,
    User,
)
from app.services.reports import report_digest
from app.services.seed import PERMISSIONS


PASSWORD = "E2e-local-only-123!"
_PERMISSION_CACHE: dict[str, Permission] = {}


def clinic_today() -> date:
    override = os.getenv("ASTRA_E2E_DATE")
    if override:
        return date.fromisoformat(override)
    return datetime.now(timezone.utc).date()


def get_or_create_permission(db, name: str) -> Permission:
    cached = _PERMISSION_CACHE.get(name)
    if cached is not None:
        return cached
    permission = db.scalar(select(Permission).where(Permission.name == name))
    if permission:
        _PERMISSION_CACHE[name] = permission
        return permission
    permission = Permission(name=name, description=name)
    db.add(permission)
    _PERMISSION_CACHE[name] = permission
    return permission


def role(db, name: str, permission_names: list[str], professional_category: str = "administrative_staff") -> Role:
    item = db.scalar(select(Role).where(Role.name == name))
    permissions = [get_or_create_permission(db, permission_name) for permission_name in permission_names]
    if item:
        item.permissions = permissions
        item.professional_category = professional_category
        return item
    item = Role(name=name, description=f"Synthetic E2E role {name}", permissions=permissions, professional_category=professional_category)
    db.add(item)
    return item


def user(db, email: str, full_name: str, role_obj: Role) -> User:
    item = db.scalar(select(User).where(User.email == email))
    if item:
        item.full_name = full_name
        item.password_hash = hash_password(PASSWORD)
        item.role = role_obj
        item.active = True
        return item
    item = User(email=email, full_name=full_name, password_hash=hash_password(PASSWORD), role=role_obj, active=True)
    db.add(item)
    return item


def link_membership(db, user_obj: User, clinic: Clinic) -> None:
    existing = db.scalar(select(ClinicMembership).where(ClinicMembership.user_id == user_obj.id, ClinicMembership.clinic_id == clinic.id))
    if existing:
        existing.active = True
        return
    db.add(ClinicMembership(user_id=user_obj.id, clinic_id=clinic.id, active=True, created_by_user_id=user_obj.id))


def link_patient(db, patient: Patient, clinic: Clinic, creator: User) -> None:
    existing = db.scalar(select(PatientClinicAssociation).where(PatientClinicAssociation.patient_id == patient.id, PatientClinicAssociation.clinic_id == clinic.id))
    if existing:
        existing.active = True
        return
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic.id, active=True, created_by_user_id=creator.id))


def clinic(db, name: str, timezone_name: str = "Europe/Zagreb", institution: Institution | None = None) -> Clinic:
    item = db.scalar(select(Clinic).where(Clinic.name == name))
    if item:
        item.active = True
        item.visible_in_catalog = True
        item.timezone = timezone_name
        if institution is not None:
            item.institution = institution
            item.institution_key = institution.code or "default"
        return item
    item = Clinic(
        name=name,
        timezone=timezone_name,
        institution=institution,
        institution_key=institution.code if institution and institution.code else "default",
        active=True,
        visible_in_catalog=True,
    )
    db.add(item)
    return item


def service(db, name: str, code: str, duration: int, price: str) -> Service:
    item = db.scalar(select(Service).where(Service.code == code))
    if item:
        item.name = name
        item.duration_minutes = duration
        item.price = Decimal(price)
        item.active = True
        item.visible_in_catalog = True
        return item
    item = Service(name=name, code=code, duration_minutes=duration, price=Decimal(price), active=True, visible_in_catalog=True)
    db.add(item)
    return item


def room(db, name: str, clinic_obj: Clinic, allowed_services: list[Service]) -> Room:
    item = db.scalar(select(Room).where(Room.name == name))
    if not item:
        item = Room(name=name, type="e2e", clinic=clinic_obj, active=True, visible_in_catalog=True)
        db.add(item)
    item.clinic = clinic_obj
    item.active = True
    item.visible_in_catalog = True
    item.allowed_services = allowed_services
    return item


def provider(db, full_name: str, email: str, clinic_obj: Clinic) -> Provider:
    item = db.scalar(select(Provider).where(Provider.email == email))
    weekly = {str(day): {"enabled": True, "start": "07:00", "end": "20:00"} for day in range(5)}
    if item:
        item.full_name = full_name
        item.clinic = clinic_obj
        item.active = True
        item.available_for_work = True
        item.weekly_working_hours = weekly
        return item
    item = Provider(
        full_name=full_name,
        specialty="Gastroenterologija",
        email=email,
        staff_role="physician",
        clinic=clinic_obj,
        active=True,
        available_for_work=True,
        weekly_working_hours=weekly,
    )
    db.add(item)
    return item


def patient(db, first_name: str, last_name: str, email: str) -> Patient:
    item = db.scalar(select(Patient).where(Patient.email == email))
    if item:
        return item
    item = Patient(first_name=first_name, last_name=last_name, date_of_birth=date(1990, 1, 2), email=email, phone="099000000")
    db.add(item)
    return item


def appointment(
    db,
    patient_obj: Patient,
    service_obj: Service,
    provider_obj: Provider,
    room_obj: Room,
    clinic_obj: Clinic,
    day: date,
    start: time,
    end: time,
    creator: User,
    status: str = "scheduled",
) -> Appointment:
    item = db.scalar(
        select(Appointment).where(
            Appointment.patient_id == patient_obj.id,
            Appointment.clinic_id == clinic_obj.id,
            Appointment.date == day,
            Appointment.start_time == start,
        )
    )
    duration = int((datetime.combine(day, end) - datetime.combine(day, start)).total_seconds() // 60)
    if item:
        item.service = service_obj
        item.provider = provider_obj
        item.room = room_obj
        item.end_time = end
        item.duration_minutes = duration
        item.status = status
        return item
    item = Appointment(
        patient=patient_obj,
        service=service_obj,
        provider=provider_obj,
        room=room_obj,
        clinic=clinic_obj,
        date=day,
        start_time=start,
        end_time=end,
        duration_minutes=duration,
        status=status,
        source="manual",
        created_by=creator.id,
    )
    db.add(item)
    return item


def journey(db, appointment_obj: Appointment, stage: str, creator: User, payment_status: str = "not_due") -> PatientJourney:
    item = db.scalar(select(PatientJourney).where(PatientJourney.appointment_id == appointment_obj.id))
    if item:
        item.current_stage = stage
        item.clinic_id = appointment_obj.clinic_id
        item.payment_status = payment_status
        return item
    item = PatientJourney(
        patient_id=appointment_obj.patient_id,
        appointment=appointment_obj,
        clinic_id=appointment_obj.clinic_id,
        intake_channel="manual",
        current_stage=stage,
        document_status="complete",
        preparation_status="complete",
        check_in_status="not_arrived" if stage in {"booked", "ready_for_arrival"} else "ready",
        encounter_status="completed" if stage in {"awaiting_payment", "completed"} else "not_started",
        consumables_status="not_applicable" if stage in {"awaiting_payment", "completed"} else "not_ready",
        billing_status="closed" if stage == "completed" else ("invoice_created" if stage == "awaiting_payment" else "not_ready"),
        payment_status=payment_status,
        created_by=creator.id,
    )
    db.add(item)
    return item


def activity(
    db,
    journey_obj: PatientJourney,
    appointment_obj: Appointment,
    service_obj: Service,
    provider_obj: Provider,
    room_obj: Room,
    key: str,
    sequence: int,
    status: str = "planned",
    offset_minutes: int = 0,
    duration_minutes: int | None = None,
) -> JourneyActivity:
    item = db.scalar(select(JourneyActivity).where(JourneyActivity.journey_id == journey_obj.id, JourneyActivity.activity_key == key))
    start_dt = datetime.combine(appointment_obj.date, appointment_obj.start_time) + timedelta(minutes=offset_minutes)
    end_dt = start_dt + timedelta(minutes=duration_minutes or service_obj.duration_minutes)
    if item:
        item.status = status
        item.planned_start = start_dt
        item.planned_end = end_dt
        item.appointment = appointment_obj if sequence == 1 else item.appointment
        item.form_resolution_status = "not_required"
        return item
    item = JourneyActivity(
        journey=journey_obj,
        appointment=appointment_obj if sequence == 1 else None,
        service=service_obj,
        activity_key=key,
        activity_kind="procedure" if "gastroscopy" in key or "colonoscopy" in key else "specialist_consultation",
        specialty_key="gastroenterology",
        clinic_id=appointment_obj.clinic_id,
        primary_provider=provider_obj,
        room=room_obj,
        sequence=sequence,
        required=True,
        planned_start=start_dt,
        planned_end=end_dt,
        status=status,
        form_resolution_status="not_required",
        consumables_status="not_applicable" if status == "completed" else "not_ready",
        billing_status="ready" if status == "completed" else "not_ready",
        created_by=journey_obj.created_by,
    )
    db.add(item)
    return item


def seed() -> dict:
    day = clinic_today()
    with SessionLocal() as db:
        _PERMISSION_CACHE.clear()
        _PERMISSION_CACHE.update({item.name: item for item in db.scalars(select(Permission)).all()})
        all_permissions = role(db, "e2e_admin", PERMISSIONS)
        receptionist_role = role(db, "e2e_receptionist", ["patients.read", "patients.write", "appointments.read", "appointments.write", "appointments.patient_availability.read", "services.read", "journey.read", "journey.transition", "checkin.update", "encounter.read", "audit.access_events.write"])
        dual_role = role(db, "e2e_dual", ["patients.read", "appointments.read", "appointments.write", "appointments.patient_availability.read", "services.read", "journey.read", "checkin.update", "encounter.read"])
        physician_role = role(
            db,
            "e2e_physician",
            [
                "clinical.documents.read_institution",
                "clinical.documents.edit_own_draft",
                "clinical.documents.add_addendum",
                "documents.view_source",
                "documents.review",
                "reports.read",
                "episodes.read",
                "clinical_findings.read",
                "clinical_open_questions.read",
                "clinical_evidence_timeline.read",
            ],
            "medical_staff",
        )
        physician_reader_role = role(
            db,
            "e2e_physician_reader",
            ["clinical.documents.read_institution", "clinical.documents.edit_own_draft", "reports.read"],
            "medical_staff",
        )
        nurse_role = role(db, "e2e_nurse", ["clinical.documents.read_institution", "reports.read"], "medical_staff")
        foreign_physician_role = role(db, "e2e_foreign_physician", ["clinical.documents.read_institution", "reports.read"], "medical_staff")

        institution_a = db.scalar(select(Institution).where(Institution.code == "e2e-nura"))
        if institution_a is None:
            institution_a = Institution(code="e2e-nura", name="E2E NURA", active=True)
            db.add(institution_a)
        institution_other = db.scalar(select(Institution).where(Institution.code == "e2e-other"))
        if institution_other is None:
            institution_other = Institution(code="e2e-other", name="E2E Druga ustanova", active=True)
            db.add(institution_other)
        db.flush()
        clinic_a = clinic(db, "E2E Klinika A", institution=institution_a)
        clinic_b = clinic(db, "E2E Klinika B", institution=institution_a)
        clinic_c = clinic(db, "E2E Druga ustanova", institution=institution_other)
        admin_a = user(db, "e2e.admin.a@example.invalid", "E2E Admin A", all_permissions)
        reception_a = user(db, "e2e.reception.a@example.invalid", "E2E Recepcija A", receptionist_role)
        dual = user(db, "e2e.dual@example.invalid", "E2E Dvije Klinike", dual_role)
        system_admin = user(db, "e2e.system@example.invalid", "E2E System Admin", all_permissions)
        physician_a = user(db, "e2e.physician.a@example.invalid", "dr. E2E Klinički A", physician_role)
        physician_b = user(db, "e2e.physician.b@example.invalid", "dr. E2E Klinički B", physician_reader_role)
        nurse_a = user(db, "e2e.nurse.a@example.invalid", "E2E Medicinska sestra", nurse_role)
        foreign_physician = user(db, "e2e.physician.foreign@example.invalid", "dr. E2E Druga ustanova", foreign_physician_role)
        db.flush()
        for user_obj, clinic_obj in [
            (admin_a, clinic_a),
            (reception_a, clinic_a),
            (dual, clinic_a),
            (dual, clinic_b),
            (physician_a, clinic_a),
            (physician_b, clinic_b),
            (nurse_a, clinic_a),
            (foreign_physician, clinic_c),
        ]:
            link_membership(db, user_obj, clinic_obj)

        consult = service(db, "E2E prvi gastro pregled", "E2E-CONSULT", 30, "90.00")
        gastro = service(db, "E2E gastroskopija", "E2E-GASTRO", 30, "150.00")
        colon = service(db, "E2E kolonoskopija", "E2E-COLON", 45, "220.00")
        room_a1 = room(db, "E2E A ordinacija", clinic_a, [consult, gastro, colon])
        room_a2 = room(db, "E2E A endoskopija", clinic_a, [gastro, colon])
        room_b1 = room(db, "E2E B ordinacija", clinic_b, [consult, gastro, colon])
        provider_a = provider(db, "dr. E2E A", "e2e.doctor.a@example.invalid", clinic_a)
        provider_b = provider(db, "dr. E2E B", "e2e.doctor.b@example.invalid", clinic_b)
        db.flush()

        shared = patient(db, "E2E", "Zajednicki Pacijent", "e2e.patient.shared@example.invalid")
        only_b = patient(db, "E2E", "Samo B Pacijent", "e2e.patient.onlyb@example.invalid")
        paid_patient = patient(db, "E2E", "Placeni Pacijent", "e2e.patient.paid@example.invalid")
        foreign_patient = patient(db, "E2E", "Druga Ustanova Pacijent", "e2e.patient.foreign@example.invalid")
        db.flush()
        link_patient(db, shared, clinic_a, admin_a)
        link_patient(db, shared, clinic_b, admin_a)
        link_patient(db, only_b, clinic_b, admin_a)
        link_patient(db, paid_patient, clinic_a, admin_a)
        link_patient(db, foreign_patient, clinic_c, foreign_physician)

        b_appt = appointment(db, shared, consult, provider_b, room_b1, clinic_b, day, time(9, 0), time(9, 30), admin_a)
        a_appt = appointment(db, shared, consult, provider_a, room_a1, clinic_a, day, time(10, 0), time(10, 30), admin_a)
        paid_appt = appointment(db, paid_patient, gastro, provider_a, room_a2, clinic_a, day, time(12, 0), time(12, 30), admin_a)
        only_b_appt = appointment(db, only_b, gastro, provider_b, room_b1, clinic_b, day, time(11, 0), time(11, 30), admin_a)
        db.flush()

        a_journey = journey(db, a_appt, "booked", admin_a)
        b_journey = journey(db, b_appt, "booked", admin_a)
        paid_journey = journey(db, paid_appt, "completed", admin_a, payment_status="paid")
        only_b_journey = journey(db, only_b_appt, "booked", admin_a)
        db.flush()

        activity(db, a_journey, a_appt, consult, provider_a, room_a1, "consultation", 1, status="planned", offset_minutes=0, duration_minutes=30)
        activity(db, a_journey, a_appt, gastro, provider_a, room_a2, "gastroscopy", 2, status="planned", offset_minutes=30, duration_minutes=30)
        activity(db, b_journey, b_appt, consult, provider_b, room_b1, "clinic-b-consultation", 1, status="planned")
        activity(db, only_b_journey, only_b_appt, gastro, provider_b, room_b1, "clinic-b-hidden", 1, status="planned")
        activity(db, paid_journey, paid_appt, gastro, provider_a, room_a2, "paid-gastroscopy", 1, status="completed")
        db.flush()

        invoice = db.scalar(select(Invoice).where(Invoice.journey_id == paid_journey.id))
        if not invoice:
            invoice = Invoice(patient_id=paid_patient.id, clinic_id=clinic_a.id, appointment_id=paid_appt.id, journey_id=paid_journey.id, invoice_number="E2E-PAID-001", invoice_date=day, status="issued", total_amount=Decimal("150.00"), payment_status="paid")
            db.add(invoice)
            db.flush()
            db.add(InvoiceLine(invoice_id=invoice.id, service_id=gastro.id, activity_id=paid_journey.activities[0].id if paid_journey.activities else None, description="E2E gastroskopija", quantity=Decimal("1"), unit_price=Decimal("150.00"), total=Decimal("150.00")))
            db.add(PaymentTransaction(invoice_id=invoice.id, amount=Decimal("150.00"), method="card", reference="E2E", created_by=admin_a.id))

        now = datetime.now(timezone.utc)
        signed_document = ClinicalDocument(
            patient_id=shared.id,
            clinic_id=clinic_b.id,
            institution_id=institution_a.id,
            source_type="generated_signed_report",
            document_type="gastroscopy_report",
            title="E2E potpisani nalaz Clinic B",
            author=physician_b.full_name,
            author_user_id=physician_b.id,
            author_professional_role="physician",
            raw_text="ORIGINAL_CONTENT",
            review_status="signed",
            physician_reviewed=True,
            reviewed_by=physician_b.id,
            reviewed_at=now,
            is_clinical_record=True,
            record_classification="clinical",
            lifecycle_status="reviewed",
            received_at=now,
        )
        own_draft = ClinicalDocument(
            patient_id=shared.id,
            clinic_id=clinic_b.id,
            institution_id=institution_a.id,
            source_type="internal",
            document_type="consultation",
            title="E2E vlastiti klinički nacrt",
            author=physician_a.full_name,
            author_user_id=physician_a.id,
            author_professional_role="physician",
            raw_text="E2E DRAFT ORIGINAL",
            review_status="draft",
            physician_reviewed=False,
            is_clinical_record=True,
            record_classification="clinical",
        )
        unclassified_source = ClinicalDocument(
            patient_id=shared.id,
            clinic_id=clinic_b.id,
            institution_id=institution_a.id,
            source_type="uploaded",
            document_type="other",
            title="E2E neklasificirani izvor",
            raw_text="E2E UNCLASSIFIED CONTENT",
            review_status="draft",
            physician_reviewed=False,
            is_clinical_record=False,
            record_classification="unclassified",
        )
        financial_source = ClinicalDocument(
            patient_id=shared.id,
            clinic_id=clinic_b.id,
            institution_id=institution_a.id,
            source_type="uploaded",
            document_type="other",
            title="E2E financijski izvor",
            raw_text="E2E FINANCIAL CONTENT",
            review_status="reviewed",
            physician_reviewed=True,
            is_clinical_record=False,
            record_classification="financial",
        )
        foreign_document = ClinicalDocument(
            patient_id=foreign_patient.id,
            clinic_id=clinic_c.id,
            institution_id=institution_other.id,
            source_type="internal",
            document_type="consultation",
            title="E2E dokument druge ustanove",
            raw_text="E2E FOREIGN CONTENT",
            review_status="reviewed",
            physician_reviewed=True,
            is_clinical_record=True,
            record_classification="clinical",
        )
        db.add_all([signed_document, own_draft, unclassified_source, financial_source, foreign_document])
        db.flush()

        cross_institution_source = ClinicalDocument(
            patient_id=shared.id,
            clinic_id=clinic_c.id,
            institution_id=institution_other.id,
            source_type="internal",
            document_type="consultation",
            title="E2E foreign institution source for shared identity",
            raw_text="E2E_FOREIGN_DERIVED_SOURCE_SENTINEL",
            review_status="reviewed",
            physician_reviewed=True,
            is_clinical_record=True,
            record_classification="clinical",
        )
        foreign_episode = ClinicalEpisode(
            patient_id=shared.id,
            institution_id=institution_other.id,
            title="E2E_FOREIGN_EPISODE_SENTINEL",
            episode_type="gastroenterology",
            status="active",
            priority="routine",
            start_date=day,
            summary="E2E foreign episode summary",
        )
        db.add_all([cross_institution_source, foreign_episode])
        db.flush()
        foreign_finding = ClinicalFinding(
            patient_id=shared.id,
            institution_id=institution_other.id,
            source_document_id=cross_institution_source.id,
            source_type="clinical_document",
            source_label="E2E foreign finding source",
            source_reference=f"clinical_document:{cross_institution_source.id}",
            finding_key="e2e_foreign_finding",
            label="E2E_FOREIGN_FINDING_SENTINEL",
            category="test",
            lifecycle_status="awaiting_review",
            requires_review=True,
        )
        db.add(foreign_finding)
        db.flush()
        foreign_question = ClinicalOpenQuestion(
            patient_id=shared.id,
            institution_id=institution_other.id,
            finding_id=foreign_finding.id,
            source_document_id=cross_institution_source.id,
            source_type="clinical_document",
            source_label="E2E foreign question source",
            source_reference=f"clinical_document:{cross_institution_source.id}",
            question_key="e2e_foreign_question",
            label="E2E_FOREIGN_QUESTION_SENTINEL",
            status="awaiting_review",
            requires_clinician_review=True,
        )
        db.add(foreign_question)
        db.flush()

        definition = ClinicalFormDefinition(
            form_key="e2e-signed-snapshot",
            name="E2E potpisani obrazac",
            specialty_key="gastroenterology",
            activity_kind="specialist_consultation",
            active=True,
        )
        db.add(definition)
        db.flush()
        version = ClinicalFormVersion(
            definition_id=definition.id,
            version=1,
            status="published",
            sections_json=[{"section_key": "main", "fields": [{"field_key": "finding", "label": "Nalaz", "type": "long_text"}]}],
            validation_schema_json={},
            print_layout_json={"layout": "e2e-original"},
            output_document_type="gastroscopy_report",
        )
        db.add(version)
        db.flush()
        report_activity = b_journey.activities[0]
        instance = ClinicalFormInstance(
            activity_id=report_activity.id,
            form_version_id=version.id,
            purpose="clinical_report",
            status="signed",
            data_json={"finding": "ORIGINAL_CONTENT"},
            rendered_summary="Nalaz: ORIGINAL_CONTENT",
            created_by=physician_b.id,
            last_edited_by=physician_b.id,
            completed_by=physician_b.id,
            signed_by=physician_b.id,
            completed_at=now,
            signed_at=now,
            binding_source="e2e",
            resolved_at=now,
        )
        db.add(instance)
        db.flush()
        signed_report = SignedClinicalReport(
            form_instance_id=instance.id,
            form_version_id=version.id,
            clinical_document_id=signed_document.id,
            activity_id=report_activity.id,
            journey_id=b_journey.id,
            patient_id=shared.id,
            document_type="gastroscopy_report",
            title=signed_document.title,
            structured_data_json={"finding": "ORIGINAL_CONTENT"},
            rendered_content="Nalaz: ORIGINAL_CONTENT",
            version_number=1,
            signer_user_id=physician_b.id,
            signer_name=physician_b.full_name,
            signed_at=now,
            content_hash=report_digest("Nalaz: ORIGINAL_CONTENT", {"finding": "ORIGINAL_CONTENT"}),
            hash_algorithm="sha256",
        )
        db.add(signed_report)
        db.flush()
        existing_addendum = ClinicalDocumentAddendum(
            original_document_id=signed_document.id,
            signed_report_id=signed_report.id,
            original_document_type="signed_clinical_report",
            patient_id=shared.id,
            institution_id=institution_a.id,
            clinic_id=clinic_b.id,
            author_user_id=physician_b.id,
            reason="E2E početna dopuna",
            content="E2E odvojena dopuna",
            status="signed",
            signed_at=now,
            signed_by_user_id=physician_b.id,
        )
        db.add(existing_addendum)
        db.flush()
        instance.data_json = {"finding": "CHANGED_CONTENT"}
        instance.rendered_summary = "Nalaz: CHANGED_CONTENT"
        version.print_layout_json = {"layout": "changed-after-signing"}

        clinic_b_invoice = Invoice(
            patient_id=shared.id,
            clinic_id=clinic_b.id,
            invoice_number="E2E-CLINIC-B-SECRET",
            invoice_date=day,
            status="issued",
            total_amount=Decimal("99.00"),
            payment_status="unpaid",
        )
        db.add(clinic_b_invoice)

        db.commit()

        payload = {
            "date": day.isoformat(),
            "password": PASSWORD,
            "users": {
                "adminA": admin_a.email,
                "receptionA": reception_a.email,
                "dual": dual.email,
                "systemAdmin": system_admin.email,
                "physicianA": physician_a.email,
                "physicianB": physician_b.email,
                "nurseA": nurse_a.email,
                "foreignPhysician": foreign_physician.email,
            },
            "clinics": {"a": clinic_a.id, "b": clinic_b.id, "foreign": clinic_c.id},
            "patients": {"shared": shared.id, "onlyB": only_b.id, "paid": paid_patient.id, "foreign": foreign_patient.id},
            "journeys": {"a": a_journey.id, "b": b_journey.id, "onlyB": only_b_journey.id, "paid": paid_journey.id},
            "appointments": {"clinicBConflict": b_appt.id, "clinicAVisit": a_appt.id},
            "services": {"consult": consult.id, "gastro": gastro.id, "colon": colon.id},
            "providers": {"a": provider_a.id, "b": provider_b.id},
            "rooms": {"a1": room_a1.id, "a2": room_a2.id, "b1": room_b1.id},
            "clinical": {
                "signedDocument": signed_document.id,
                "signedReport": signed_report.id,
                "ownDraft": own_draft.id,
                "unclassifiedSource": unclassified_source.id,
                "financialSource": financial_source.id,
                "foreignDocument": foreign_document.id,
                "clinicBInvoice": clinic_b_invoice.id,
                "foreignEpisode": foreign_episode.id,
                "foreignFinding": foreign_finding.id,
                "foreignQuestion": foreign_question.id,
            },
        }
        output = os.getenv("ASTRA_E2E_SEED_FILE")
        if output:
            Path(output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload


if __name__ == "__main__":
    result = seed()
    output_file = os.getenv("ASTRA_E2E_SEED_FILE")
    if output_file:
        print(json.dumps({"seed_file": output_file, "date": result["date"]}, indent=2))
    else:
        print(json.dumps(result, indent=2))
