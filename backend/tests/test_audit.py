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


def test_sensitive_access_event_records_safe_payload(client, db, auth_setup):
    token = login_token(client, "admin@test.local")

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}", "X-Request-ID": "audit-access-patient"},
        json={
            "action": "patient.viewed",
            "entity_type": "Patient",
            "entity_id": 123,
            "surface": "patient_workspace",
            "clinic_id": auth_setup["clinic"].id,
            "journey_id": 456,
        },
    )

    assert response.status_code == 200
    log = db.query(AuditLog).filter(AuditLog.action == "patient.viewed").one()
    assert log.entity_type == "Patient"
    assert log.entity_id == 123
    assert log.request_id == "audit-access-patient"
    assert log.summary == "Sensitive access event: patient.viewed"
    assert log.after_json == {
        "surface": "patient_workspace",
        "clinic_id": auth_setup["clinic"].id,
        "journey_id": 456,
    }
    serialized = str(log.after_json) + str(log.summary)
    assert "Sintetički" not in serialized
    assert "Pacijent" not in serialized


def test_sensitive_access_event_rejects_mismatched_action_and_entity(client, db, auth_setup):
    token = login_token(client, "admin@test.local")

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "signed_report.viewed",
            "entity_type": "Patient",
            "entity_id": 123,
            "surface": "report_viewer",
        },
    )

    assert response.status_code == 422
    assert db.query(AuditLog).filter(AuditLog.action == "signed_report.viewed").count() == 0


def test_sensitive_access_event_requires_write_permission(client, db, auth_setup):
    token = login_token(client, "limited@test.local")

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "patient.viewed",
            "entity_type": "Patient",
            "entity_id": 123,
            "surface": "patient_workspace",
        },
    )

    assert response.status_code == 403


def test_audit_log_view_is_itself_audited(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    db.add(AuditLog(action="create", entity_type="Patient", entity_id=1, summary="Existing safe audit"))
    db.flush()

    response = client.get("/api/audit-log", headers={"Authorization": f"Bearer {token}", "X-Request-ID": "audit-log-opened"})

    assert response.status_code == 200
    log = db.query(AuditLog).filter(AuditLog.action == "audit_log.viewed").one()
    assert log.entity_type == "AuditLog"
    assert log.entity_id is None
    assert log.request_id == "audit-log-opened"
    assert log.after_json == {"surface": "audit_viewer", "clinic_id": None, "journey_id": None}
