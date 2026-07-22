from __future__ import annotations

import argparse
import os

from sqlalchemy import create_engine, text


MARKER = "PR3-MIGRATION-"


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value


def seed() -> None:
    engine = create_engine(database_url())
    with engine.begin() as connection:
        institution_a = connection.scalar(
            text("INSERT INTO institutions (code, name, active) VALUES ('pr3-migration-a', 'PR3 Migration A', true) RETURNING id")
        )
        institution_b = connection.scalar(
            text("INSERT INTO institutions (code, name, active) VALUES ('pr3-migration-b', 'PR3 Migration B', true) RETURNING id")
        )
        clinic_a = connection.scalar(
            text("INSERT INTO clinics (name, timezone, institution_key, institution_id, active) VALUES ('PR3 Migration Clinic A', 'Europe/Zagreb', 'pr3-migration-a', :institution_id, true) RETURNING id"),
            {"institution_id": institution_a},
        )
        clinic_b = connection.scalar(
            text("INSERT INTO clinics (name, timezone, institution_key, institution_id, active) VALUES ('PR3 Migration Clinic B', 'Europe/Zagreb', 'pr3-migration-b', :institution_id, true) RETURNING id"),
            {"institution_id": institution_b},
        )
        patient = connection.scalar(
            text("INSERT INTO patients (first_name, last_name) VALUES ('PR3', 'Migration') RETURNING id")
        )
        provider = connection.scalar(
            text("INSERT INTO providers (full_name, active, weekly_working_hours, clinic_id) VALUES ('PR3 Migration Provider', true, '{}'::json, :clinic_id) RETURNING id"),
            {"clinic_id": clinic_b},
        )
        room = connection.scalar(
            text("INSERT INTO rooms (name, active, clinic_id) VALUES ('PR3 Migration Room', true, :clinic_id) RETURNING id"),
            {"clinic_id": clinic_b},
        )
        service = connection.scalar(
            text("INSERT INTO services (name, duration_minutes, price, active) VALUES ('PR3 Migration Service', 30, 1, true) RETURNING id")
        )
        appointment = connection.scalar(
            text(
                """
                INSERT INTO appointments
                    (patient_id, service_id, provider_id, room_id, clinic_id, date,
                     start_time, end_time, duration_minutes, status, source)
                VALUES
                    (:patient_id, :service_id, :provider_id, :room_id, :clinic_id,
                     DATE '2026-07-22', TIME '09:00', TIME '09:30', 30, 'scheduled', 'manual')
                RETURNING id
                """
            ),
            {
                "patient_id": patient,
                "service_id": service,
                "provider_id": provider,
                "room_id": room,
                "clinic_id": clinic_b,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO clinical_documents
                    (patient_id, clinic_id, appointment_id, source_type, document_type, title)
                VALUES
                    (:patient_id, :clinic_a, NULL, 'migration_test', 'other', :agreed),
                    (:patient_id, NULL, :appointment_id, 'migration_test', 'other', :appointment_only),
                    (:patient_id, NULL, NULL, 'migration_test', 'other', :unresolved),
                    (:patient_id, :clinic_a, :appointment_id, 'migration_test', 'other', :conflicting)
                """
            ),
            {
                "patient_id": patient,
                "clinic_a": clinic_a,
                "appointment_id": appointment,
                "agreed": f"{MARKER}AGREED",
                "appointment_only": f"{MARKER}APPOINTMENT",
                "unresolved": f"{MARKER}UNRESOLVED",
                "conflicting": f"{MARKER}CONFLICTING",
            },
        )


def check() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        rows = dict(
            connection.execute(
                text(
                    """
                    SELECT document.title, document.institution_id
                    FROM clinical_documents AS document
                    WHERE document.title LIKE :marker
                    """
                ),
                {"marker": f"{MARKER}%"},
            ).all()
        )
        expected_a = connection.scalar(text("SELECT id FROM institutions WHERE code = 'pr3-migration-a'"))
        expected_b = connection.scalar(text("SELECT id FROM institutions WHERE code = 'pr3-migration-b'"))
    assert rows[f"{MARKER}AGREED"] == expected_a
    assert rows[f"{MARKER}APPOINTMENT"] == expected_b
    assert rows[f"{MARKER}UNRESOLVED"] is None
    assert rows[f"{MARKER}CONFLICTING"] is None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("seed", "check"))
    args = parser.parse_args()
    seed() if args.action == "seed" else check()
