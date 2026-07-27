from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Actor, CurrentUserContext
from app.models.domain import AuditLog, Clinic, Institution, Role, User
from app.services.audit_access import _authorized_audit_reference


pytestmark = pytest.mark.integration


def test_postgresql_audit_reference_lookup_hides_foreign_object_existence(pg_db):
    institution = Institution(code="third-rescan-local", name="Third rescan local")
    foreign_institution = Institution(code="third-rescan-foreign", name="Third rescan foreign")
    pg_db.add_all([institution, foreign_institution])
    pg_db.flush()
    local_clinic = Clinic(name="Third rescan local clinic", institution_id=institution.id)
    foreign_clinic = Clinic(name="Third rescan foreign clinic", institution_id=foreign_institution.id)
    role = Role(
        name="third-rescan-audit-role",
        description="Synthetic PostgreSQL audit scope role",
        professional_category="non_medical_staff",
    )
    pg_db.add_all([local_clinic, foreign_clinic, role])
    pg_db.flush()
    user = User(
        email="third-rescan-audit@test.local",
        full_name="Third Rescan Audit",
        password_hash="synthetic-not-a-login-secret",
        role_id=role.id,
    )
    allowed = AuditLog(
        scope_type="clinic",
        clinic_id=local_clinic.id,
        institution_id=institution.id,
        action="update",
        entity_type="Appointment",
    )
    foreign = AuditLog(
        scope_type="clinic",
        clinic_id=foreign_clinic.id,
        institution_id=foreign_institution.id,
        action="update",
        entity_type="Appointment",
    )
    pg_db.add_all([user, allowed, foreign])
    pg_db.flush()
    context = CurrentUserContext(
        actor=Actor(actor_type="user", user=user),
        user=user,
        permissions={"audit.read"},
        active_clinic=local_clinic,
    )

    assert _authorized_audit_reference(pg_db, allowed.id, context).id == allowed.id

    outcomes = []
    for audit_id in (foreign.id, foreign.id + 1_000_000):
        with pytest.raises(HTTPException) as error:
            _authorized_audit_reference(pg_db, audit_id, context)
        outcomes.append((error.value.status_code, error.value.detail))

    assert outcomes[0] == outcomes[1]
    assert outcomes[0][0] == 404
