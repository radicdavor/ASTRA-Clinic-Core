from datetime import date
from decimal import Decimal

from app.auth.dependencies import hash_api_key
from app.models.domain import ApiKey, AuditLog, InventoryBatch, InventoryItem, Invoice, InvoiceLine, StockLocation
from tests.conftest import login_token


def test_admin_can_access_inventory(client, auth_setup):
    token = login_token(client, "admin@test.local")

    response = client.get("/api/inventory/items", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_user_without_write_off_cannot_write_off_stock(client, db, auth_setup):
    token = login_token(client, "limited@test.local")
    item = InventoryItem(sku="DENY-WO", name="Deny writeoff")
    location = StockLocation(name="Deny location", type="main")
    db.add_all([item, location])
    db.flush()
    batch = InventoryBatch(inventory_item_id=item.id, location_id=location.id, quantity=Decimal("1"))
    db.add(batch)
    db.flush()

    response = client.post(
        "/api/inventory/write-off",
        headers={"Authorization": f"Bearer {token}"},
        json={"inventory_item_id": item.id, "batch_id": batch.id, "quantity": 1, "movement_type": "write_off", "reason": "test"},
    )

    assert response.status_code == 403


def test_user_without_billing_mark_paid_cannot_create_payment(client, db, auth_setup):
    token = login_token(client, "limited@test.local")
    invoice = Invoice(patient_id=1, invoice_number="ASTRA-TEST", status="issued", total_amount=Decimal("10"), payment_status="unpaid")
    line = InvoiceLine(invoice=invoice, description="Line", quantity=Decimal("1"), unit_price=Decimal("10"), total=Decimal("10"))
    db.add_all([invoice, line])
    db.flush()

    response = client.post(
        f"/api/invoices/{invoice.id}/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": 10, "method": "cash"},
    )

    assert response.status_code == 403


def test_ai_api_key_cannot_adjust_stock_or_pay_invoice(client, db, auth_setup):
    raw_key = "astra_test_key"
    db.add(ApiKey(name="AI", key_hash=hash_api_key(raw_key), scopes=["ai.appointments.create"], active=True))
    db.flush()

    stock_response = client.post(
        "/api/inventory/adjustment",
        headers={"X-ASTRA-API-Key": raw_key},
        json={"inventory_item_id": 1, "quantity": 1, "movement_type": "adjustment", "reason": "test"},
    )
    pay_response = client.post(
        "/api/invoices/1/payments",
        headers={"X-ASTRA-API-Key": raw_key},
        json={"amount": 1, "method": "cash"},
    )

    assert stock_response.status_code == 403
    assert pay_response.status_code == 403


def test_api_key_allowed_action_is_audited_as_api_key(client, db, auth_setup):
    raw_key = "astra_patient_key"
    api_key = ApiKey(name="AI patients", key_hash=hash_api_key(raw_key), scopes=["ai.patients.create"], active=True)
    db.add(api_key)
    db.flush()

    response = client.post(
        "/api/ai/patients/create",
        headers={"X-ASTRA-API-Key": raw_key},
        json={"first_name": "Api", "last_name": "Key", "date_of_birth": str(date(1990, 1, 1))},
    )

    assert response.status_code == 200
    assert any(log.actor_type == "api_key" and log.actor_api_key_id == api_key.id for log in db.query(AuditLog).all())
