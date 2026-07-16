from decimal import Decimal
from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import DBAPIError

from app.auth.dependencies import hash_api_key
from app.core.security import hash_password
from app.models.domain import ApiKey, Appointment, AuditLog, ClinicalDocument, ClinicalFormDefinition, ClinicalFormInstance, ClinicalFormVersion, Invoice, InvoiceLine, JourneyActivity, JourneyCheckIn, Patient, PatientJourney, Permission, Provider, Role, Room, Service, SignedClinicalReport, User
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


def login(client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "secret"})
    assert response.status_code == 200
    return response.json()["access_token"]


def seed_clinic_objects(db):
    patient = Patient(first_name="API", last_name="Patient")
    provider = Provider(full_name="dr. API", specialty="QA")
    room = Room(name="API Room", type="test")
    service = Service(name="API Service", duration_minutes=30, price=Decimal("100"))
    db.add_all([patient, provider, room, service])
    db.flush()
    return patient, provider, room, service


def test_postgresql_migrations_created_key_tables(pg_db):
    table_names = set(inspect(pg_db.bind).get_table_names())

    assert REQUIRED_TABLES.issubset(table_names)
    assert pg_db.scalar(select(JourneyCheckIn).limit(1)) is None


def test_postgresql_rejects_signed_report_content_update_and_delete(pg_db):
    signer = create_user_with_permissions(pg_db, "report-signer-pg@test.local", ["reports.read"])
    patient, provider, room, service = seed_clinic_objects(pg_db)
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
    document = ClinicalDocument(patient_id=patient.id, source_type="generated_signed_report", document_type="gastroscopy_report", title="PG nalaz", raw_text="Nalaz: Sintetički nalaz", review_status="signed", physician_reviewed=True, reviewed_by=signer.id, reviewed_at=now, appointment_id=appointment.id, journey_id=journey.id, upload_channel="generated", lifecycle_status="reviewed", received_at=now)
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
    patient, provider, room, service = seed_clinic_objects(pg_db)
    token = login(pg_client, user.email)
    headers = {"Authorization": f"Bearer {token}"}

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
