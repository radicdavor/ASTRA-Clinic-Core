import pytest

import app.services.clinical_readiness_acknowledgments as acknowledgment_service
from app.auth.dependencies import hash_api_key
from app.models.domain import (
    ApiKey,
    Appointment,
    AuditLog,
    ClinicalEpisode,
    ClinicalPlan,
    ClinicalReadinessReviewAcknowledgment,
    ClinicalReadinessSnapshot,
    Permission,
)
from app.services.clinical_readiness_acknowledgments import (
    CLINICAL_READINESS_ACKNOWLEDGED_EVENT,
    CLINICAL_READINESS_ACKNOWLEDGMENT_READ_DENIED_EVENT,
    create_clinical_readiness_review_acknowledgment,
)
from app.services.clinical_readiness_snapshots import capture_clinical_readiness_snapshot
from tests.factories import appointment, patient, provider, room, service


ADVISORY_SIGNAL_KEY = "no_reviewed_clinical_documents"


def create_acknowledgment(db, auth_setup, appt, **overrides):
    payload = {
        "appointment_id": appt.id,
        "patient_id": appt.patient_id,
        "advisory_signal_key": ADVISORY_SIGNAL_KEY,
        "actor_user_id": auth_setup["admin"].id,
        "actor_role": "physician",
        "reason": "Human reviewed advisory signal.",
    }
    payload.update(overrides)
    return create_clinical_readiness_review_acknowledgment(db, **payload)


def acknowledgment_list_endpoint(client, appointment_id, headers):
    return client.get(
        f"/api/appointments/{appointment_id}/clinical-readiness/acknowledgments",
        headers=headers,
    )


def acknowledgment_detail_endpoint(client, appointment_id, acknowledgment_id, headers):
    return client.get(
        f"/api/appointments/{appointment_id}/clinical-readiness/acknowledgments/{acknowledgment_id}",
        headers=headers,
    )


def auth_headers(client):
    from tests.conftest import login_token

    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def denied_read_events(db):
    return db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_ACKNOWLEDGMENT_READ_DENIED_EVENT).all()


def test_internal_acknowledgment_service_requires_reason(db, auth_setup):
    appt = appointment(db)

    with pytest.raises(ValueError, match="Razlog pregleda signala je obavezan"):
        create_acknowledgment(db, auth_setup, appt, reason="   ")

    assert db.query(ClinicalReadinessReviewAcknowledgment).count() == 0
    assert db.query(AuditLog).count() == 0


def test_internal_acknowledgment_service_requires_actor(db, auth_setup):
    appt = appointment(db)

    with pytest.raises(ValueError, match="Actor user id je obavezan"):
        create_acknowledgment(db, auth_setup, appt, actor_user_id=None)

    assert db.query(ClinicalReadinessReviewAcknowledgment).count() == 0
    assert db.query(AuditLog).count() == 0


@pytest.mark.parametrize("actor_role", ["api_key", "system", "system_job", "ai_agent"])
def test_internal_acknowledgment_service_denies_non_human_actor_roles(db, auth_setup, actor_role):
    appt = appointment(db)

    with pytest.raises(PermissionError, match="Acknowledgment zahtijeva prijavljenog korisnika"):
        create_acknowledgment(db, auth_setup, appt, actor_role=actor_role)

    assert db.query(ClinicalReadinessReviewAcknowledgment).count() == 0
    assert db.query(AuditLog).count() == 0


def test_internal_acknowledgment_service_checks_appointment_patient_scope(db, auth_setup):
    appt = appointment(db)
    other_patient = patient(db, first_name="Other", last_name="Patient")

    with pytest.raises(ValueError, match="Termin ne pripada navedenom pacijentu"):
        create_acknowledgment(db, auth_setup, appt, patient_id=other_patient.id)

    assert db.query(ClinicalReadinessReviewAcknowledgment).count() == 0
    assert db.query(AuditLog).count() == 0


def test_internal_acknowledgment_service_checks_advisory_signal_key(db, auth_setup):
    appt = appointment(db)

    with pytest.raises(ValueError, match="Advisory signal nije prepoznat"):
        create_acknowledgment(db, auth_setup, appt, advisory_signal_key="unknown_signal")

    assert db.query(ClinicalReadinessReviewAcknowledgment).count() == 0
    assert db.query(AuditLog).count() == 0


def test_internal_acknowledgment_service_checks_optional_snapshot_scope(db, auth_setup):
    appt = appointment(db)
    other_appt = appointment(
        db,
        provider_obj=provider(db, name="dr. Other"),
        room_obj=room(db, name="Room other"),
        service_obj=service(db, name="Other service"),
    )
    other_snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=other_appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Snapshot for other appointment.",
    )

    with pytest.raises(ValueError, match="Snapshot ne pripada ovom terminu"):
        create_acknowledgment(db, auth_setup, appt, snapshot_id=other_snapshot.id)

    assert db.query(ClinicalReadinessReviewAcknowledgment).count() == 0


def test_internal_acknowledgment_service_inserts_row_and_audit(db, auth_setup):
    appt = appointment(db)
    snapshot = capture_clinical_readiness_snapshot(
        db,
        appointment_id=appt.id,
        actor_user_id=auth_setup["admin"].id,
        reason="Snapshot context.",
    )

    acknowledgment = create_acknowledgment(db, auth_setup, appt, snapshot_id=snapshot.id)

    assert acknowledgment.id is not None
    assert acknowledgment.appointment_id == appt.id
    assert acknowledgment.patient_id == appt.patient_id
    assert acknowledgment.snapshot_id == snapshot.id
    assert acknowledgment.advisory_signal_key == ADVISORY_SIGNAL_KEY
    assert acknowledgment.actor_user_id == auth_setup["admin"].id
    assert acknowledgment.actor_role == "physician"
    assert acknowledgment.reason == "Human reviewed advisory signal."
    assert acknowledgment.is_decision is False
    assert acknowledgment.is_clearance is False
    assert acknowledgment.is_override is False

    event = db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_ACKNOWLEDGED_EVENT).one()
    assert event.entity_type == "ClinicalReadinessReviewAcknowledgment"
    assert event.entity_id == acknowledgment.id
    assert event.actor_user_id == auth_setup["admin"].id
    assert event.after_json["acknowledgment_id"] == acknowledgment.id
    assert event.after_json["appointment_id"] == appt.id
    assert event.after_json["patient_id"] == appt.patient_id
    assert event.after_json["snapshot_id"] == snapshot.id
    assert event.after_json["advisory_signal_key"] == ADVISORY_SIGNAL_KEY
    assert event.after_json["reason"] == "Human reviewed advisory signal."
    assert event.after_json["is_decision"] is False
    assert event.after_json["is_clearance"] is False
    assert event.after_json["is_override"] is False


def test_internal_acknowledgment_audit_failure_rolls_back_insert(db, auth_setup, monkeypatch):
    appt = appointment(db)

    def fail_audit(*args, **kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(acknowledgment_service, "audit", fail_audit)

    with pytest.raises(RuntimeError, match="audit unavailable"):
        create_acknowledgment(db, auth_setup, appt)

    assert db.query(ClinicalReadinessReviewAcknowledgment).count() == 0
    assert db.query(AuditLog).filter(AuditLog.action == CLINICAL_READINESS_ACKNOWLEDGED_EVENT).count() == 0


def test_internal_acknowledgment_db_failure_does_not_write_audit(db, auth_setup, monkeypatch):
    appt = appointment(db)
    audit_calls = []

    def spy_audit(*args, **kwargs):
        audit_calls.append((args, kwargs))

    def fail_flush(*args, **kwargs):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(acknowledgment_service, "audit", spy_audit)
    monkeypatch.setattr(db, "flush", fail_flush)

    with pytest.raises(RuntimeError, match="db unavailable"):
        create_acknowledgment(db, auth_setup, appt)

    assert audit_calls == []


def test_internal_acknowledgment_has_no_workflow_side_effects(db, auth_setup):
    appt = appointment(db, status="scheduled")
    original_status = appt.status
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()
    snapshot_count = db.query(ClinicalReadinessSnapshot).count()

    create_acknowledgment(db, auth_setup, appt)
    db.expire(appt)

    assert appt.status == original_status
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert db.query(ClinicalReadinessSnapshot).count() == snapshot_count

    table_names = set(db.get_bind().dialect.get_table_names(db.connection()))
    assert "tasks" not in table_names
    assert "outcome_evidence" not in table_names
    assert "patient_messages" not in table_names


def test_acknowledgment_write_runtime_surface_still_absent(client):
    route_paths = {route.path for route in client.app.routes}

    assert "/api/clinical-readiness-review-acknowledgments" not in route_paths
    assert "/api/appointments/{appointment_id}/clinical-readiness-review-acknowledgments" not in route_paths
    assert "/api/appointments/{appointment_id}/clinical-readiness/acknowledgments" in route_paths
    assert "/api/appointments/{appointment_id}/clinical-readiness/acknowledgments/{acknowledgment_id}" in route_paths
    write_methods = {"POST", "PATCH", "PUT", "DELETE"}
    for route in client.app.routes:
        if "acknowledgment" in route.path:
            assert write_methods.isdisjoint(getattr(route, "methods", set()))


def test_acknowledgment_runtime_write_permission_seed_still_absent(db):
    forbidden_permissions = {
        "clinical_readiness.acknowledgments.write",
        "clinical_readiness.acknowledgments.manage",
    }

    seeded_permissions = {name for (name,) in db.query(Permission.name).all()}

    assert forbidden_permissions.isdisjoint(seeded_permissions)


def test_acknowledgment_read_list_requires_auth(client, db):
    appt = appointment(db)

    response = acknowledgment_list_endpoint(client, appt.id, headers={})

    assert response.status_code == 401


def test_acknowledgment_read_list_requires_read_permission(client, db, auth_setup):
    appt = appointment(db)
    from tests.conftest import login_token

    token = login_token(client, "limited@test.local")
    response = acknowledgment_list_endpoint(client, appt.id, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_acknowledgment_read_list_returns_empty_state(client, db, auth_setup):
    appt = appointment(db)

    response = acknowledgment_list_endpoint(client, appt.id, auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["appointment_id"] == appt.id
    assert body["acknowledgments"] == []
    assert body["count"] == 0
    assert body["is_read_only"] is True
    assert "ne predstavlja clinical approval" in body["warning"].lower()


def test_acknowledgment_read_list_returns_newest_first_and_writes_no_audit(client, db, auth_setup):
    appt = appointment(db)
    first = create_acknowledgment(db, auth_setup, appt, reason="First review.")
    second = create_acknowledgment(db, auth_setup, appt, reason="Second review.")
    audit_count = db.query(AuditLog).count()

    response = acknowledgment_list_endpoint(client, appt.id, auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [item["id"] for item in body["acknowledgments"]] == [second.id, first.id]
    assert body["acknowledgments"][0]["acknowledgment_key"] == f"ack-{second.id}"
    assert body["acknowledgments"][0]["is_decision"] is False
    assert body["acknowledgments"][0]["is_clearance"] is False
    assert body["acknowledgments"][0]["is_override"] is False
    assert db.query(AuditLog).count() == audit_count


def test_acknowledgment_detail_is_appointment_scoped_and_read_only(client, db, auth_setup):
    appt = appointment(db, status="scheduled")
    original_status = appt.status
    acknowledgment = create_acknowledgment(db, auth_setup, appt)
    audit_count = db.query(AuditLog).count()

    response = acknowledgment_detail_endpoint(client, appt.id, acknowledgment.id, auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == acknowledgment.id
    assert body["appointment_id"] == appt.id
    assert body["patient_id"] == appt.patient_id
    assert body["reason"] == "Human reviewed advisory signal."
    assert "ne predstavlja clinical approval" in body["warning"].lower()
    assert "approval_status" not in body
    assert "clearance_status" not in body
    assert "override_status" not in body
    assert "outcome_evidence_id" not in body
    db.expire(appt)
    assert appt.status == original_status
    assert db.query(AuditLog).count() == audit_count


def test_acknowledgment_permission_denied_read_writes_single_audit(client, db, auth_setup):
    from tests.conftest import login_token

    appt = appointment(db)
    db.commit()
    token = login_token(client, "limited@test.local")
    denied_count = len(denied_read_events(db))

    permission_response = acknowledgment_list_endpoint(
        client,
        appt.id,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert permission_response.status_code == 403
    events = denied_read_events(db)
    assert len(events) == denied_count + 1
    payload = events[-1].after_json
    assert payload["denial_category"] == "missing_permission"
    assert payload["access_type"] == "list"
    assert payload["appointment_id"] == appt.id
    assert payload["actor_type"] == "user"
    assert payload["result"] == "denied"
    assert "reason" not in payload
    assert "approval_status" not in payload
    assert "clearance_status" not in payload
    assert "override_status" not in payload


def test_acknowledgment_scope_denied_detail_read_writes_safe_audit(client, db, auth_setup):
    appt = appointment(db, status="scheduled")
    other_appt = appointment(
        db,
        provider_obj=provider(db, name="dr. Failed Read Other"),
        room_obj=room(db, name="Failed read room"),
        service_obj=service(db, name="Failed read service"),
    )
    acknowledgment = create_acknowledgment(db, auth_setup, appt)
    original_status = appt.status
    denied_count = len(denied_read_events(db))

    wrong_scope_response = acknowledgment_detail_endpoint(
        client,
        other_appt.id,
        acknowledgment.id,
        auth_headers(client),
    )

    assert wrong_scope_response.status_code == 404
    db.expire(appt)
    assert appt.status == original_status
    events = denied_read_events(db)
    assert len(events) == denied_count + 1
    payload = events[-1].after_json
    assert payload["denial_category"] == "appointment_scope_mismatch"
    assert payload["access_type"] == "detail"
    assert payload["appointment_id"] == other_appt.id
    assert payload["acknowledgment_id"] == acknowledgment.id
    assert payload["actor_type"] == "user"
    assert "reason" not in payload
    assert "outcome_evidence_id" not in payload
    assert "task_id" not in payload
    assert "patient_message_id" not in payload


def test_acknowledgment_missing_detail_read_does_not_create_audit_noise(client, db, auth_setup):
    appt = appointment(db, status="scheduled")
    denied_count = len(denied_read_events(db))
    audit_count = db.query(AuditLog).count()

    response = acknowledgment_detail_endpoint(
        client,
        appt.id,
        9999,
        auth_headers(client),
    )

    assert response.status_code == 404
    assert len(denied_read_events(db)) == denied_count
    assert db.query(AuditLog).count() == audit_count


def test_acknowledgment_successful_repeated_reads_do_not_create_audit_noise(client, db, auth_setup):
    appt = appointment(db)
    acknowledgment = create_acknowledgment(db, auth_setup, appt)
    denied_count = len(denied_read_events(db))
    audit_count = db.query(AuditLog).count()
    headers = auth_headers(client)

    for _ in range(3):
        list_response = acknowledgment_list_endpoint(client, appt.id, headers)
        detail_response = acknowledgment_detail_endpoint(client, appt.id, acknowledgment.id, headers)
        assert list_response.status_code == 200
        assert detail_response.status_code == 200

    assert len(denied_read_events(db)) == denied_count
    assert db.query(AuditLog).count() == audit_count


def test_acknowledgment_denied_read_audit_failure_preserves_denied_response(client, db, auth_setup, monkeypatch):
    from tests.conftest import login_token
    import app.api.routes.appointments as appointment_routes

    appt = appointment(db)
    db.commit()
    token = login_token(client, "limited@test.local")
    original_status = appt.status

    def fail_audit(*args, **kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(appointment_routes, "record_acknowledgment_read_denied_audit", fail_audit)

    response = acknowledgment_list_endpoint(
        client,
        appt.id,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    refreshed_appt = db.get(Appointment, appt.id)
    assert refreshed_appt.status == original_status


def test_acknowledgment_detail_rejects_wrong_appointment(client, db, auth_setup):
    appt = appointment(db)
    other_appt = appointment(
        db,
        provider_obj=provider(db, name="dr. Read Other"),
        room_obj=room(db, name="Read other room"),
        service_obj=service(db, name="Read other service"),
    )
    acknowledgment = create_acknowledgment(db, auth_setup, appt)

    response = acknowledgment_detail_endpoint(client, other_appt.id, acknowledgment.id, auth_headers(client))

    assert response.status_code == 404


def test_api_key_acknowledgment_read_denied_even_with_read_scope(client, db):
    appt = appointment(db)
    api_key = ApiKey(
        name="Acknowledgment read integration",
        key_hash=hash_api_key("raw-ack-read-key"),
        scopes=["clinical_readiness.acknowledgments.read"],
        active=True,
    )
    db.add(api_key)
    db.commit()
    denied_count = len(denied_read_events(db))

    response = acknowledgment_list_endpoint(
        client,
        appt.id,
        headers={"X-ASTRA-API-Key": "raw-ack-read-key"},
    )

    assert response.status_code == 403
    events = denied_read_events(db)
    assert len(events) == denied_count + 1
    payload = events[-1].after_json
    assert payload["denial_category"] == "api_key_denied"
    assert payload["actor_type"] == "api_key"
    assert payload["actor_api_key_id"] == api_key.id
    assert payload["access_type"] == "list"
    assert "reason" not in payload
    assert "approval_status" not in payload
    assert "clearance_status" not in payload
    assert "override_status" not in payload
