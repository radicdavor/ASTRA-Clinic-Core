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
        provider_user = create_role_and_user(connection, "provider")
        creator_user = create_role_and_user(connection, "creator")
        verifier_user = create_role_and_user(connection, "verifier")
        create_role_and_user(connection, "ambiguous")
        create_role_and_user(connection, "system-admin", permission_name="system.admin")
        create_role_and_user(connection, "billing")
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
                "email": f"{PREFIX}provider@example.invalid",
                "clinic_id": clinic_a,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO providers
                    (full_name, email, active, staff_role, clinic_id, weekly_working_hours)
                VALUES (:name, :email, true, 'physician', NULL, '{}'::json)
                """
            ),
            {
                "name": f"{PREFIX}orphan-provider",
                "email": f"{PREFIX}orphan-provider@example.invalid",
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO providers
                    (full_name, email, active, staff_role, clinic_id, weekly_working_hours)
                VALUES
                    (:name_a, :email_a, true, 'physician', :clinic_a, '{}'::json),
                    (:name_b, :email_b, true, 'physician', :clinic_b, '{}'::json)
                """
            ),
            {
                "name_a": f"{PREFIX}ambiguous-a",
                "email_a": f"{PREFIX}AMBIGUOUS@example.invalid",
                "clinic_a": clinic_a,
                "name_b": f"{PREFIX}ambiguous-b",
                "email_b": f"{PREFIX}Ambiguous@Example.Invalid",
                "clinic_b": clinic_b,
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
        assert provider_user and creator_user and verifier_user and inactive_user and orphan_user


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


def check_single() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        expected = clinic_id(connection, "single-clinic")
        assert memberships(connection, "single-admin") == [expected]
        assert memberships(connection, "single-medical") == [expected]
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
    assert_route_scope("single-admin", {expected})
    assert_route_scope("single-medical", {expected})


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


def check_multi() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        clinic_a = clinic_id(connection, "clinic-a")
        clinic_b = clinic_id(connection, "clinic-b")
        assert memberships(connection, "provider") == [clinic_a]
        # Creating or identity-verifying a record is not authoritative evidence
        # that the operator belongs to that clinic.
        assert memberships(connection, "creator") == []
        assert memberships(connection, "verifier") == []
        assert memberships(connection, "ambiguous") == []
        assert memberships(connection, "system-admin") == [clinic_a, clinic_b]
        assert memberships(connection, "billing") == []
        assert memberships(connection, "inactive") == []
        assert memberships(connection, "orphan-provider") == []
        issue = connection.execute(
            text(
                """
                SELECT reason, candidate_clinic_ids, status
                FROM clinic_membership_migration_issues
                WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id(connection, "ambiguous")},
        ).one()
        assert issue.reason == "ambiguous_clinic_membership"
        assert issue.candidate_clinic_ids == [clinic_a, clinic_b]
        assert issue.status == "pending"
        for suffix in ("creator", "verifier", "billing", "orphan-provider"):
            pending = connection.execute(
                text(
                    """
                    SELECT reason, candidate_clinic_ids, status
                    FROM clinic_membership_migration_issues
                    WHERE user_id = :user_id
                    """
                ),
                {"user_id": user_id(connection, suffix)},
            ).one()
            assert pending.reason == "ambiguous_clinic_membership"
            assert pending.candidate_clinic_ids == []
            assert pending.status == "pending"
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
    assert_route_scope("system-admin", {clinic_a, clinic_b})
    assert_route_scope("billing", set())
    assert_route_scope("orphan-provider", set())


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
