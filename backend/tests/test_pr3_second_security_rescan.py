from __future__ import annotations

from datetime import datetime, UTC

import pytest

from app.auth.dependencies import hash_api_key
from app.models.domain import ApiKey, AuditLog, PatientJourney, UserSession
from app.services.request_ids import REQUEST_ID_PATTERN, normalize_request_id
from app.services.sessions import SECURITY_AUDIT_EVENT_POLICIES
from tests.conftest import login_token
from tests.factories import default_clinic, episode, patient, provider, room, service


def _payload(db, *, start: str, end: str):
    patient_obj = patient(db, f"Secure{start.replace(':', '')}")
    provider_obj = provider(db, f"dr. Secure {start}")
    room_obj = room(db, f"Secure room {start}")
    service_obj = service(db, f"Secure service {start}")
    clinic = default_clinic(db)
    provider_obj.clinic_id = clinic.id
    room_obj.clinic_id = clinic.id
    episode_obj = episode(db, patient_obj=patient_obj, provider_obj=provider_obj)
    episode_obj.summary = "SYNTHETIC_EPISODE_SUMMARY_SENTINEL"
    episode_obj.clinical_notes = "SYNTHETIC_EPISODE_NOTES_SENTINEL"
    db.flush()
    return {
        "patient_id": patient_obj.id,
        "provider_id": provider_obj.id,
        "room_id": room_obj.id,
        "service_id": service_obj.id,
        "episode_id": episode_obj.id,
        "date": "2026-07-06",
        "start_time": start,
        "end_time": end,
        "duration_minutes": 30,
        "status": "scheduled",
        "source": "manual",
    }


@pytest.mark.parametrize(
    ("route", "start", "end"),
    (
        ("/api/appointments", "09:00", "09:30"),
        ("/api/intake/web/appointments", "10:00", "10:30"),
        ("/api/ai/appointments/create", "11:00", "11:30"),
    ),
)
def test_scheduling_create_responses_never_materialize_episode_phi(
    client, db, auth_setup, route, start, end
):
    token = login_token(client, "admin@test.local")
    response = client.post(
        route,
        headers={"Authorization": f"Bearer {token}"},
        json=_payload(db, start=start, end=end),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["episode_id"] is not None
    assert "episode" not in body
    assert "SYNTHETIC_EPISODE_SUMMARY_SENTINEL" not in response.text
    assert "SYNTHETIC_EPISODE_NOTES_SENTINEL" not in response.text


def test_ai_api_key_receives_only_operational_appointment_projection(client, db, auth_setup):
    raw_key = "astra_second_rescan_ai_key"
    db.add(
        ApiKey(
            name="Synthetic scheduler",
            key_hash=hash_api_key(raw_key),
            scopes=["ai.appointments.create"],
            clinic_id=auth_setup["clinic"].id,
            institution_id=auth_setup["clinic"].institution_id,
            active=True,
        )
    )
    db.flush()

    response = client.post(
        "/api/ai/appointments/create",
        headers={"X-ASTRA-API-Key": raw_key},
        json=_payload(db, start="12:00", end="12:30"),
    )

    assert response.status_code == 200
    assert response.json()["episode_id"] is not None
    assert "episode" not in response.json()
    assert "SYNTHETIC_EPISODE_" not in response.text


def test_episode_mismatch_and_foreign_reference_share_generic_not_found(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    payload = _payload(db, start="13:00", end="13:30")
    other_patient = patient(db, "Other")
    payload["patient_id"] = other_patient.id

    mismatch = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    missing_payload = dict(payload, episode_id=999999)
    missing = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json=missing_payload,
    )

    assert mismatch.status_code == missing.status_code == 404
    assert mismatch.json() == missing.json()


def test_openapi_scheduling_contract_does_not_embed_clinical_episode(client):
    schema = client.get("/openapi.json").json()
    operational = schema["components"]["schemas"]["AppointmentOperationalOut"]
    appointment = schema["components"]["schemas"]["AppointmentOut"]

    assert "episode" not in operational.get("properties", {})
    assert "episode" not in appointment.get("properties", {})
    assert "episode_id" in operational["properties"]


def test_every_browser_security_event_has_an_explicit_persistence_class():
    expected = {
        "auth.browser_login_success": "individual",
        "auth.browser_logout": "individual",
        "auth.browser_session_revoked": "individual",
        "auth.browser_session_invalid": "bounded_counter",
        "auth.browser_csrf_invalid": "bounded_counter",
        "auth.browser_credential_conflict": "bounded_counter",
    }

    assert {
        action: policy.persistence_mode
        for action, policy in SECURITY_AUDIT_EVENT_POLICIES.items()
    } == expected


def test_scheduling_read_update_and_episode_siblings_use_operational_projection(
    client, db, auth_setup
):
    token = login_token(client, "admin@test.local")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/appointments",
        headers=headers,
        json=_payload(db, start="09:00", end="09:30"),
    )
    assert created.status_code == 200
    appointment_id = created.json()["id"]
    episode_id = created.json()["episode_id"]

    responses = (
        client.get(f"/api/appointments/{appointment_id}", headers=headers),
        client.get("/api/appointments?date_from=2026-07-06&date_to=2026-07-06", headers=headers),
        client.get("/api/schedule/day?date=2026-07-06", headers=headers),
        client.patch(
            f"/api/appointments/{appointment_id}",
            headers=headers,
            json={"status": "arrived"},
        ),
        client.get(f"/api/episodes/{episode_id}/appointments", headers=headers),
    )

    for response in responses:
        assert response.status_code == 200
        assert '"episode":' not in response.text
        assert "SYNTHETIC_EPISODE_" not in response.text


@pytest.mark.parametrize(
    "raw",
    (
        "a",
        "x" * 80,
        "08e3eb4f-4a35-4d15-acd8-30e7b7b54b09",
        "external.correlation_id:2026-07-25",
    ),
)
def test_valid_request_ids_are_preserved(raw):
    assert normalize_request_id(raw) == raw


@pytest.mark.parametrize(
    "raw",
    (
        None,
        "x" * 81,
        "x" * 10_000,
        "unicode-č",
        "line\r\nbreak",
        "white space",
        "unsafe/value",
    ),
)
def test_invalid_request_ids_are_replaced_with_safe_canonical_values(raw):
    normalized = normalize_request_id(raw)
    assert REQUEST_ID_PATTERN.fullmatch(normalized)
    assert normalized != raw


def test_oversized_request_id_cannot_suppress_invalid_session_audit(client, db, auth_setup):
    client.cookies.set("astra_session", "u" * 64)
    response = client.get("/auth/session", headers={"X-Request-ID": "x" * 81})

    assert response.status_code == 401
    canonical = response.headers["X-Request-ID"]
    assert REQUEST_ID_PATTERN.fullmatch(canonical)
    assert canonical != "x" * 81
    db.expire_all()
    event = db.query(AuditLog).filter(AuditLog.action == "auth.browser_session_invalid").one()
    assert event.occurrence_count == 1
    assert event.request_id is None


def test_known_invalid_session_burst_is_bounded(client, db, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    session = db.query(UserSession).one()
    session.revoked_at = datetime.now(UTC)
    db.commit()

    for _ in range(12):
        assert client.get("/auth/session").status_code == 401

    db.expire_all()
    events = db.query(AuditLog).filter(AuditLog.action == "auth.browser_session_invalid").all()
    assert len(events) == 1
    assert events[0].occurrence_count == 12
    assert events[0].actor_user_id == auth_setup["admin"].id


def test_invalid_csrf_burst_is_bounded(client, db, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    assert login.status_code == 200

    for _ in range(9):
        response = client.post(
            "/api/patients",
            headers={"X-CSRF-Token": "wrong-token"},
            json={"first_name": "Never", "last_name": "Created"},
        )
        assert response.status_code == 403

    db.expire_all()
    events = db.query(AuditLog).filter(AuditLog.action == "auth.browser_csrf_invalid").all()
    assert len(events) == 1
    assert events[0].occurrence_count == 9


def test_credential_conflict_burst_is_bounded(client, db, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    assert login.status_code == 200
    token = login_token(client, "admin@test.local")

    for _ in range(10):
        response = client.get(
            "/api/inventory/items",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    db.expire_all()
    events = db.query(AuditLog).filter(AuditLog.action == "auth.browser_credential_conflict").all()
    assert len(events) == 1
    assert events[0].occurrence_count == 10
    assert events[0].actor_user_id == auth_setup["admin"].id


@pytest.mark.parametrize(
    ("action", "entity_type"),
    (
        ("clinical_workspace.opened", "PatientJourney"),
        ("clinical_form.viewed", "ClinicalFormInstance"),
        ("signed_report.viewed", "SignedClinicalReport"),
        ("source_document.viewed", "ClinicalDocument"),
        ("source_document.downloaded", "ClinicalDocument"),
        ("clinical_report.printed", "SignedClinicalReport"),
    ),
)
def test_non_medical_admin_is_rejected_before_clinical_object_resolution(
    client, db, auth_setup, action, entity_type
):
    auth_setup["admin"].role.professional_category = "administrative_staff"
    token = login_token(client, "admin@test.local")
    before = db.query(AuditLog).filter(AuditLog.action == action).count()

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": action,
            "entity_type": entity_type,
            "entity_id": 999999,
            "surface": "clinical_workspace",
        },
    )

    assert response.status_code == 403
    assert db.query(AuditLog).filter(AuditLog.action == action).count() == before


def test_medical_staff_can_record_scoped_clinical_access(client, db, auth_setup):
    payload = _payload(db, start="14:00", end="14:30")
    token = login_token(client, "admin@test.local")
    appointment_response = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    journey = db.query(PatientJourney).filter(
        PatientJourney.appointment_id == appointment_response.json()["id"]
    ).one()

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "clinical_workspace.opened",
            "entity_type": "PatientJourney",
            "entity_id": journey.id,
            "surface": "clinical_workspace",
        },
    )

    assert response.status_code == 200
    event = db.get(AuditLog, response.json()["id"])
    assert event.actor_user_id == auth_setup["admin"].id
    assert "SYNTHETIC_EPISODE" not in str(event.after_json)
