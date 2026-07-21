from decimal import Decimal
from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import DBAPIError

from app.auth.dependencies import hash_api_key
from app.core.security import hash_password
from app.models.domain import ApiKey, Appointment, AuditLog, ClinicalDocument, ClinicalFormDefinition, ClinicalFormInstance, ClinicalFormVersion, Clinic, ClinicMembership, Institution, Invoice, InvoiceLine, JourneyActivity, JourneyCheckIn, Patient, PatientJourney, Permission, Provider, Role, Room, Service, SignedClinicalReport, User
from app.services.reports import report_digest


pytestmark = pytest.mark.integration


REQUIRED_TABLES = {
    "users",
    "roles",
    "permissions",
    "patients",
    "appointments",
    "inventory_items",
    "inventory_batches",
    "stock_movements",
    "purchase_orders",
    "invoices",
    "audit_logs",
}


def create_user_with_permissions(db, email: str, permission_names: list[str]) -> User:
    permissions = [Permission(name=name, description=name) for name in permission_names]
    role = Role(name=email.split("@")[0], description=email, permissions=permissions)
    user = User(email=email, full_name=email, password_hash=hash_password("secret"), role=role)
    db.add_all([*permissions, role, user])
    db.flush()
    return user


def permission(db, name: str) -> Permission:
    existing = db.scalar(select(Permission).where(Permission.name == name))
    if existing:
        return existing
    item = Permission(name=name, description=name)
    db.add(item)
    db.flush()
    return item


def create_institution_user(db, email: str, permission_names: list[str], clinic: Clinic, category: str = "medical_staff") -> User:
    role = Role(
        name=email.split("@")[0],
        description=email,
        professional_category=category,
        permissions=[permission(db, name) for name in permission_names],
    )
    user = User(email=email, full_name=email, password_hash=hash_password("secret"), role=role)
    db.add_all([role, user])
    db.flush()
    db.add(ClinicMembership(user_id=user.id, clinic_id=clinic.id, created_by_user_id=user.id))
    db.flush()
    return user


def login(client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "secret"})
    assert response.status_code == 200
    return response.json()["access_token"]


def seed_clinic_objects(db, user: User | None = None):
    patient = Patient(first_name="API", last_name="Patient")
    institution = Institution(code="api-test", name="API Test Institution", active=True)
    clinic = Clinic(name="API Test Clinic", institution_key="api-test", institution=institution)
    provider = Provider(full_name="dr. API", specialty="QA", clinic=clinic)
    room = Room(name="API Room", type="test", clinic=clinic)
    service = Service(name="API Service", duration_minutes=30, price=Decimal("100"))
    db.add_all([patient, institution, clinic, provider, room, service])
    db.flush()
    if user is not None:
        db.add(ClinicMembership(user_id=user.id, clinic_id=clinic.id, created_by_user_id=user.id))
        db.flush()
    return patient, provider, room, service


def test_postgresql_migrations_created_key_tables(pg_db):
    table_names = set(inspect(pg_db.bind).get_table_names())

    assert REQUIRED_TABLES.issubset(table_names)
    assert pg_db.scalar(select(JourneyCheckIn).limit(1)) is None


def test_postgresql_rejects_signed_report_content_update_and_delete_and_preserves_snapshot(pg_client, pg_db):
    signer = create_user_with_permissions(
        pg_db,
        "report-signer-pg@test.local",
        ["reports.read", "clinical.documents.read_institution", "clinical.documents.add_addendum"],
    )
    signer.role.professional_category = "medical_staff"
    patient, provider, room, service = seed_clinic_objects(pg_db, signer)
    appointment = Appointment(patient_id=patient.id, provider_id=provider.id, room_id=room.id, service_id=service.id, date=date(2026, 7, 16), start_time=time(8), end_time=time(8, 30), duration_minutes=30, status="scheduled", source="manual")
    pg_db.add(appointment); pg_db.flush()
    journey = PatientJourney(patient_id=patient.id, appointment_id=appointment.id, intake_channel="manual", current_stage="procedure_completed")
    pg_db.add(journey); pg_db.flush()
    now = datetime.now(timezone.utc)
    activity = JourneyActivity(journey_id=journey.id, appointment_id=appointment.id, service_id=service.id, activity_key="primary", activity_kind="gastroscopy", specialty_key="gastroenterology", primary_provider_id=provider.id, room_id=room.id, sequence=1, planned_start=now, planned_end=now + timedelta(minutes=30), status="completed", form_resolution_status="resolved")
    definition = ClinicalFormDefinition(form_key="pg-report-integrity", name="PG nalaz", specialty_key="gastroenterology", activity_kind="gastroscopy", active=True)
    pg_db.add_all([activity, definition]); pg_db.flush()
    version = ClinicalFormVersion(definition_id=definition.id, version=1, status="published", sections_json=[{"section_key": "main", "fields": [{"field_key": "finding", "label": "Nalaz", "type": "long_text"}]}], validation_schema_json={}, print_layout_json={}, output_document_type="gastroscopy_report")
    pg_db.add(version); pg_db.flush()
    instance = ClinicalFormInstance(activity_id=activity.id, form_version_id=version.id, purpose="clinical_report", status="signed", data_json={"finding": "Sintetički nalaz"}, rendered_summary="Nalaz: Sintetički nalaz", created_by=signer.id, last_edited_by=signer.id, completed_by=signer.id, signed_by=signer.id, completed_at=now, signed_at=now, binding_source="test", resolved_at=now)
    document = ClinicalDocument(patient_id=patient.id, clinic_id=room.clinic_id, source_type="generated_signed_report", document_type="gastroscopy_report", title="PG nalaz", raw_text="Nalaz: Sintetički nalaz", review_status="signed", physician_reviewed=True, reviewed_by=signer.id, reviewed_at=now, appointment_id=appointment.id, journey_id=journey.id, upload_channel="generated", lifecycle_status="reviewed", received_at=now)
    pg_db.add_all([instance, document]); pg_db.flush()
    report = SignedClinicalReport(form_instance_id=instance.id, form_version_id=version.id, clinical_document_id=document.id, activity_id=activity.id, journey_id=journey.id, patient_id=patient.id, document_type="gastroscopy_report", title="PG nalaz", structured_data_json=instance.data_json, rendered_content=instance.rendered_summary, version_number=1, signer_user_id=signer.id, signer_name=signer.full_name, signed_at=now, content_hash=report_digest(instance.rendered_summary, instance.data_json), hash_algorithm="sha256")
    pg_db.add(report); pg_db.flush()

    with pytest.raises(DBAPIError):
        with pg_db.begin_nested():
            pg_db.execute(text("UPDATE signed_clinical_reports SET rendered_content = 'nedopuštena izmjena' WHERE id = :id"), {"id": report.id})
    with pytest.raises(DBAPIError):
        with pg_db.begin_nested():
            pg_db.execute(text("DELETE FROM signed_clinical_reports WHERE id = :id"), {"id": report.id})
    pg_db.refresh(report)
    assert report.rendered_content == "Nalaz: Sintetički nalaz"

    original_data = dict(report.structured_data_json)
    original_signer = report.signer_name
    original_signed_at = report.signed_at
    instance.data_json = {"finding": "CHANGED_CONTENT"}
    instance.rendered_summary = "CHANGED_CONTENT"
    version.sections_json = [{"section_key": "changed", "fields": []}]
    version.print_layout_json = {"layout": "changed"}
    pg_db.commit()
    auth = {"Authorization": f"Bearer {login(pg_client, signer.email)}", "X-Clinic-Id": str(room.clinic_id)}

    preview = pg_client.get(f"/api/signed-reports/{report.id}", headers=auth)
    addendum = pg_client.post(
        f"/api/signed-reports/{report.id}/addenda",
        headers=auth,
        json={"reason": "PG naknadno pojašnjenje", "content": "Odvojena PG dopuna."},
    )
    listed = pg_client.get(f"/api/clinical-documents/{document.id}/addenda", headers=auth)

    assert preview.status_code == 200
    assert preview.json()["rendered_content"] == "Nalaz: Sintetički nalaz"
    assert preview.json()["structured_data_json"] == original_data
    assert "CHANGED_CONTENT" not in preview.json()["rendered_content"]
    assert preview.json()["signer_name"] == original_signer
    assert preview.json()["signed_at"] == original_signed_at.isoformat().replace("+00:00", "Z")
    assert addendum.status_code == 200
    assert addendum.json()["signed_report_id"] == report.id
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [addendum.json()["id"]]


def test_postgresql_institution_clinical_record_role_boundaries(pg_client, pg_db):
    institution = Institution(code="pg-nura", name="PG NURA", active=True)
    other_institution = Institution(code="pg-other", name="PG Other", active=True)
    clinic_a = Clinic(name="PG Gastro", institution_key="pg-nura", institution=institution)
    clinic_b = Clinic(name="PG Endoscopy", institution_key="pg-nura", institution=institution)
    other_clinic = Clinic(name="PG Foreign", institution_key="pg-other", institution=other_institution)
    patient = Patient(first_name="PG", last_name="Record")
    pg_db.add_all([institution, other_institution, clinic_a, clinic_b, other_clinic, patient])
    pg_db.flush()
    physician = create_institution_user(
        pg_db,
        "pg-physician-record@test.local",
        ["clinical.documents.read_institution", "clinical.documents.edit_own_draft", "documents.review"],
        clinic_a,
    )
    nurse = create_institution_user(pg_db, "pg-nurse-record@test.local", ["clinical.documents.read_institution"], clinic_b)
    other_physician = create_institution_user(
        pg_db,
        "pg-other-physician-record@test.local",
        ["clinical.documents.read_institution", "clinical.documents.edit_own_draft"],
        clinic_a,
    )
    administrator = create_institution_user(pg_db, "pg-admin-record@test.local", ["clinical.documents.read_institution"], clinic_a, "administrative_staff")
    foreign_physician = create_institution_user(pg_db, "pg-foreign-record@test.local", ["clinical.documents.read_institution"], other_clinic)
    clinical = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=clinic_b.id,
        source_type="external",
        document_type="gastroscopy",
        title="PG klinički nalaz",
        raw_text="Sintetički klinički tekst",
        review_status="reviewed",
        physician_reviewed=True,
        is_clinical_record=True,
        record_classification="clinical",
    )
    financial = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=clinic_b.id,
        source_type="uploaded",
        document_type="other",
        title="PG financijski prilog",
        review_status="reviewed",
        physician_reviewed=True,
        is_clinical_record=False,
        record_classification="financial",
    )
    own_draft = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=clinic_b.id,
        source_type="internal",
        document_type="consultation",
        title="PG vlastiti nacrt",
        raw_text="PG draft",
        review_status="draft",
        author_user_id=physician.id,
        is_clinical_record=True,
        record_classification="clinical",
    )
    legacy_draft = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=clinic_b.id,
        source_type="internal",
        document_type="consultation",
        title="PG legacy nacrt",
        raw_text="PG legacy draft",
        review_status="draft",
        author_user_id=None,
        is_clinical_record=True,
        record_classification="clinical",
    )
    unclassified = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=clinic_b.id,
        source_type="uploaded",
        document_type="other",
        title="PG izvor za klasifikaciju",
        raw_text="SADRŽAJ NE SMIJE U AUDIT",
        review_status="draft",
        is_clinical_record=False,
        record_classification="unclassified",
    )
    denied_unclassified = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=clinic_b.id,
        source_type="uploaded",
        document_type="other",
        title="PG izvor bez reviewer dozvole",
        raw_text="DRUGI SADRŽAJ NE SMIJE U AUDIT",
        review_status="draft",
        is_clinical_record=False,
        record_classification="unclassified",
    )
    pg_db.add_all([clinical, financial, own_draft, legacy_draft, unclassified, denied_unclassified])
    pg_db.commit()

    physician_headers = {"Authorization": f"Bearer {login(pg_client, physician.email)}"}
    nurse_headers = {"Authorization": f"Bearer {login(pg_client, nurse.email)}"}
    other_physician_headers = {"Authorization": f"Bearer {login(pg_client, other_physician.email)}"}
    admin_headers = {"Authorization": f"Bearer {login(pg_client, administrator.email)}"}
    foreign_headers = {"Authorization": f"Bearer {login(pg_client, foreign_physician.email)}"}

    assert pg_client.get(f"/api/clinical-documents/{clinical.id}", headers=physician_headers).status_code == 200
    assert pg_client.get(f"/api/clinical-documents/{clinical.id}", headers=nurse_headers).status_code == 200
    assert pg_client.get(f"/api/clinical-documents/{clinical.id}", headers=admin_headers).status_code == 403
    assert pg_client.get(f"/api/clinical-documents/{clinical.id}", headers=foreign_headers).status_code == 404
    assert pg_client.get(f"/api/clinical-documents/{financial.id}", headers=physician_headers).status_code == 403
    assert pg_client.patch(f"/api/clinical-documents/{own_draft.id}", headers=physician_headers, json={"title": "PG nacrt uredio autor"}).status_code == 200
    assert pg_client.patch(f"/api/clinical-documents/{own_draft.id}", headers=other_physician_headers, json={"title": "Nedopušten drugi autor"}).status_code == 403
    assert pg_client.patch(f"/api/clinical-documents/{own_draft.id}", headers=nurse_headers, json={"title": "Nedopuštena sestra"}).status_code == 403
    assert pg_client.patch(f"/api/clinical-documents/{legacy_draft.id}", headers=physician_headers, json={"title": "Nedopušten legacy edit"}).status_code == 403

    denied_classification = pg_client.post(
        f"/api/clinical-documents/{denied_unclassified.id}/classification/review",
        headers=admin_headers,
        json={"record_classification": "clinical"},
    )
    classified = pg_client.post(
        f"/api/clinical-documents/{unclassified.id}/classification/review",
        headers=physician_headers,
        json={"record_classification": "clinical"},
    )
    reclassified = pg_client.post(
        f"/api/clinical-documents/{unclassified.id}/classification/review",
        headers=physician_headers,
        json={"record_classification": "financial"},
    )

    assert denied_classification.status_code == 403
    assert classified.status_code == 200
    assert reclassified.status_code == 409
    classification_audit = pg_db.scalar(
        select(AuditLog).where(AuditLog.action == "document_classification_reviewed", AuditLog.entity_id == unclassified.id)
    )
    assert classification_audit.before_json["record_classification"] == "unclassified"
    assert classification_audit.after_json["record_classification"] == "clinical"
    assert "raw_text" not in classification_audit.before_json
    assert "raw_text" not in classification_audit.after_json

    assert pg_client.get("/api/invoices", headers=nurse_headers).status_code == 403
    assert pg_client.get("/api/dashboard/day?date=2026-07-21", headers=nurse_headers).status_code == 403

    physician.role.permissions = [
        item for item in physician.role.permissions if item.name != "clinical.documents.read_institution"
    ]
    pg_db.commit()
    assert pg_client.get(f"/api/clinical-documents/{clinical.id}", headers=physician_headers).status_code == 403


def test_api_permission_boundaries_and_api_key_actor(pg_client, pg_db):
    admin = create_user_with_permissions(pg_db, "admin-pg@test.local", ["admin.manage_users", "patients.write", "audit.read"])
    limited = create_user_with_permissions(pg_db, "limited-pg@test.local", ["patients.read"])
    pg_db.flush()
    admin_token = login(pg_client, admin.email)
    limited_token = login(pg_client, limited.email)

    unauthenticated = pg_client.get("/api/patients")
    denied_audit = pg_client.get("/api/audit-log", headers={"Authorization": f"Bearer {limited_token}"})
    api_key_response = pg_client.post(
        "/auth/api-keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "AI patient writer", "scopes": ["ai.patients.create"]},
    )

    assert unauthenticated.status_code == 401
    assert denied_audit.status_code == 403
    assert api_key_response.status_code == 200
    raw_key = api_key_response.json()["key"]
    stored_key = pg_db.get(ApiKey, api_key_response.json()["id"])
    assert "key_hash" not in api_key_response.json()
    assert stored_key.key_hash == hash_api_key(raw_key)

    forbidden_writeoff = pg_client.post(
        "/api/inventory/write-off",
        headers={"X-ASTRA-API-Key": raw_key},
        json={"inventory_item_id": 1, "quantity": 1, "movement_type": "write_off", "reason": "test"},
    )
    forbidden_adjustment = pg_client.post(
        "/api/inventory/adjustment",
        headers={"X-ASTRA-API-Key": raw_key},
        json={"inventory_item_id": 1, "quantity": 1, "movement_type": "adjustment", "reason": "test"},
    )
    forbidden_payment = pg_client.post(
        "/api/invoices/1/mark-paid",
        headers={"X-ASTRA-API-Key": raw_key},
        json={},
    )
    forbidden_audit = pg_client.get("/api/audit-log", headers={"X-ASTRA-API-Key": raw_key})
    allowed_ai_action = pg_client.post(
        "/api/ai/patients/create",
        headers={"X-ASTRA-API-Key": raw_key, "X-Request-ID": "quality-gate-api-key"},
        json={"first_name": "Key", "last_name": "Actor"},
    )

    assert forbidden_writeoff.status_code == 403
    assert forbidden_adjustment.status_code == 403
    assert forbidden_payment.status_code == 403
    assert forbidden_audit.status_code == 403
    assert allowed_ai_action.status_code == 200
    log = pg_db.query(AuditLog).filter(AuditLog.request_id == "quality-gate-api-key").one()
    assert log.actor_type == "api_key"
    assert log.actor_api_key_id == stored_key.id


def test_appointment_api_conflict_schedule_order_and_audit(pg_client, pg_db):
    user = create_user_with_permissions(pg_db, "appointments-pg@test.local", ["appointments.read", "appointments.write"])
    patient, provider, room, service = seed_clinic_objects(pg_db, user)
    token = login(pg_client, user.email)
    headers = {"Authorization": f"Bearer {token}", "X-Clinic-Id": str(room.clinic_id)}

    first = pg_client.post(
        "/api/appointments",
        headers=headers,
        json={"patient_id": patient.id, "provider_id": provider.id, "room_id": room.id, "service_id": service.id, "date": "2026-07-06", "start_time": "09:00", "end_time": "09:30", "duration_minutes": 30, "status": "scheduled", "source": "manual"},
    )
    later = pg_client.post(
        "/api/appointments",
        headers=headers,
        json={"patient_id": patient.id, "provider_id": provider.id, "room_id": room.id, "service_id": service.id, "date": "2026-07-06", "start_time": "10:00", "end_time": "10:30", "duration_minutes": 30, "status": "scheduled", "source": "manual"},
    )
    overlap = pg_client.post(
        "/api/appointments",
        headers=headers,
        json={"patient_id": patient.id, "provider_id": provider.id, "room_id": room.id, "service_id": service.id, "date": "2026-07-06", "start_time": "09:15", "end_time": "09:45", "duration_minutes": 30, "status": "scheduled", "source": "manual"},
    )
    schedule = pg_client.get("/api/schedule/day?date=2026-07-06", headers=headers)
    updated = pg_client.patch(f"/api/appointments/{first.json()['id']}", headers=headers, json={"status": "arrived"})
    # This legacy CRUD probe tests the appointment delete endpoint in isolation.
    # Canonical journeys intentionally protect their appointments from hard delete.
    pg_db.query(PatientJourney).filter(PatientJourney.appointment_id == later.json()["id"]).delete()
    pg_db.flush()
    deleted = pg_client.delete(f"/api/appointments/{later.json()['id']}", headers=headers)

    assert first.status_code == 200
    assert later.status_code == 200
    assert overlap.status_code == 409
    assert [item["start_time"] for item in schedule.json()] == ["09:00:00", "10:00:00"]
    assert updated.status_code == 200
    assert deleted.status_code == 200
    actions = [log.action for log in pg_db.query(AuditLog).filter(AuditLog.entity_type == "Appointment").all()]
    assert {"create", "update", "delete"}.issubset(set(actions))


def test_invoice_issue_uses_noop_fiscalization_and_audits(pg_client, pg_db):
    user = create_user_with_permissions(pg_db, "billing-pg@test.local", ["billing.read", "billing.write"])
    patient = Patient(first_name="Billing", last_name="Patient")
    invoice = Invoice(patient=patient, invoice_number="DRAFT-PG", status="draft", payment_status="unpaid", total_amount=Decimal("100"))
    line = InvoiceLine(invoice=invoice, description="Line", quantity=Decimal("1"), unit_price=Decimal("100"), total=Decimal("100"))
    pg_db.add_all([patient, invoice, line])
    pg_db.flush()
    token = login(pg_client, user.email)

    response = pg_client.post(f"/api/invoices/{invoice.id}/issue", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "issued"
    assert body["fiscalization_provider"] == "noop"
    assert body["fiscalization_status"] == "fiscalized"
    assert pg_db.query(AuditLog).filter(AuditLog.entity_type == "FiscalizationAttempt", AuditLog.entity_id == invoice.id).count() == 1
