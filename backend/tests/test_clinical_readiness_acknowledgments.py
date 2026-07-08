import pytest

import app.services.clinical_readiness_acknowledgments as acknowledgment_service
from app.models.domain import (
    AuditLog,
    ClinicalEpisode,
    ClinicalPlan,
    ClinicalReadinessReviewAcknowledgment,
    ClinicalReadinessSnapshot,
    Permission,
)
from app.services.clinical_readiness_acknowledgments import (
    CLINICAL_READINESS_ACKNOWLEDGED_EVENT,
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


def test_acknowledgment_runtime_surface_still_absent(client):
    route_paths = {route.path for route in client.app.routes}

    assert "/api/clinical-readiness-review-acknowledgments" not in route_paths
    assert "/api/appointments/{appointment_id}/clinical-readiness-review-acknowledgments" not in route_paths
    assert all("acknowledgment" not in path for path in route_paths)


def test_acknowledgment_runtime_permission_seed_still_absent(db):
    forbidden_permissions = {
        "clinical_readiness.acknowledgments.read",
        "clinical_readiness.acknowledgments.write",
        "clinical_readiness.acknowledgments.manage",
    }

    seeded_permissions = {name for (name,) in db.query(Permission.name).all()}

    assert forbidden_permissions.isdisjoint(seeded_permissions)
