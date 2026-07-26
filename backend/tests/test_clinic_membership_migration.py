import pytest
from sqlalchemy import select

from app.models.domain import (
    ClinicMembership,
    ClinicMembershipMigrationIssue,
    Role,
    User,
)
from app.services.clinic_membership_migration import (
    MembershipMigrationResolutionError,
    membership_migration_status,
    resolve_membership_migration_issue,
)


def test_operator_resolves_only_an_explicit_pending_membership_issue(db, auth_setup):
    target = User(
        email="legacy-ambiguous@example.invalid",
        full_name="Legacy Ambiguous",
        password_hash="not-used",
        role=db.scalar(select(Role).where(Role.name == "limited")),
    )
    db.add(target)
    db.flush()
    issue = ClinicMembershipMigrationIssue(
        user_id=target.id,
        reason="ambiguous_clinic_membership",
        candidate_clinic_ids=[auth_setup["clinic"].id],
    )
    db.add(issue)
    db.commit()

    resolved = resolve_membership_migration_issue(
        db,
        user_email=target.email,
        clinic_id=auth_setup["clinic"].id,
        operator_email=auth_setup["admin"].email,
        note="Owner verified the legacy clinic assignment.",
    )
    db.commit()

    membership = db.scalar(
        select(ClinicMembership).where(
            ClinicMembership.user_id == target.id,
            ClinicMembership.clinic_id == auth_setup["clinic"].id,
        )
    )
    assert membership is not None
    assert membership.active is True
    assert membership.created_by_user_id == auth_setup["admin"].id
    assert resolved.status == "resolved"
    assert resolved.resolved_by_user_id == auth_setup["admin"].id
    assert resolved.resolution_note == "Owner verified the legacy clinic assignment."
    assert membership_migration_status(db)["pending"] == 0
    assert membership_migration_status(db)["resolved"] == 1


def test_operator_cannot_assign_membership_without_pending_migration_issue(db, auth_setup):
    target = User(
        email="legacy-no-issue@example.invalid",
        full_name="Legacy No Issue",
        password_hash="not-used",
        role=db.scalar(select(Role).where(Role.name == "limited")),
    )
    db.add(target)
    db.commit()

    with pytest.raises(MembershipMigrationResolutionError, match="Nema otvorenog"):
        resolve_membership_migration_issue(
            db,
            user_email=target.email,
            clinic_id=auth_setup["clinic"].id,
            operator_email=auth_setup["admin"].email,
            note="Must not create arbitrary access.",
        )

    assert db.scalar(
        select(ClinicMembership).where(ClinicMembership.user_id == target.id)
    ) is None


def test_non_admin_operator_cannot_resolve_membership_issue(db, auth_setup):
    target = User(
        email="legacy-protected@example.invalid",
        full_name="Legacy Protected",
        password_hash="not-used",
        role=db.scalar(select(Role).where(Role.name == "limited")),
    )
    db.add(target)
    db.flush()
    db.add(
        ClinicMembershipMigrationIssue(
            user_id=target.id,
            reason="ambiguous_clinic_membership",
            candidate_clinic_ids=[auth_setup["clinic"].id],
        )
    )
    db.commit()

    with pytest.raises(MembershipMigrationResolutionError, match="system.admin"):
        resolve_membership_migration_issue(
            db,
            user_email=target.email,
            clinic_id=auth_setup["clinic"].id,
            operator_email="limited@test.local",
            note="Unauthorized operator.",
        )

    assert db.scalar(
        select(ClinicMembership).where(ClinicMembership.user_id == target.id)
    ) is None
