from decimal import Decimal

import pytest

from app.models.domain import AuditLog, InventoryBatch, InventoryItem, ServiceMaterialTemplate, StockMovement
from tests.integration.test_quality_gate_api import create_user_with_permissions, login, seed_clinic_objects


pytestmark = pytest.mark.integration


def test_full_pilot_demo_flow(pg_client, pg_db):
    user = create_user_with_permissions(
        pg_db,
        "pilot-pg@test.local",
        [
            "patients.read",
            "appointments.read",
            "appointments.write",
            "inventory.read",
            "inventory.write",
            "billing.read",
            "billing.write",
            "billing.mark_paid",
            "procurement.read",
            "procurement.write",
            "audit.read",
        ],
    )
    patient, provider, room, service = seed_clinic_objects(pg_db)
    item = InventoryItem(sku="PILOT-MAT", name="Pilot material", current_stock=Decimal("5"), reorder_point=Decimal("2"), minimum_stock=Decimal("2"), purchase_price=Decimal("5"))
    pg_db.add(item)
    pg_db.flush()
    location_response_seed = pg_client.get("/api/inventory/stock-locations", headers={"Authorization": f"Bearer {login(pg_client, user.email)}"})
    token = login(pg_client, user.email)
    headers = {"Authorization": f"Bearer {token}", "X-Request-ID": "pilot-demo-flow"}
    location = None
    if location_response_seed.json():
        location = location_response_seed.json()[0]
    else:
        from app.models.domain import StockLocation

        loc = StockLocation(name="Pilot skladiste", type="main")
        pg_db.add(loc)
        pg_db.flush()
        location = {"id": loc.id}
    pg_db.add(InventoryBatch(inventory_item_id=item.id, quantity=Decimal("5"), location_id=location["id"], purchase_price=Decimal("5")))
    pg_db.add(ServiceMaterialTemplate(service_id=service.id, inventory_item_id=item.id, default_quantity=Decimal("1"), required=True, variable_quantity_allowed=False))
    pg_db.flush()

    appointment = pg_client.post(
        "/api/appointments",
        headers=headers,
        json={"patient_id": patient.id, "provider_id": provider.id, "room_id": room.id, "service_id": service.id, "date": "2026-07-05", "start_time": "11:00", "end_time": "11:30", "duration_minutes": 30, "status": "scheduled", "source": "manual"},
    )
    assert appointment.status_code == 200
    appointment_id = appointment.json()["id"]

    completed = pg_client.post(f"/api/appointments/{appointment_id}/complete-with-consumption", headers=headers, json={})
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert pg_db.get(InventoryItem, item.id).current_stock == Decimal("4.00")
    assert pg_db.query(StockMovement).filter(StockMovement.related_appointment_id == appointment_id).count() == 1

    draft_invoice = pg_client.post(f"/api/appointments/{appointment_id}/draft-invoice", headers=headers)
    assert draft_invoice.status_code == 200
    invoice_id = draft_invoice.json()["id"]

    issued = pg_client.post(f"/api/invoices/{invoice_id}/issue", headers=headers)
    assert issued.status_code == 200
    assert issued.json()["status"] == "issued"
    assert issued.json()["fiscalization_provider"] == "noop"

    payment = pg_client.post(f"/api/invoices/{invoice_id}/payments", headers=headers, json={"amount": "100", "method": "cash"})
    assert payment.status_code == 200
    invoice_after_payment = pg_client.get(f"/api/invoices/{invoice_id}", headers=headers)
    assert invoice_after_payment.json()["payment_status"] in {"paid", "partially_paid"}

    supplier = pg_client.post("/api/suppliers", headers=headers, json={"name": "Pilot dobavljac"})
    assert supplier.status_code == 200
    order = pg_client.post("/api/purchase-orders", headers=headers, json={"supplier_id": supplier.json()["id"], "status": "ordered"})
    assert order.status_code == 200
    line = pg_client.post(f"/api/purchase-orders/{order.json()['id']}/lines", headers=headers, json={"inventory_item_id": item.id, "quantity_ordered": "3", "unit_price": "5"})
    assert line.status_code == 200
    receive = pg_client.post(
        f"/api/purchase-orders/{order.json()['id']}/receive",
        headers=headers,
        json={"lines": [{"purchase_order_line_id": line.json()["id"], "quantity_received": "3", "location_id": location["id"], "purchase_price": "5"}]},
    )
    assert receive.status_code == 200
    assert pg_db.get(InventoryItem, item.id).current_stock == Decimal("7.00")

    assert pg_db.query(AuditLog).filter(AuditLog.request_id == "pilot-demo-flow").count() >= 6
