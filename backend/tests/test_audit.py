from starlette.requests import Request

from app.audit.service import audit, resolved_client_ip
from app.core.config import Settings
from app.models.domain import AuditLog, Clinic, ClinicalDocument, Institution, Patient, PatientClinicAssociation
from tests.conftest import login_token
from tests.factories import appointment


def request_with_client(peer: str, headers: dict[str, str] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()],
            "client": (peer, 12345),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )


def test_trusted_proxy_preserves_valid_originating_client_ip(monkeypatch):
    settings = Settings(app_env="test", trusted_proxy_networks="172.30.0.0/24")
    monkeypatch.setattr("app.audit.service.get_settings", lambda: settings)
    request = request_with_client(
        "172.30.0.12",
        {"X-Real-IP": "203.0.113.25", "X-Forwarded-For": "203.0.113.25"},
    )

    assert resolved_client_ip(request) == "203.0.113.25"


def test_trusted_proxy_uses_first_address_in_documented_forwarded_chain(monkeypatch):
    settings = Settings(app_env="test", trusted_proxy_networks="172.30.0.0/24")
    monkeypatch.setattr("app.audit.service.get_settings", lambda: settings)
    request = request_with_client(
        "172.30.0.12",
        {"X-Forwarded-For": "203.0.113.25, 198.51.100.40"},
    )

    assert resolved_client_ip(request) == "203.0.113.25"


def test_untrusted_peer_cannot_spoof_audit_client_ip(monkeypatch):
    settings = Settings(app_env="test", trusted_proxy_networks="172.30.0.0/24")
    monkeypatch.setattr("app.audit.service.get_settings", lambda: settings)
    request = request_with_client(
        "198.51.100.8",
        {"X-Real-IP": "203.0.113.25", "X-Forwarded-For": "203.0.113.25"},
    )

    assert resolved_client_ip(request) == "198.51.100.8"


def test_trusted_proxy_invalid_forwarded_ip_falls_back_to_peer(monkeypatch):
    settings = Settings(app_env="test", trusted_proxy_networks="172.30.0.0/24")
    monkeypatch.setattr("app.audit.service.get_settings", lambda: settings)
    request = request_with_client("172.30.0.12", {"X-Real-IP": "not-an-ip"})

    assert resolved_client_ip(request) == "172.30.0.12"


def test_audit_record_persists_resolved_trusted_proxy_client_ip(db, monkeypatch):
    settings = Settings(app_env="test", trusted_proxy_networks="172.30.0.0/24")
    monkeypatch.setattr("app.audit.service.get_settings", lambda: settings)
    request = request_with_client("172.30.0.12", {"X-Real-IP": "203.0.113.25"})

    event = audit(db, "proxy_test", "System", request=request)
    db.flush()

    assert event.ip_address == "203.0.113.25"


def test_production_proxy_configuration_rejects_global_trust():
    settings = Settings(
        app_env="production",
        trusted_proxy_networks="0.0.0.0/0",
    )

    assert "Production TRUSTED_PROXY_NETWORKS must not trust every client address." in settings.production_safety_errors()


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
    assert "notes" not in log.after_json
    assert log.scope_type == "clinic"
    assert log.clinic_id == auth_setup["clinic"].id


def test_client_cannot_assert_authoritative_sensitive_access(client, db, auth_setup):
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

    assert response.status_code == 409
    assert db.query(AuditLog).filter(AuditLog.action == "patient.viewed").count() == 0


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

    assert response.status_code == 409
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


def test_unique_client_interaction_ids_cannot_multiply_authoritative_events(client, db, auth_setup):
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
    payload["interaction_id"] = "different-open-002"
    second = client.post("/api/audit/access-events", headers={"Authorization": f"Bearer {token}"}, json=payload)

    assert first.status_code == second.status_code == 409
    assert db.query(AuditLog).filter(AuditLog.action == "patient.viewed").count() == 0


def test_client_cannot_assert_source_document_download(client, db, auth_setup):
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

    assert response.status_code == 409
    assert db.query(AuditLog).filter(AuditLog.action == "source_document.downloaded").count() == 0


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
    assert log.after_json == {"surface": "audit_viewer", "clinic_id": auth_setup["clinic"].id}
    assert log.scope_type == "clinic"
    assert log.clinic_id == auth_setup["clinic"].id


def test_audit_log_returns_only_safe_active_clinic_projection(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    local = AuditLog(
        scope_type="clinic",
        clinic_id=auth_setup["clinic"].id,
        institution_id=auth_setup["clinic"].institution_id,
        action="update",
        entity_type="ClinicalDocument",
        entity_id=11,
        summary="AUDIT_PHI_SENTINEL",
        before_json={"status": "draft", "raw_text": "AUDIT_PHI_SENTINEL"},
        after_json={"status": "reviewed", "token": "AUDIT_TOKEN_SENTINEL"},
    )
    foreign_clinic = Clinic(name="Foreign audit clinic")
    db.add(foreign_clinic)
    db.flush()
    foreign = AuditLog(
        scope_type="clinic",
        clinic_id=foreign_clinic.id,
        action="update",
        entity_type="ClinicalDocument",
        entity_id=12,
        after_json={"report_content": "AUDIT_REPORT_SENTINEL"},
    )
    system = AuditLog(
        scope_type="system_security",
        action="auth.invalid_session",
        entity_type="user_session",
        after_json={"reason_code": "AUDIT_SECURITY_SENTINEL"},
    )
    legacy = AuditLog(action="legacy", entity_type="Patient", summary="AUDIT_LEGACY_SENTINEL")
    db.add_all([local, foreign, system, legacy])
    db.flush()

    response = client.get("/api/audit-log", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [local.id]
    assert body[0]["changed_fields"] == ["raw_text", "status", "token"]
    assert body[0]["status"] == "reviewed"
    assert "before_json" not in body[0]
    assert "after_json" not in body[0]
    assert "summary" not in body[0]
    serialized = response.text
    for sentinel in (
        "AUDIT_PHI_SENTINEL",
        "AUDIT_TOKEN_SENTINEL",
        "AUDIT_REPORT_SENTINEL",
        "AUDIT_SECURITY_SENTINEL",
        "AUDIT_LEGACY_SENTINEL",
    ):
        assert sentinel not in serialized


def test_audit_log_view_does_not_recursively_audit_itself(client, db, auth_setup):
    token = login_token(client, "admin@test.local")

    first = client.get("/api/audit-log", headers={"Authorization": f"Bearer {token}"})
    second = client.get("/api/audit-log", headers={"Authorization": f"Bearer {token}"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert db.query(AuditLog).filter(AuditLog.action == "audit_log.viewed").count() == 2


def test_direct_audit_reference_is_not_an_authoritative_access_path(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    local = AuditLog(
        scope_type="clinic",
        clinic_id=auth_setup["clinic"].id,
        institution_id=auth_setup["clinic"].institution_id,
        action="update",
        entity_type="Appointment",
        entity_id=11,
    )
    foreign_clinic = Clinic(name="Foreign direct audit reference")
    db.add_all([local, foreign_clinic])
    db.flush()
    foreign = AuditLog(scope_type="clinic", clinic_id=foreign_clinic.id, action="update", entity_type="Appointment", entity_id=12)
    db.add(foreign)
    db.flush()

    def record(entity_id):
        return client.post(
            "/api/audit/access-events",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "audit_log.viewed", "entity_type": "AuditLog", "entity_id": entity_id, "surface": "audit_viewer"},
        )

    allowed = record(local.id)
    forbidden = record(foreign.id)
    missing = record(999999)

    assert allowed.status_code == forbidden.status_code == missing.status_code == 409
    assert forbidden.json() == missing.json()


def test_direct_system_audit_reference_requires_explicit_system_permission(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    system_event = AuditLog(scope_type="system_security", action="auth.browser_session_invalid", entity_type="user_session")
    db.add(system_event)
    db.flush()
    auth_setup["admin"].role.permissions = [
        permission for permission in auth_setup["admin"].role.permissions if permission.name != "system.admin"
    ]
    db.flush()

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "audit_log.viewed", "entity_type": "AuditLog", "entity_id": system_event.id, "surface": "audit_viewer"},
    )

    assert response.status_code == 409


def test_direct_institution_audit_reference_requires_matching_medical_scope(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    foreign_institution = Institution(code="audit-foreign", name="Foreign audit institution")
    local = AuditLog(
        scope_type="institution_clinical",
        institution_id=auth_setup["clinic"].institution_id,
        action="clinical_document_reviewed",
        entity_type="ClinicalDocument",
        entity_id=21,
    )
    foreign = AuditLog(
        scope_type="institution_clinical",
        action="clinical_document_reviewed",
        entity_type="ClinicalDocument",
        entity_id=22,
    )
    db.add_all([foreign_institution, local])
    db.flush()
    foreign.institution_id = foreign_institution.id
    db.add(foreign)
    db.flush()

    def record(entity_id):
        return client.post(
            "/api/audit/access-events",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "audit_log.viewed", "entity_type": "AuditLog", "entity_id": entity_id, "surface": "audit_viewer"},
        )

    assert record(local.id).status_code == 409
    foreign_response = record(foreign.id)
    missing_response = record(foreign.id + 1_000_000)
    assert foreign_response.status_code == missing_response.status_code == 409
    assert foreign_response.json() == missing_response.json()


def test_direct_sensitive_access_does_not_call_authoritative_audit_writer(client, db, auth_setup, monkeypatch):
    token = login_token(client, "admin@test.local")
    patient = scoped_patient(db, auth_setup, first_name="Exact", last_name="Event")

    def unexpected_audit(*args, **kwargs):
        raise AssertionError("Direct endpoint must not call authoritative audit writer")

    monkeypatch.setattr("app.services.audit_access.audit", unexpected_audit)
    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "patient.viewed", "entity_type": "Patient", "entity_id": patient.id, "surface": "patient_workspace"},
    )

    assert response.status_code == 409
