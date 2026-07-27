from app.models.domain import AuditLog, Clinic, Institution
from tests.conftest import login_token


def test_foreign_and_missing_audit_references_have_identical_not_found_response(
    client, db, auth_setup
):
    token = login_token(client, "admin@test.local")
    foreign_clinic = Clinic(name="Third rescan foreign audit clinic")
    db.add(foreign_clinic)
    db.flush()
    foreign = AuditLog(
        scope_type="clinic",
        clinic_id=foreign_clinic.id,
        action="update",
        entity_type="Appointment",
        entity_id=17,
    )
    db.add(foreign)
    db.flush()

    def record(entity_id: int):
        return client.post(
            "/api/audit/access-events",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "action": "audit_log.viewed",
                "entity_type": "AuditLog",
                "entity_id": entity_id,
                "surface": "audit_viewer",
            },
        )

    foreign_response = record(foreign.id)
    missing_response = record(foreign.id + 1_000_000)

    assert foreign_response.status_code == missing_response.status_code == 409
    assert foreign_response.json() == missing_response.json()
    assert (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "audit_log.viewed",
            AuditLog.entity_id == foreign.id,
        )
        .count()
        == 0
    )


def test_inaccessible_audit_scope_variants_are_indistinguishable_from_missing(
    client, db, auth_setup
):
    token = login_token(client, "admin@test.local")
    foreign_clinic = Clinic(name="Third rescan foreign clinic variant")
    foreign_institution = Institution(
        code="third-rescan-foreign",
        name="Third rescan foreign institution",
    )
    db.add_all([foreign_clinic, foreign_institution])
    db.flush()
    events = [
        AuditLog(
            scope_type="clinic",
            clinic_id=foreign_clinic.id,
            action="update",
            entity_type="Appointment",
        ),
        AuditLog(
            scope_type="institution_clinical",
            institution_id=foreign_institution.id,
            action="clinical_document_reviewed",
            entity_type="ClinicalDocument",
        ),
        AuditLog(
            scope_type="system_security",
            action="auth.browser_session_invalid",
            entity_type="UserSession",
        ),
        AuditLog(
            scope_type=None,
            action="legacy_unresolved",
            entity_type="LegacyObject",
        ),
    ]
    db.add_all(events)
    db.flush()
    auth_setup["admin"].role.permissions = [
        permission
        for permission in auth_setup["admin"].role.permissions
        if permission.name != "system.admin"
    ]
    db.flush()

    def record(entity_id: int):
        return client.post(
            "/api/audit/access-events",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "action": "audit_log.viewed",
                "entity_type": "AuditLog",
                "entity_id": entity_id,
                "surface": "audit_viewer",
            },
        )

    missing = record(max(event.id for event in events) + 1_000_000)
    for event in events:
        response = record(event.id)
        assert response.status_code == missing.status_code == 409
        assert response.json() == missing.json()

    viewed_ids = {
        event.entity_id
        for event in db.query(AuditLog)
        .filter(AuditLog.action == "audit_log.viewed")
        .all()
    }
    assert viewed_ids.isdisjoint({event.id for event in events})


def test_direct_clinic_audit_reference_cannot_create_authoritative_event(client, db, auth_setup):
    token = login_token(client, "admin@test.local")
    allowed = AuditLog(
        scope_type="clinic",
        clinic_id=auth_setup["clinic"].id,
        institution_id=auth_setup["clinic"].institution_id,
        action="update",
        entity_type="Appointment",
        entity_id=31,
    )
    db.add(allowed)
    db.flush()

    response = client.post(
        "/api/audit/access-events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "audit_log.viewed",
            "entity_type": "AuditLog",
            "entity_id": allowed.id,
            "surface": "audit_viewer",
        },
    )

    assert response.status_code == 409
    assert (
        db.query(AuditLog)
        .filter(AuditLog.action == "audit_log.viewed", AuditLog.entity_id == allowed.id)
        .count()
        == 0
    )
