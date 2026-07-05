from app.models.domain import AuditLog
from tests.conftest import login_token
from tests.factories import appointment


def test_appointment_update_audit_contains_before_and_after(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    appt = appointment(db)

    response = client.patch(
        f"/api/appointments/{appt.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "arrived", "notes": "Pacijent stigao"},
    )

    assert response.status_code == 200
    log = db.query(AuditLog).filter(AuditLog.entity_type == "Appointment", AuditLog.entity_id == appt.id, AuditLog.action == "update").one()
    assert log.before_json["status"] == "scheduled"
    assert log.after_json["status"] == "arrived"
    assert log.after_json["notes"] == "Pacijent stigao"
