from decimal import Decimal

import pytest
from sqlalchemy import inspect

from app.auth.dependencies import hash_api_key
from app.core.security import hash_password
from app.models.domain import ApiKey, AuditLog, Invoice, InvoiceLine, Patient, Permission, Provider, Role, Room, Service, User


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
    allowed_ai_action = pg_client.post(
        "/api/ai/patients/create",
        headers={"X-ASTRA-API-Key": raw_key, "X-Request-ID": "quality-gate-api-key"},
        json={"first_name": "Key", "last_name": "Actor"},
    )

    assert forbidden_writeoff.status_code == 403
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
        json={"patient_id": patient.id, "provider_id": provider.id, "room_id": room.id, "service_id": service.id, "date": "2026-07-05", "start_time": "09:00", "end_time": "09:30", "duration_minutes": 30, "status": "scheduled", "source": "manual"},
    )
    later = pg_client.post(
        "/api/appointments",
        headers=headers,
        json={"patient_id": patient.id, "provider_id": provider.id, "room_id": room.id, "service_id": service.id, "date": "2026-07-05", "start_time": "10:00", "end_time": "10:30", "duration_minutes": 30, "status": "scheduled", "source": "manual"},
    )
    overlap = pg_client.post(
        "/api/appointments",
        headers=headers,
        json={"patient_id": patient.id, "provider_id": provider.id, "room_id": room.id, "service_id": service.id, "date": "2026-07-05", "start_time": "09:15", "end_time": "09:45", "duration_minutes": 30, "status": "scheduled", "source": "manual"},
    )
    schedule = pg_client.get("/api/schedule/day?date=2026-07-05", headers=headers)
    updated = pg_client.patch(f"/api/appointments/{first.json()['id']}", headers=headers, json={"status": "arrived"})
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
