from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "backend"))

PREFIX = "membership-migration-"
PASSWORD = "synthetic-membership-test"


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value


def password_hash() -> str:
    from app.core.security import hash_password

    return hash_password(PASSWORD)


def cleanup() -> None:
    engine = create_engine(database_url())
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM appointments WHERE notes LIKE :prefix"),
            {"prefix": f"{PREFIX}%"},
        )
        connection.execute(
            text("DELETE FROM rooms WHERE name LIKE :prefix"),
            {"prefix": f"{PREFIX}%"},
        )
        connection.execute(
            text("DELETE FROM services WHERE name LIKE :prefix"),
            {"prefix": f"{PREFIX}%"},
        )
        connection.execute(
            text("DELETE FROM providers WHERE lower(email) LIKE lower(:prefix)"),
            {"prefix": f"{PREFIX}%"},
        )
        connection.execute(
            text("DELETE FROM patients WHERE last_name LIKE :prefix"),
            {"prefix": f"{PREFIX}%"},
        )
        connection.execute(
            text("DELETE FROM users WHERE email LIKE :prefix"),
            {"prefix": f"{PREFIX}%"},
        )
        connection.execute(
            text(
                """
                DELETE FROM role_permissions
                WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :prefix)
                """
            ),
            {"prefix": f"{PREFIX}%"},
        )
        connection.execute(
            text("DELETE FROM roles WHERE name LIKE :prefix"),
            {"prefix": f"{PREFIX}%"},
        )
        connection.execute(
            text("DELETE FROM clinics WHERE name LIKE :prefix"),
            {"prefix": f"{PREFIX}%"},
        )
        if connection.dialect.has_table(connection, "institutions"):
            connection.execute(
                text("DELETE FROM institutions WHERE code LIKE :prefix"),
                {"prefix": f"{PREFIX}%"},
            )
        connection.execute(
            text(
                """
                DELETE FROM clinics
                WHERE name = 'Gastroenterologija'
                  AND NOT EXISTS (SELECT 1 FROM rooms WHERE rooms.clinic_id = clinics.id)
                  AND NOT EXISTS (SELECT 1 FROM providers WHERE providers.clinic_id = clinics.id)
                """
            )
        )


def create_role_and_user(
    connection,
    suffix: str,
    *,
    active: bool = True,
    permission_name: str | None = None,
) -> int:
    role_id = connection.scalar(
        text("INSERT INTO roles (name) VALUES (:name) RETURNING id"),
        {"name": f"{PREFIX}{suffix}-role"},
    )
    if permission_name:
        permission_id = connection.scalar(
            text(
                """
                INSERT INTO permissions (name)
                VALUES (:name)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """
            ),
            {"name": permission_name},
        )
        connection.execute(
            text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES (:role_id, :permission_id)
                ON CONFLICT DO NOTHING
                """
            ),
            {"role_id": role_id, "permission_id": permission_id},
        )
    return connection.scalar(
        text(
            """
            INSERT INTO users (email, full_name, password_hash, active, role_id)
            VALUES (:email, :name, :password_hash, :active, :role_id)
            RETURNING id
            """
        ),
        {
            "email": f"{PREFIX}{suffix}@example.invalid",
            "name": f"Synthetic {suffix}",
            "password_hash": password_hash(),
            "active": active,
            "role_id": role_id,
        },
    )


def seed_single() -> None:
    engine = create_engine(database_url())
    with engine.begin() as connection:
        clinic_id = connection.scalar(
            text("INSERT INTO clinics (name, active) VALUES (:name, true) RETURNING id"),
            {"name": f"{PREFIX}single-clinic"},
        )
        create_role_and_user(
            connection,
            "single-admin",
            permission_name="system.admin",
        )
        create_role_and_user(connection, "single-medical")
        create_role_and_user(connection, "single-no-candidate")
        connection.execute(
            text(
                """
                INSERT INTO providers
                    (full_name, email, active, staff_role, clinic_id, weekly_working_hours)
                VALUES (:name, :email, true, 'physician', :clinic_id, '{}'::json)
                """
            ),
            {
                "name": f"{PREFIX}single-medical",
                "email": f"{PREFIX}single-medical@example.invalid",
                "clinic_id": clinic_id,
            },
        )


def seed_multi() -> None:
    engine = create_engine(database_url())
    with engine.begin() as connection:
        clinic_a = connection.scalar(
            text("INSERT INTO clinics (name, active) VALUES (:name, true) RETURNING id"),
            {"name": f"{PREFIX}clinic-a"},
        )
        clinic_b = connection.scalar(
            text("INSERT INTO clinics (name, active) VALUES (:name, true) RETURNING id"),
            {"name": f"{PREFIX}clinic-b"},
        )
        clinic_c = connection.scalar(
            text("INSERT INTO clinics (name, active) VALUES (:name, true) RETURNING id"),
            {"name": f"{PREFIX}clinic-c"},
        )
        inactive_clinic = connection.scalar(
            text("INSERT INTO clinics (name, active) VALUES (:name, false) RETURNING id"),
            {"name": f"{PREFIX}inactive-clinic"},
        )
        provider_user = create_role_and_user(connection, "provider")
        creator_user = create_role_and_user(connection, "creator")
        verifier_user = create_role_and_user(connection, "verifier")
        create_role_and_user(connection, "ambiguous")
        create_role_and_user(connection, "system-admin", permission_name="system.admin")
        create_role_and_user(connection, "no-candidate")
        create_role_and_user(connection, "inactive-provider")
        create_role_and_user(connection, "inactive-clinic")
        create_role_and_user(connection, "invalid-provider")
        create_role_and_user(connection, "duplicate-provider")
        create_role_and_user(connection, "manual-preserved")
        create_role_and_user(connection, "unrelated-preserved")
        inactive_user = create_role_and_user(connection, "inactive", active=False)
        orphan_user = create_role_and_user(connection, "orphan-provider")
        provider = connection.scalar(
            text(
                """
                INSERT INTO providers
                    (full_name, email, active, staff_role, clinic_id, weekly_working_hours)
                VALUES (:name, :email, true, 'physician', :clinic_id, '{}'::json)
                RETURNING id
                """
            ),
            {
                "name": f"{PREFIX}provider",
                "email": f"{PREFIX}PROVIDER@EXAMPLE.INVALID",
                "clinic_id": clinic_a,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO providers
                    (full_name, email, active, staff_role, clinic_id, weekly_working_hours)
                VALUES
                    (:inactive_duplicate_name, :inactive_duplicate_email, false, 'physician', :clinic_b, '{}'::json),
                    (:name_a, :email_a, true, 'physician', :clinic_a, '{}'::json),
                    (:name_b, :email_b, true, 'physician', :clinic_b, '{}'::json),
                    (:orphan_name, :orphan_email, true, 'physician', NULL, '{}'::json),
                    (:inactive_provider_name, :inactive_provider_email, false, 'physician', :clinic_a, '{}'::json),
                    (:inactive_clinic_name, :inactive_clinic_email, true, 'physician', :inactive_clinic, '{}'::json),
                    (:invalid_name, :invalid_email, true, 'physician', NULL, '{}'::json),
                    (:duplicate_name_a, :duplicate_email_a, true, 'physician', :clinic_a, '{}'::json),
                    (:duplicate_name_b, :duplicate_email_b, true, 'physician', :clinic_a, '{}'::json),
                    (:manual_name_a, :manual_email_a, true, 'physician', :clinic_a, '{}'::json),
                    (:manual_name_b, :manual_email_b, true, 'physician', :clinic_b, '{}'::json),
                    (:unrelated_name_a, :unrelated_email_a, true, 'physician', :clinic_a, '{}'::json),
                    (:unrelated_name_b, :unrelated_email_b, true, 'physician', :clinic_b, '{}'::json)
                """
            ),
            {
                "inactive_duplicate_name": f"{PREFIX}provider-inactive-duplicate",
                "inactive_duplicate_email": f"{PREFIX}Provider@Example.Invalid",
                "name_a": f"{PREFIX}ambiguous-a",
                "email_a": f"{PREFIX}AMBIGUOUS@example.invalid",
                "clinic_a": clinic_a,
                "name_b": f"{PREFIX}ambiguous-b",
                "email_b": f"{PREFIX}Ambiguous@Example.Invalid",
                "clinic_b": clinic_b,
                "orphan_name": f"{PREFIX}orphan-provider",
                "orphan_email": f"{PREFIX}orphan-provider@example.invalid",
                "inactive_provider_name": f"{PREFIX}inactive-provider",
                "inactive_provider_email": f"{PREFIX}INACTIVE-PROVIDER@example.invalid",
                "inactive_clinic_name": f"{PREFIX}inactive-clinic",
                "inactive_clinic_email": f"{PREFIX}inactive-clinic@example.invalid",
                "inactive_clinic": inactive_clinic,
                "invalid_name": f"{PREFIX}invalid-provider",
                "invalid_email": f"{PREFIX}invalid-provider@example.invalid",
                "duplicate_name_a": f"{PREFIX}duplicate-provider-a",
                "duplicate_email_a": f"{PREFIX}DUPLICATE-PROVIDER@example.invalid",
                "duplicate_name_b": f"{PREFIX}duplicate-provider-b",
                "duplicate_email_b": f"{PREFIX}Duplicate-Provider@Example.Invalid",
                "manual_name_a": f"{PREFIX}manual-preserved-a",
                "manual_email_a": f"{PREFIX}MANUAL-PRESERVED@example.invalid",
                "manual_name_b": f"{PREFIX}manual-preserved-b",
                "manual_email_b": f"{PREFIX}Manual-Preserved@Example.Invalid",
                "unrelated_name_a": f"{PREFIX}unrelated-preserved-a",
                "unrelated_email_a": f"{PREFIX}UNRELATED-PRESERVED@example.invalid",
                "unrelated_name_b": f"{PREFIX}unrelated-preserved-b",
                "unrelated_email_b": f"{PREFIX}Unrelated-Preserved@Example.Invalid",
            },
        )
        room = connection.scalar(
            text(
                "INSERT INTO rooms (name, active, clinic_id) VALUES (:name, true, :clinic_id) RETURNING id"
            ),
            {"name": f"{PREFIX}room-b", "clinic_id": clinic_b},
        )
        service = connection.scalar(
            text(
                """
                INSERT INTO services (name, duration_minutes, price, active, visible_in_catalog)
                VALUES (:name, 30, 1, true, true) RETURNING id
                """
            ),
            {"name": f"{PREFIX}service"},
        )
        patient = connection.scalar(
            text(
                "INSERT INTO patients (first_name, last_name) VALUES ('Synthetic', :name) RETURNING id"
            ),
            {"name": f"{PREFIX}patient"},
        )
        connection.execute(
            text(
                """
                INSERT INTO appointments
                    (patient_id, service_id, provider_id, room_id, date, start_time, end_time,
                     duration_minutes, status, source, notes, created_by, identity_verified_by)
                VALUES
                    (:patient_id, :service_id, :provider_id, :room_id, DATE '2026-07-26',
                     TIME '09:00', TIME '09:30', 30, 'scheduled', 'manual', :notes,
                     :created_by, :verified_by)
                """
            ),
            {
                "patient_id": patient,
                "service_id": service,
                "provider_id": provider,
                "room_id": room,
                "notes": f"{PREFIX}appointment",
                "created_by": creator_user,
                "verified_by": verifier_user,
            },
        )
        assert (
            provider_user
            and creator_user
            and verifier_user
            and inactive_user
            and orphan_user
            and clinic_c
        )


def user_id(connection, suffix: str) -> int:
    return connection.scalar(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": f"{PREFIX}{suffix}@example.invalid"},
    )


def clinic_id(connection, suffix: str) -> int:
    return connection.scalar(
        text("SELECT id FROM clinics WHERE name = :name"),
        {"name": f"{PREFIX}{suffix}"},
    )


def memberships(connection, suffix: str) -> list[int]:
    return list(
        connection.scalars(
            text(
                """
                SELECT clinic_id
                FROM clinic_memberships
                WHERE user_id = :user_id AND active = true
                ORDER BY clinic_id
                """
            ),
            {"user_id": user_id(connection, suffix)},
        )
    )


def seed_unsafe_ambiguous_memberships() -> None:
    """Reproduce the access granted by the pre-correction draft of 0057."""
    engine = create_engine(database_url())
    with engine.begin() as connection:
        secondary_institution = connection.scalar(
            text(
                """
                INSERT INTO institutions (code, name, active)
                VALUES (:code, :name, true)
                ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """
            ),
            {
                "code": f"{PREFIX}secondary-institution",
                "name": f"{PREFIX}secondary-institution",
            },
        )
        connection.execute(
            text(
                """
                UPDATE clinics
                SET institution_id = :institution_id,
                    institution_key = :institution_key
                WHERE id = :clinic_id
                """
            ),
            {
                "institution_id": secondary_institution,
                "institution_key": f"{PREFIX}secondary-institution",
                "clinic_id": clinic_id(connection, "clinic-b"),
            },
        )
        target_user_id = user_id(connection, "ambiguous")
        for suffix in ("clinic-a", "clinic-b"):
            connection.execute(
                text(
                    """
                    INSERT INTO clinic_memberships (user_id, clinic_id, active)
                    VALUES (:user_id, :clinic_id, true)
                    ON CONFLICT (user_id, clinic_id) DO UPDATE
                    SET active = true, created_by_user_id = NULL
                    """
                ),
                {
                    "user_id": target_user_id,
                    "clinic_id": clinic_id(connection, suffix),
                },
            )
        # Explicit operator provenance must survive the ambiguous identity
        # correction even though this user has two provider candidates.
        connection.execute(
            text(
                """
                INSERT INTO clinic_memberships
                    (user_id, clinic_id, active, created_by_user_id)
                VALUES (:user_id, :clinic_id, true, :operator_id)
                ON CONFLICT (user_id, clinic_id) DO UPDATE
                SET active = true, created_by_user_id = EXCLUDED.created_by_user_id
                """
            ),
            {
                "user_id": user_id(connection, "manual-preserved"),
                "clinic_id": clinic_id(connection, "clinic-a"),
                "operator_id": user_id(connection, "system-admin"),
            },
        )
        # A null-origin legacy membership outside the ambiguous provider
        # candidate set is unrelated evidence and must not be deleted.
        connection.execute(
            text(
                """
                INSERT INTO clinic_memberships (user_id, clinic_id, active)
                VALUES (:user_id, :clinic_id, true)
                ON CONFLICT (user_id, clinic_id) DO UPDATE
                SET active = true, created_by_user_id = NULL
                """
            ),
            {
                "user_id": user_id(connection, "unrelated-preserved"),
                "clinic_id": clinic_id(connection, "clinic-c"),
            },
        )


def check_single() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        expected = clinic_id(connection, "single-clinic")
        assert memberships(connection, "single-admin") == [expected]
        assert memberships(connection, "single-medical") == [expected]
        assert memberships(connection, "single-no-candidate") == []
        assert connection.scalar(
            text(
                """
                SELECT count(*)
                FROM clinic_membership_migration_issues
                WHERE user_id IN (:first, :second)
                """
            ),
            {
                "first": user_id(connection, "single-admin"),
                "second": user_id(connection, "single-medical"),
            },
        ) == 0
        unsupported = migration_issue(connection, "single-no-candidate")
        assert unsupported.reason == "no_clinic_candidate"
        assert unsupported.candidate_clinic_ids == []
        assert unsupported.correction_reason == "corrected_unsafe_automatic_membership"
        assert unsupported.corrected_clinic_ids == [expected]
    assert_route_scope("single-admin", {expected})
    assert_route_scope("single-medical", {expected})
    assert_route_scope("single-no-candidate", set())
    print("evidence:test_single_clinic_no_candidate_correction")


def assert_route_scope(suffix: str, expected_clinic_ids: set[int]) -> None:
    from app.main import app

    with TestClient(app) as client:
        login = client.post(
            "/auth/login",
            json={"email": f"{PREFIX}{suffix}@example.invalid", "password": PASSWORD},
        )
        assert login.status_code == 200
        response = client.get(
            "/auth/me/clinics",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        assert response.status_code == 200
        assert {clinic["id"] for clinic in response.json()["clinics"]} == expected_clinic_ids


def migration_issue(connection, suffix: str):
    return connection.execute(
        text(
            """
            SELECT
                reason,
                candidate_clinic_ids,
                correction_reason,
                corrected_clinic_ids,
                status
            FROM clinic_membership_migration_issues
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id(connection, suffix)},
    ).one()


def check_multi() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        clinic_a = clinic_id(connection, "clinic-a")
        clinic_b = clinic_id(connection, "clinic-b")
        clinic_c = clinic_id(connection, "clinic-c")
        inactive_clinic = clinic_id(connection, "inactive-clinic")
        assert memberships(connection, "provider") == [clinic_a]
        assert connection.scalar(
            text(
                """
                SELECT count(*)
                FROM clinic_membership_migration_issues
                WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id(connection, "provider")},
        ) == 0
        # Creating or identity-verifying a record is not authoritative evidence
        # that the operator belongs to that clinic.
        assert memberships(connection, "creator") == []
        assert memberships(connection, "verifier") == []
        assert memberships(connection, "ambiguous") == []
        assert memberships(connection, "system-admin") == [clinic_a, clinic_b, clinic_c]
        assert memberships(connection, "no-candidate") == []
        assert memberships(connection, "inactive-provider") == []
        assert memberships(connection, "inactive-clinic") == []
        assert memberships(connection, "invalid-provider") == []
        assert memberships(connection, "duplicate-provider") == []
        assert memberships(connection, "manual-preserved") == [clinic_a]
        assert memberships(connection, "unrelated-preserved") == [clinic_c]
        assert memberships(connection, "inactive") == []
        assert memberships(connection, "orphan-provider") == []

        issue = migration_issue(connection, "ambiguous")
        assert issue.reason == "ambiguous_active_clinic_candidates"
        assert issue.candidate_clinic_ids == [clinic_a, clinic_b]
        assert issue.correction_reason == "corrected_unsafe_automatic_membership"
        assert issue.corrected_clinic_ids == [clinic_a, clinic_b]
        assert issue.status == "pending"

        for suffix in ("creator", "verifier", "no-candidate"):
            pending = migration_issue(connection, suffix)
            assert pending.reason == "no_clinic_candidate"
            assert pending.candidate_clinic_ids == []
            assert pending.correction_reason is None
            assert pending.corrected_clinic_ids is None
            assert pending.status == "pending"

        for suffix in ("orphan-provider", "invalid-provider"):
            pending = migration_issue(connection, suffix)
            assert pending.reason == "invalid_provider_identity"
            assert pending.candidate_clinic_ids == []
            assert pending.correction_reason is None
            assert pending.corrected_clinic_ids is None

        inactive_provider_issue = migration_issue(connection, "inactive-provider")
        assert inactive_provider_issue.reason == "inactive_clinic_candidate"
        assert inactive_provider_issue.candidate_clinic_ids == [clinic_a]
        assert inactive_provider_issue.correction_reason is None

        inactive_clinic_issue = migration_issue(connection, "inactive-clinic")
        assert inactive_clinic_issue.reason == "inactive_clinic_candidate"
        assert inactive_clinic_issue.candidate_clinic_ids == [inactive_clinic]
        assert inactive_clinic_issue.correction_reason is None

        duplicate_issue = migration_issue(connection, "duplicate-provider")
        assert duplicate_issue.reason == "invalid_provider_identity"
        assert duplicate_issue.candidate_clinic_ids == [clinic_a]
        assert duplicate_issue.correction_reason == "corrected_unsafe_automatic_membership"
        assert duplicate_issue.corrected_clinic_ids == [clinic_a]

        manual_issue = migration_issue(connection, "manual-preserved")
        assert manual_issue.reason == "ambiguous_active_clinic_candidates"
        assert manual_issue.candidate_clinic_ids == [clinic_a, clinic_b]
        assert manual_issue.correction_reason is None
        assert manual_issue.corrected_clinic_ids is None

        unrelated_issue = migration_issue(connection, "unrelated-preserved")
        assert unrelated_issue.reason == "ambiguous_active_clinic_candidates"
        assert unrelated_issue.candidate_clinic_ids == [clinic_a, clinic_b]
        assert unrelated_issue.correction_reason is None
        assert unrelated_issue.corrected_clinic_ids is None

        institution_ids = connection.execute(
            text(
                """
                SELECT institution_id
                FROM clinics
                WHERE id IN (:clinic_a, :clinic_b)
                ORDER BY id
                """
            ),
            {"clinic_a": clinic_a, "clinic_b": clinic_b},
        ).scalars().all()
        assert len(set(institution_ids)) == 2

        assert connection.scalar(
            text(
                """
                SELECT count(*) FROM clinic_membership_migration_issues
                WHERE user_id IN (:inactive, :admin)
                """
            ),
            {
                "inactive": user_id(connection, "inactive"),
                "admin": user_id(connection, "system-admin"),
            },
        ) == 0
        duplicate_count = connection.scalar(
            text(
                """
                SELECT count(*)
                FROM (
                    SELECT user_id, clinic_id
                    FROM clinic_memberships
                    GROUP BY user_id, clinic_id
                    HAVING count(*) > 1
                ) duplicate_memberships
                """
            )
        )
        assert duplicate_count == 0
    assert_route_scope("provider", {clinic_a})
    assert_route_scope("creator", set())
    assert_route_scope("verifier", set())
    assert_route_scope("ambiguous", set())
    assert_route_scope("system-admin", {clinic_a, clinic_b, clinic_c})
    assert_route_scope("no-candidate", set())
    assert_route_scope("inactive-provider", set())
    assert_route_scope("inactive-clinic", set())
    assert_route_scope("invalid-provider", set())
    assert_route_scope("duplicate-provider", set())
    assert_route_scope("manual-preserved", {clinic_a})
    assert_route_scope("unrelated-preserved", {clinic_c})
    assert_route_scope("orphan-provider", set())
    print("evidence:test_single_active_candidate")
    print("evidence:test_case_insensitive_single_candidate")
    print("evidence:test_active_candidate_ignores_inactive_duplicate")
    print("evidence:test_multiple_case_insensitive_active_candidates")
    print("evidence:test_no_candidate")
    print("evidence:test_inactive_provider_candidate")
    print("evidence:test_inactive_clinic_candidate")
    print("evidence:test_invalid_provider_identity")
    print("evidence:test_manual_membership_preservation")
    print("evidence:test_unrelated_membership_preservation")
    print("evidence:test_unsafe_assignment_correction_record")
    print("evidence:test_legitimate_automatic_membership_preservation")
    print("evidence:test_system_admin_preservation")
    print("evidence:test_inactive_user_no_issue")
    print("evidence:test_multiple_institutions_fail_closed")
    print("evidence:test_duplicate_provider_identity_fail_closed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=(
            "cleanup",
            "seed-single",
            "check-single",
            "seed-multi",
            "seed-unsafe-ambiguous-memberships",
            "check-multi",
        ),
    )
    args = parser.parse_args()
    {
        "cleanup": cleanup,
        "seed-single": seed_single,
        "check-single": check_single,
        "seed-multi": seed_multi,
        "seed-unsafe-ambiguous-memberships": seed_unsafe_ambiguous_memberships,
        "check-multi": check_multi,
    }[args.action]()
