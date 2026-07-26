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
            text("DELETE FROM providers WHERE email LIKE :prefix"),
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


def create_role_and_user(connection, suffix: str) -> int:
    role_id = connection.scalar(
        text("INSERT INTO roles (name) VALUES (:name) RETURNING id"),
        {"name": f"{PREFIX}{suffix}-role"},
    )
    return connection.scalar(
        text(
            """
            INSERT INTO users (email, full_name, password_hash, active, role_id)
            VALUES (:email, :name, :password_hash, true, :role_id)
            RETURNING id
            """
        ),
        {
            "email": f"{PREFIX}{suffix}@example.invalid",
            "name": f"Synthetic {suffix}",
            "password_hash": password_hash(),
            "role_id": role_id,
        },
    )


def seed_single() -> None:
    engine = create_engine(database_url())
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO clinics (name, active) VALUES (:name, true)"),
            {"name": f"{PREFIX}single-clinic"},
        )
        create_role_and_user(connection, "single-a")
        create_role_and_user(connection, "single-b")


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
        assert provider_user and creator_user and verifier_user


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


def check_single() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        expected = clinic_id(connection, "single-clinic")
        assert memberships(connection, "single-a") == [expected]
        assert memberships(connection, "single-b") == [expected]
        assert connection.scalar(
            text(
                """
                SELECT count(*)
                FROM clinic_membership_migration_issues
                WHERE user_id IN (:first, :second)
                """
            ),
            {
                "first": user_id(connection, "single-a"),
                "second": user_id(connection, "single-b"),
            },
        ) == 0
    assert_route_scope("single-a", {expected})


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
        assert memberships(connection, "creator") == [clinic_b]
        assert memberships(connection, "verifier") == [clinic_b]
        assert memberships(connection, "ambiguous") == []
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
    assert_route_scope("creator", {clinic_b})
    assert_route_scope("verifier", {clinic_b})
    assert_route_scope("ambiguous", set())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("cleanup", "seed-single", "check-single", "seed-multi", "check-multi"),
    )
    args = parser.parse_args()
    {
        "cleanup": cleanup,
        "seed-single": seed_single,
        "check-single": check_single,
        "seed-multi": seed_multi,
        "check-multi": check_multi,
    }[args.action]()
