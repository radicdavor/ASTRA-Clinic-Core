from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit
from app.models.domain import (
    Clinic,
    ClinicMembership,
    ClinicMembershipMigrationIssue,
    User,
)


class MembershipMigrationResolutionError(ValueError):
    pass


def membership_migration_status(db: Session) -> dict:
    issues = db.scalars(
        select(ClinicMembershipMigrationIssue)
        .order_by(
            ClinicMembershipMigrationIssue.status,
            ClinicMembershipMigrationIssue.id,
        )
    ).all()
    return {
        "pending": sum(issue.status == "pending" for issue in issues),
        "resolved": sum(issue.status == "resolved" for issue in issues),
        "issues": [
            {
                "id": issue.id,
                "user_id": issue.user_id,
                "user_email": issue.user.email,
                "user_name": issue.user.full_name,
                "reason": issue.reason,
                "candidate_clinic_ids": issue.candidate_clinic_ids,
                "correction_reason": issue.correction_reason,
                "corrected_clinic_ids": issue.corrected_clinic_ids,
                "status": issue.status,
                "resolution_clinic_id": issue.resolution_clinic_id,
            }
            for issue in issues
        ],
    }


def resolve_membership_migration_issue(
    db: Session,
    *,
    user_email: str,
    clinic_id: int,
    operator_email: str,
    note: str,
) -> ClinicMembershipMigrationIssue:
    normalized_note = note.strip()
    if not normalized_note:
        raise MembershipMigrationResolutionError("Bilješka operatora je obvezna")
    target = db.scalar(select(User).where(User.email == user_email, User.active.is_(True)))
    operator = db.scalar(select(User).where(User.email == operator_email, User.active.is_(True)))
    clinic = db.scalar(select(Clinic).where(Clinic.id == clinic_id, Clinic.active.is_(True)))
    if target is None or operator is None or clinic is None:
        raise MembershipMigrationResolutionError("Korisnik, operator ili aktivna klinika nisu pronađeni")
    operator_permissions = {
        permission.name
        for permission in (operator.role.permissions if operator.role else [])
    }
    if "system.admin" not in operator_permissions:
        raise MembershipMigrationResolutionError("Operator nema dozvolu system.admin")
    issue = db.scalar(
        select(ClinicMembershipMigrationIssue).where(
            ClinicMembershipMigrationIssue.user_id == target.id,
            ClinicMembershipMigrationIssue.status == "pending",
        ).with_for_update()
    )
    if issue is None:
        raise MembershipMigrationResolutionError("Nema otvorenog migracijskog pitanja za korisnika")
    membership = db.scalar(
        select(ClinicMembership).where(
            ClinicMembership.user_id == target.id,
            ClinicMembership.clinic_id == clinic.id,
        )
    )
    if membership is None:
        membership = ClinicMembership(
            user_id=target.id,
            clinic_id=clinic.id,
            active=True,
            created_by_user_id=operator.id,
        )
        db.add(membership)
    else:
        membership.active = True
        membership.created_by_user_id = operator.id
    issue.status = "resolved"
    issue.resolution_clinic_id = clinic.id
    issue.resolution_note = normalized_note
    issue.resolved_at = datetime.now(timezone.utc)
    issue.resolved_by_user_id = operator.id
    db.flush()
    audit(
        db,
        "clinic_membership_migration_resolved",
        "ClinicMembership",
        membership.id,
        "Operator je razriješio legacy članstvo korisnika u klinici",
        operator.id,
        after_json={
            "user_id": target.id,
            "clinic_id": clinic.id,
            "migration_issue_id": issue.id,
            "active": True,
        },
        scope_type="clinic",
        clinic_id=clinic.id,
        institution_id=clinic.institution_id,
    )
    return issue
