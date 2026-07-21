from datetime import date, time

from sqlalchemy import select

from app.core.security import hash_password
from app.models.domain import (
    Appointment,
    AuditLog,
    ClinicalDocument,
    Clinic,
    ClinicMembership,
    Patient,
    PatientClinicAssociation,
    Permission,
    Provider,
    Role,
    Room,
    Service,
    User,
)
from tests.conftest import login_token


def headers(client, email: str) -> dict[str, str]:
    token = login_token(client, email)
    return {"Authorization": f"Bearer {token}"}


def permission(db, name: str) -> Permission:
    item = db.scalar(select(Permission).where(Permission.name == name))
    if item is None:
        item = Permission(name=name, description=name)
        db.add(item)
        db.flush()
    return item


def user_with_role(db, email: str, permissions: list[str], category: str, clinic: Clinic) -> User:
    role = Role(
        name=email.split("@")[0],
        description=email,
        professional_category=category,
        permissions=[permission(db, name) for name in permissions],
    )
    user = User(email=email, full_name=email, password_hash=hash_password("secret"), role=role)
    db.add_all([role, user])
    db.flush()
    db.add(ClinicMembership(user_id=user.id, clinic_id=clinic.id, active=True, created_by_user_id=user.id))
    db.flush()
    return user


def setup_scope(db):
    clinic_a = Clinic(name="Clinic A", institution_key="nura")
    clinic_b = Clinic(name="Clinic B", institution_key="nura")
    clinic_other = Clinic(name="Other Institution Clinic", institution_key="other")
    patient = Patient(first_name="Synthetic", last_name="Patient")
    provider = Provider(full_name="dr. Synthetic", specialty="Gastroenterology", clinic=clinic_b)
    room = Room(name="Institution Room", type="ordination", clinic=clinic_b)
    service = Service(name="Synthetic service", duration_minutes=30, price=100)
    db.add_all([clinic_a, clinic_b, clinic_other, patient, provider, room, service])
    db.flush()
    db.add_all(
        [
            PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic_a.id, active=True),
            PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic_b.id, active=True),
        ]
    )
    appointment = Appointment(
        patient_id=patient.id,
        provider_id=provider.id,
        room_id=room.id,
        service_id=service.id,
        clinic_id=clinic_b.id,
        date=date(2026, 7, 21),
        start_time=time(9, 0),
        end_time=time(9, 30),
        duration_minutes=30,
        status="scheduled",
        source="manual",
    )
    db.add(appointment)
    db.flush()
    return clinic_a, clinic_b, clinic_other, patient, appointment


MEDICAL_READ = ["clinical.documents.read_institution", "clinical_documents.read"]
MEDICAL_EDIT = MEDICAL_READ + ["clinical.documents.edit_own_draft", "clinical_documents.review"]
MEDICAL_ADDENDUM = MEDICAL_READ + ["clinical.documents.add_addendum"]


def clinical_doc(db, patient: Patient, clinic: Clinic, author: User | None = None, status: str = "draft", document_type: str = "gastroscopy", is_clinical_record: bool = True) -> ClinicalDocument:
    document = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=clinic.id,
        source_type="external",
        document_type=document_type,
        title="Klinički nalaz",
        raw_text="Sintetički klinički tekst",
        review_status=status,
        physician_reviewed=status in {"reviewed", "signed"},
        author_user_id=author.id if author else None,
        author_professional_role=author.role.name if author else None,
        is_clinical_record=is_clinical_record,
    )
    db.add(document)
    db.flush()
    return document


def test_physician_and_nurse_read_clinical_documents_across_clinics_same_institution(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    physician = user_with_role(db, "doctor-a@test.local", MEDICAL_READ, "medical_staff", clinic_a)
    nurse = user_with_role(db, "nurse-a@test.local", MEDICAL_READ, "medical_staff", clinic_a)
    physician_doc = clinical_doc(db, patient, clinic_b, physician, status="reviewed")
    nursing_doc = clinical_doc(db, patient, clinic_b, nurse, status="reviewed", document_type="other")
    db.commit()

    assert client.get(f"/api/clinical-documents/{physician_doc.id}", headers=headers(client, physician.email)).status_code == 200
    assert client.get(f"/api/clinical-documents/{physician_doc.id}", headers=headers(client, nurse.email)).status_code == 200
    assert client.get(f"/api/clinical-documents/{nursing_doc.id}", headers=headers(client, nurse.email)).status_code == 200


def test_administrative_and_other_institution_users_cannot_read_full_clinical_document(client, db):
    clinic_a, clinic_b, clinic_other, patient, _ = setup_scope(db)
    admin = user_with_role(db, "system-admin@test.local", ["system.admin", "clinical.documents.read_institution"], "administrative", clinic_a)
    other_doctor = user_with_role(db, "doctor-other@test.local", MEDICAL_READ, "medical_staff", clinic_other)
    other_nurse = user_with_role(db, "nurse-other@test.local", MEDICAL_READ, "medical_staff", clinic_other)
    document = clinical_doc(db, patient, clinic_b, status="reviewed")
    source_nonclinical = clinical_doc(db, patient, clinic_b, status="reviewed", document_type="invoice_attachment", is_clinical_record=False)
    db.commit()

    assert client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, admin.email)).status_code == 403
    assert client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, other_doctor.email)).status_code == 404
    assert client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, other_nurse.email)).status_code == 404
    assert client.get(f"/api/clinical-documents/{source_nonclinical.id}", headers=headers(client, admin.email)).status_code == 403


def test_author_controlled_draft_editing_and_signed_immutability(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    author_doctor = user_with_role(db, "author-doctor@test.local", MEDICAL_EDIT, "medical_staff", clinic_a)
    other_doctor = user_with_role(db, "other-doctor@test.local", MEDICAL_EDIT, "medical_staff", clinic_a)
    author_nurse = user_with_role(db, "author-nurse@test.local", MEDICAL_EDIT, "medical_staff", clinic_a)
    doctor_draft = clinical_doc(db, patient, clinic_b, author_doctor, status="draft")
    nurse_draft = clinical_doc(db, patient, clinic_b, author_nurse, status="draft", document_type="other")
    signed_doc = clinical_doc(db, patient, clinic_b, author_doctor, status="signed")
    db.commit()

    denied_other = client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, other_doctor.email), json={"title": "Tuđa izmjena"})
    denied_nurse = client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, author_nurse.email), json={"title": "Sestrinska izmjena"})
    own_doctor = client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, author_doctor.email), json={"title": "Vlastiti liječnički nacrt"})
    own_nurse = client.patch(f"/api/clinical-documents/{nurse_draft.id}", headers=headers(client, author_nurse.email), json={"title": "Vlastita sestrinska dokumentacija"})
    signed_read = client.get(f"/api/clinical-documents/{signed_doc.id}", headers=headers(client, author_doctor.email))
    signed_denied = client.patch(f"/api/clinical-documents/{signed_doc.id}", headers=headers(client, author_doctor.email), json={"title": "Izmjena potpisanog"})

    assert denied_other.status_code == 403
    assert denied_nurse.status_code == 403
    assert own_doctor.status_code == 200
    assert own_nurse.status_code == 200
    assert signed_read.status_code == 200
    assert signed_denied.status_code == 409


def test_addendum_is_separate_audited_record_and_does_not_change_original(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    doctor = user_with_role(db, "addendum-doctor@test.local", MEDICAL_ADDENDUM, "medical_staff", clinic_a)
    document = clinical_doc(db, patient, clinic_b, doctor, status="signed")
    original_text = document.raw_text
    db.commit()

    response = client.post(
        f"/api/clinical-documents/{document.id}/addenda",
        headers=headers(client, doctor.email),
        json={"reason": "Naknadna dopuna", "content": "Sintetička dopuna nalaza."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["original_document_id"] == document.id
    assert body["author_user_id"] == doctor.id
    assert body["signed_at"]
    db.refresh(document)
    assert document.raw_text == original_text
    assert db.scalar(select(AuditLog).where(AuditLog.action == "clinical_document_addendum_created")) is not None


def test_institution_read_is_audited_and_does_not_open_finance_or_dashboard(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    nurse = user_with_role(db, "boundary-nurse@test.local", MEDICAL_READ, "medical_staff", clinic_a)
    document = clinical_doc(db, patient, clinic_b, nurse, status="reviewed")
    db.commit()

    read_response = client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, nurse.email))
    finance_response = client.get("/api/invoices", headers=headers(client, nurse.email))
    dashboard_response = client.get("/api/dashboard/day?date=2026-07-21", headers=headers(client, nurse.email))

    assert read_response.status_code == 200
    assert finance_response.status_code == 403
    assert dashboard_response.status_code == 403
    audit_log = db.scalar(select(AuditLog).where(AuditLog.action == "clinical_document_viewed", AuditLog.entity_id == document.id))
    assert audit_log is not None
    assert audit_log.after_json["document_clinic_id"] == clinic_b.id


def test_patient_appointment_availability_remains_minimal(client, db):
    clinic_a, _, _, patient, appointment = setup_scope(db)
    user = user_with_role(db, "schedule-medical@test.local", MEDICAL_READ + ["appointments.patient_availability.read"], "medical_staff", clinic_a)
    db.commit()

    response = client.get(f"/api/patients/{patient.id}/appointments", headers={**headers(client, user.email), "X-Clinic-Id": str(clinic_a.id)})

    assert response.status_code == 200
    assert response.json()[0]["appointment_id"] == appointment.id
    serialized = str(response.json())
    assert "Sintetički klinički tekst" not in serialized
