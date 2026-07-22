from datetime import date, time

from sqlalchemy import select

from app.core.security import hash_password
from app.models.domain import (
    Appointment,
    AuditLog,
    ClinicalDocument,
    Clinic,
    ClinicMembership,
    Institution,
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
    institution = Institution(code="nura", name="NURA", active=True)
    other_institution = Institution(code="other", name="Other Institution", active=True)
    clinic_a = Clinic(name="Clinic A", institution_key="nura", institution=institution)
    clinic_b = Clinic(name="Clinic B", institution_key="nura", institution=institution)
    clinic_other = Clinic(name="Other Institution Clinic", institution_key="other", institution=other_institution)
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


def clinical_doc(
    db,
    patient: Patient,
    clinic: Clinic,
    author: User | None = None,
    status: str = "draft",
    document_type: str = "gastroscopy",
    is_clinical_record: bool = True,
    record_classification: str = "clinical",
) -> ClinicalDocument:
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
        record_classification=record_classification,
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


def test_institution_entity_and_membership_context_are_resolved_from_clinic_memberships(client, db):
    clinic_a, clinic_b, clinic_other, _, _ = setup_scope(db)
    physician = user_with_role(db, "institution-map@test.local", MEDICAL_READ, "medical_staff", clinic_a)
    db.add(ClinicMembership(user_id=physician.id, clinic_id=clinic_b.id, active=True, created_by_user_id=physician.id))
    db.add(ClinicMembership(user_id=physician.id, clinic_id=clinic_other.id, active=False, created_by_user_id=physician.id))
    db.commit()

    assert clinic_a.institution_id == clinic_b.institution_id
    assert clinic_a.institution_id != clinic_other.institution_id
    assert {membership.clinic.institution_id for membership in physician.clinic_memberships if membership.active} == {clinic_a.institution_id}


def test_medical_category_and_permission_are_both_required_for_institution_read(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    permission_without_category = user_with_role(db, "permission-admin@test.local", MEDICAL_READ, "administrative_staff", clinic_a)
    category_without_permission = user_with_role(db, "category-doctor@test.local", ["clinical_documents.read"], "medical_staff", clinic_a)
    document = clinical_doc(db, patient, clinic_b, status="reviewed")
    db.commit()

    assert client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, permission_without_category.email)).status_code == 403
    assert client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, category_without_permission.email)).status_code == 403


def test_administrative_and_other_institution_users_cannot_read_full_clinical_document(client, db):
    clinic_a, clinic_b, clinic_other, patient, _ = setup_scope(db)
    admin = user_with_role(db, "system-admin@test.local", ["system.admin", "clinical.documents.read_institution"], "administrative", clinic_a)
    other_doctor = user_with_role(db, "doctor-other@test.local", MEDICAL_READ, "medical_staff", clinic_other)
    other_nurse = user_with_role(db, "nurse-other@test.local", MEDICAL_READ, "medical_staff", clinic_other)
    document = clinical_doc(db, patient, clinic_b, status="reviewed")
    source_nonclinical = clinical_doc(db, patient, clinic_b, status="reviewed", document_type="invoice_attachment", is_clinical_record=False, record_classification="financial")
    db.commit()

    assert client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, admin.email)).status_code == 403
    assert client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, other_doctor.email)).status_code == 404
    assert client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, other_nurse.email)).status_code == 404
    assert client.get(f"/api/clinical-documents/{source_nonclinical.id}", headers=headers(client, admin.email)).status_code == 403


def test_unclassified_and_financial_source_documents_are_not_institution_readable(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    doctor = user_with_role(db, "source-policy-doctor@test.local", MEDICAL_READ + ["documents.view_source"], "medical_staff", clinic_a)
    clinical = clinical_doc(db, patient, clinic_b, status="reviewed", record_classification="clinical")
    financial = clinical_doc(db, patient, clinic_b, status="reviewed", record_classification="financial")
    unclassified = clinical_doc(db, patient, clinic_b, status="reviewed", record_classification="unclassified")
    db.commit()

    assert client.get(f"/api/clinical-documents/{clinical.id}", headers=headers(client, doctor.email)).status_code == 200
    assert client.get(f"/api/clinical-documents/{financial.id}", headers=headers(client, doctor.email)).status_code == 403
    assert client.get(f"/api/clinical-documents/{unclassified.id}", headers=headers(client, doctor.email)).status_code == 403


def test_author_controlled_draft_editing_and_signed_immutability(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    author_doctor = user_with_role(db, "author-doctor@test.local", MEDICAL_EDIT, "medical_staff", clinic_a)
    other_doctor = user_with_role(db, "other-doctor@test.local", MEDICAL_EDIT, "medical_staff", clinic_a)
    author_nurse = user_with_role(db, "author-nurse@test.local", MEDICAL_EDIT, "medical_staff", clinic_a)
    doctor_draft = clinical_doc(db, patient, clinic_b, author_doctor, status="draft")
    nurse_draft = clinical_doc(db, patient, clinic_b, author_nurse, status="draft", document_type="other")
    signed_doc = clinical_doc(db, patient, clinic_b, author_doctor, status="signed")
    db.commit()

    author_detail = client.get(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, author_doctor.email))
    other_detail = client.get(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, other_doctor.email))
    nurse_detail = client.get(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, author_nurse.email))
    denied_other = client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, other_doctor.email), json={"title": "Tuđa izmjena"})
    denied_nurse = client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, author_nurse.email), json={"title": "Sestrinska izmjena"})
    own_doctor = client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, author_doctor.email), json={"title": "Vlastiti liječnički nacrt"})
    own_nurse = client.patch(f"/api/clinical-documents/{nurse_draft.id}", headers=headers(client, author_nurse.email), json={"title": "Vlastita sestrinska dokumentacija"})
    signed_read = client.get(f"/api/clinical-documents/{signed_doc.id}", headers=headers(client, author_doctor.email))
    signed_denied = client.patch(f"/api/clinical-documents/{signed_doc.id}", headers=headers(client, author_doctor.email), json={"title": "Izmjena potpisanog"})

    assert author_detail.json()["can_edit"] is True
    assert other_detail.json()["can_edit"] is False
    assert nurse_detail.json()["can_edit"] is False
    assert denied_other.status_code == 403
    assert denied_nurse.status_code == 403
    assert own_doctor.status_code == 200
    assert own_nurse.status_code == 200
    assert signed_read.status_code == 200
    assert signed_denied.status_code == 409


def test_foreign_drafts_are_readable_but_not_editable_and_legacy_unknown_author_is_read_only(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    author_doctor = user_with_role(db, "foreign-author@test.local", MEDICAL_EDIT, "medical_staff", clinic_b)
    reader_doctor = user_with_role(db, "foreign-reader@test.local", MEDICAL_EDIT, "medical_staff", clinic_a)
    reader_nurse = user_with_role(db, "foreign-nurse@test.local", MEDICAL_EDIT, "medical_staff", clinic_a)
    reception = user_with_role(db, "foreign-reception@test.local", ["clinical.documents.read_institution", "clinical.documents.edit_own_draft"], "administrative_staff", clinic_a)
    other_clinic = Clinic(name="Foreign Institution Draft Clinic", institution_key="foreign")
    db.add(other_clinic)
    db.flush()
    other_doctor = user_with_role(db, "foreign-other-inst@test.local", MEDICAL_EDIT, "medical_staff", other_clinic)
    doctor_draft = clinical_doc(db, patient, clinic_b, author_doctor, status="draft")
    legacy_unknown_author = clinical_doc(db, patient, clinic_b, None, status="draft")
    db.commit()

    assert client.get(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, reader_doctor.email)).status_code == 200
    assert client.get(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, reader_nurse.email)).status_code == 200
    assert client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, reader_doctor.email), json={"title": "Tuđi nacrt"}).status_code == 403
    assert client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, reader_nurse.email), json={"title": "Sestrinska izmjena tuđeg nacrta"}).status_code == 403
    assert client.get(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, reception.email)).status_code == 403
    assert client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, reception.email), json={"title": "Administrativna izmjena"}).status_code == 403
    assert client.get(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, other_doctor.email)).status_code == 404
    assert client.patch(f"/api/clinical-documents/{doctor_draft.id}", headers=headers(client, other_doctor.email), json={"title": "Druga ustanova"}).status_code == 404
    assert client.get(f"/api/clinical-documents/{legacy_unknown_author.id}", headers=headers(client, reader_doctor.email)).status_code == 200
    assert client.patch(f"/api/clinical-documents/{legacy_unknown_author.id}", headers=headers(client, reader_doctor.email), json={"title": "Legacy edit"}).status_code == 403


def test_permission_revocation_affects_existing_session_immediately(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    doctor = user_with_role(db, "revoked-editor@test.local", MEDICAL_EDIT, "medical_staff", clinic_a)
    document = clinical_doc(db, patient, clinic_b, doctor, status="draft")
    token = login_token(client, doctor.email)
    auth = {"Authorization": f"Bearer {token}"}
    db.commit()

    assert client.patch(f"/api/clinical-documents/{document.id}", headers=auth, json={"title": "Prva izmjena"}).status_code == 200
    doctor.role.permissions = [permission for permission in doctor.role.permissions if permission.name != "clinical.documents.edit_own_draft"]
    db.commit()

    denied = client.patch(f"/api/clinical-documents/{document.id}", headers=auth, json={"title": "Nakon opoziva"})

    assert denied.status_code == 403


def test_addendum_is_separate_audited_record_and_does_not_change_original(client, db):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    doctor = user_with_role(db, "addendum-doctor@test.local", MEDICAL_ADDENDUM, "medical_staff", clinic_a)
    document = clinical_doc(db, patient, clinic_b, doctor, status="signed")
    original_text = document.raw_text
    db.commit()

    detail = client.get(f"/api/clinical-documents/{document.id}", headers=headers(client, doctor.email))
    response = client.post(
        f"/api/clinical-documents/{document.id}/addenda",
        headers=headers(client, doctor.email),
        json={"reason": "Naknadna dopuna", "content": "Sintetička dopuna nalaza."},
    )

    assert detail.status_code == 200
    assert detail.json()["can_edit"] is False
    assert detail.json()["can_add_addendum"] is True
    assert response.status_code == 200
    body = response.json()
    assert body["original_document_id"] == document.id
    assert body["author_user_id"] == doctor.id
    assert body["patient_id"] == patient.id
    assert body["clinic_id"] == clinic_b.id
    assert body["institution_id"] == clinic_b.institution_id
    assert body["signed_by_user_id"] == doctor.id
    assert body["signed_at"]
    db.refresh(document)
    assert document.raw_text == original_text
    assert db.scalar(select(AuditLog).where(AuditLog.action == "clinical_document_addendum_created")) is not None


def test_addendum_permissions_cross_institution_scope_and_stable_listing(client, db):
    clinic_a, clinic_b, clinic_other, patient, _ = setup_scope(db)
    doctor = user_with_role(db, "addendum-owner@test.local", MEDICAL_ADDENDUM, "medical_staff", clinic_a)
    reception = user_with_role(db, "addendum-reception@test.local", ["clinical.documents.read_institution"], "administrative_staff", clinic_a)
    foreign_doctor = user_with_role(db, "addendum-foreign@test.local", MEDICAL_ADDENDUM, "medical_staff", clinic_other)
    document = clinical_doc(db, patient, clinic_b, doctor, status="signed")
    db.commit()

    first = client.post(
        f"/api/clinical-documents/{document.id}/addenda",
        headers=headers(client, doctor.email),
        json={"reason": "Prva dopuna", "content": "Prvi sintetički sadržaj."},
    )
    second = client.post(
        f"/api/clinical-documents/{document.id}/addenda",
        headers=headers(client, doctor.email),
        json={"reason": "Druga dopuna", "content": "Drugi sintetički sadržaj."},
    )
    denied_reception = client.post(
        f"/api/clinical-documents/{document.id}/addenda",
        headers=headers(client, reception.email),
        json={"reason": "Nedopušteno", "content": "Nedopušteni sadržaj."},
    )
    denied_foreign = client.post(
        f"/api/clinical-documents/{document.id}/addenda",
        headers=headers(client, foreign_doctor.email),
        json={"reason": "Druga ustanova", "content": "Nedopušteni sadržaj."},
    )
    listed = client.get(f"/api/clinical-documents/{document.id}/addenda", headers=headers(client, doctor.email))

    assert first.status_code == 200
    assert second.status_code == 200
    assert denied_reception.status_code == 403
    assert denied_foreign.status_code == 404
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [first.json()["id"], second.json()["id"]]


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


def test_patient_clinical_record_lists_metadata_without_full_document_content(client, db, sql_query_counter):
    clinic_a, clinic_b, _, patient, _ = setup_scope(db)
    physician = user_with_role(db, "timeline-doctor@test.local", MEDICAL_READ + ["clinical.documents.add_addendum", "clinical.documents.edit_own_draft"], "medical_staff", clinic_a)
    own_draft = clinical_doc(db, patient, clinic_b, physician, status="draft", document_type="other")
    signed = clinical_doc(db, patient, clinic_b, status="signed")
    billing_like = clinical_doc(db, patient, clinic_b, status="reviewed", record_classification="financial")
    db.commit()

    request_headers = headers(client, physician.email)
    with sql_query_counter.track() as query_count:
        response = client.get(f"/api/patients/{patient.id}/clinical-record", headers=request_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["institution_id"] == clinic_a.institution_id
    document_ids = {item["document_id"] for item in body["items"]}
    assert own_draft.id in document_ids
    assert signed.id in document_ids
    assert billing_like.id not in document_ids
    assert "Sintetički klinički tekst" not in str(body)
    draft_item = next(item for item in body["items"] if item["document_id"] == own_draft.id)
    signed_item = next(item for item in body["items"] if item["document_id"] == signed.id)
    assert draft_item["can_edit"] is True
    assert signed_item["can_add_addendum"] is True
    assert db.scalar(select(AuditLog).where(AuditLog.action == "clinical_history.opened", AuditLog.entity_id == patient.id)) is not None
    assert query_count.count <= 12
    metadata_selects = [
        statement.lower()
        for statement in query_count.statements
        if "clinical_documents" in statement.lower() and statement.lstrip().lower().startswith("select")
    ]
    assert metadata_selects
    assert all("raw_text" not in statement and "ai_summary" not in statement for statement in metadata_selects)


def test_patient_clinical_record_denies_admin_and_other_institution(client, db):
    clinic_a, clinic_b, clinic_other, patient, _ = setup_scope(db)
    admin = user_with_role(db, "timeline-admin@test.local", ["clinical.documents.read_institution"], "administrative_staff", clinic_a)
    other_doctor = user_with_role(db, "timeline-other@test.local", MEDICAL_READ, "medical_staff", clinic_other)
    document = clinical_doc(db, patient, clinic_b, status="reviewed")
    db.commit()

    admin_response = client.get(f"/api/patients/{patient.id}/clinical-record", headers=headers(client, admin.email))
    other_response = client.get(f"/api/patients/{patient.id}/clinical-record?institution_id={clinic_a.institution_id}", headers=headers(client, other_doctor.email))

    assert document.id
    assert admin_response.status_code == 403
    assert other_response.status_code == 404


def test_patient_appointment_availability_remains_minimal(client, db):
    clinic_a, _, _, patient, appointment = setup_scope(db)
    user = user_with_role(db, "schedule-medical@test.local", MEDICAL_READ + ["appointments.patient_availability.read"], "medical_staff", clinic_a)
    db.commit()

    response = client.get(f"/api/patients/{patient.id}/appointments", headers={**headers(client, user.email), "X-Clinic-Id": str(clinic_a.id)})

    assert response.status_code == 200
    assert response.json()[0]["appointment_id"] == appointment.id
    serialized = str(response.json())
    assert "Sintetički klinički tekst" not in serialized
