from decimal import Decimal

from app.models.domain import ServiceMaterialTemplate, StockMovement
from tests.conftest import login_token
from tests.factories import appointment, service, stock_item_with_batch


def test_failed_completion_with_material_consumption_does_not_mutate_stock_or_appointment(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    svc = service(db, name="Gastroscopy with materials")
    enough_item, enough_batch, _ = stock_item_with_batch(db, sku="MAT-ENOUGH", quantity=Decimal("5"))
    low_item, low_batch, _ = stock_item_with_batch(db, sku="MAT-LOW", quantity=Decimal("1"))
    appt = appointment(db, service_obj=svc)
    db.add_all(
        [
            ServiceMaterialTemplate(service_id=svc.id, inventory_item_id=enough_item.id, default_quantity=Decimal("3"), required=True, variable_quantity_allowed=False),
            ServiceMaterialTemplate(service_id=svc.id, inventory_item_id=low_item.id, default_quantity=Decimal("3"), required=True, variable_quantity_allowed=False),
        ]
    )
    db.flush()

    response = client.post(
        f"/api/appointments/{appt.id}/complete-with-consumption",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 409
    assert enough_batch.quantity == Decimal("5")
    assert low_batch.quantity == Decimal("1")
    assert appt.status == "scheduled"
    assert db.query(StockMovement).count() == 0
