from app.models.domain import AuditLog, Clinic, ClinicalDocument, Patient, PatientClinicAssociation
from tests.conftest import login_token
from tests.factories import appointment


def scoped_patient(db, auth_setup, first_name="Audit", last_name="Patient"):
    item = Patient(first_name=first_name, last_name=last_name)
    db.add(item)
    db.flush()
    db.add(PatientClinicAssociation(patient_id=item.id, clinic_id=auth_setup["clinic"].id, created_by_user_id=auth_setup["admin"].id))
    db.flush()
    return item


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
    patient = scoped_patient(db, auth_setup)

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}", "X-Request-ID": "audit-access-patient"},
        json={
            "action": "patient.viewed",
            "entity_type": "Patient",
            "entity_id": patient.id,
            "surface": "patient_workspace",
            "interaction_id": "patient-open-001",
        },
    )

    assert response.status_code == 200
    log = db.query(AuditLog).filter(AuditLog.action == "patient.viewed").one()
    assert log.entity_type == "Patient"
    assert log.entity_id == patient.id
    assert log.actor_user_id == auth_setup["admin"].id
    assert log.request_id == "audit-access-patient"
    assert log.summary == "Sensitive access event: patient.viewed"
    assert log.after_json == {
        "surface": "patient_workspace",
        "clinic_id": auth_setup["clinic"].id,
        "interaction_id": "patient-open-001",
    }
    serialized = str(log.after_json) + str(log.summary)
    assert "Sinteticki" not in serialized
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


def test_sensitive_access_event_rejects_unknown_action_code(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    patient = scoped_patient(db, auth_setup)

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "patient.secretly_exported",
            "entity_type": "Patient",
            "entity_id": patient.id,
            "surface": "patient_workspace",
        },
    )

    assert response.status_code == 422


def test_sensitive_access_event_rejects_spoofed_actor_clinic_and_metadata(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    patient = scoped_patient(db, auth_setup)

    for forbidden_payload in [
        {"actor_user_id": 999},
        {"clinic_id": 999},
        {"metadata": {"patient_name": "PHI"}},
        {"patient_name": "PHI"},
        {"event_timestamp": "2026-07-21T08:00:00Z"},
    ]:
        response = client.post(
            "/api/audit/access-events",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "action": "patient.viewed",
                "entity_type": "Patient",
                "entity_id": patient.id,
                "surface": "patient_workspace",
                **forbidden_payload,
            },
        )
        assert response.status_code == 422

    assert db.query(AuditLog).filter(AuditLog.action == "patient.viewed").count() == 0


def test_sensitive_access_event_rejects_cross_clinic_object_without_disclosure(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    other_clinic = Clinic(name="Audit Other Clinic")
    patient = Patient(first_name="Other", last_name="Clinic")
    db.add_all([other_clinic, patient])
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=other_clinic.id))
    db.flush()

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "patient.viewed",
            "entity_type": "Patient",
            "entity_id": patient.id,
            "surface": "patient_workspace",
        },
    )

    assert response.status_code == 404
    assert db.query(AuditLog).filter(AuditLog.action == "patient.viewed").count() == 0


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


def test_sensitive_access_event_deduplicates_interaction_id(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    patient = scoped_patient(db, auth_setup)
    payload = {
        "action": "patient.viewed",
        "entity_type": "Patient",
        "entity_id": patient.id,
        "surface": "patient_workspace",
        "interaction_id": "duplicate-open-001",
    }

    first = client.post("/api/audit/access-events", headers={"Authorization": f"Bearer {token}"}, json=payload)
    second = client.post("/api/audit/access-events", headers={"Authorization": f"Bearer {token}"}, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert db.query(AuditLog).filter(AuditLog.action == "patient.viewed").count() == 1


def test_source_document_access_event_requires_scoped_document(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    patient = scoped_patient(db, auth_setup)
    document = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=auth_setup["clinic"].id,
        institution_id=auth_setup["clinic"].institution_id,
        source_type="uploaded",
        document_type="laboratory",
        title="Synthetic source",
        review_status="reviewed",
    )
    db.add(document)
    db.flush()

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "source_document.downloaded",
            "entity_type": "ClinicalDocument",
            "entity_id": document.id,
            "surface": "document_center",
        },
    )

    assert response.status_code == 200
    log = db.query(AuditLog).filter(AuditLog.action == "source_document.downloaded").one()
    assert log.entity_id == document.id
    assert log.after_json["clinic_id"] == auth_setup["clinic"].id


def test_direct_patient_export_access_event_is_rejected_without_export_workflow(client, db, auth_setup):
    token = login_token(client, "admin@test.local")

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "patient_export.created",
            "entity_type": "PatientExport",
            "entity_id": 1,
            "surface": "patient_workspace",
        },
    )

    assert response.status_code == 409


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
    assert log.after_json == {"surface": "audit_viewer", "clinic_id": auth_setup["clinic"].id, "interaction_id": None}


def test_audit_log_view_does_not_recursively_audit_itself(client, db, auth_setup):
    token = login_token(client, "admin@test.local")

    first = client.get("/api/audit-log", headers={"Authorization": f"Bearer {token}"})
    second = client.get("/api/audit-log", headers={"Authorization": f"Bearer {token}"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert db.query(AuditLog).filter(AuditLog.action == "audit_log.viewed").count() == 2
