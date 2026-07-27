from __future__ import annotations

import argparse
import os

from sqlalchemy import create_engine, text


PREFIX = "PR3-SCOPE-MIGRATION-"


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value


def seed() -> None:
    engine = create_engine(database_url())
    with engine.begin() as connection:
        institution_a = connection.scalar(text("INSERT INTO institutions (code, name, active) VALUES ('pr3-scope-a', 'PR3 Scope A', true) RETURNING id"))
        institution_b = connection.scalar(text("INSERT INTO institutions (code, name, active) VALUES ('pr3-scope-b', 'PR3 Scope B', true) RETURNING id"))
        clinic_a = connection.scalar(text("INSERT INTO clinics (name, timezone, institution_key, institution_id, active) VALUES ('PR3 Scope Clinic A', 'Europe/Zagreb', 'pr3-scope-a', :institution_id, true) RETURNING id"), {"institution_id": institution_a})
        clinic_b = connection.scalar(text("INSERT INTO clinics (name, timezone, institution_key, institution_id, active) VALUES ('PR3 Scope Clinic B', 'Europe/Zagreb', 'pr3-scope-b', :institution_id, true) RETURNING id"), {"institution_id": institution_b})
        patient = connection.scalar(text("INSERT INTO patients (first_name, last_name) VALUES ('PR3', 'Scope Migration') RETURNING id"))
        provider = connection.scalar(text("INSERT INTO providers (full_name, active, weekly_working_hours) VALUES ('PR3 Scope Provider', true, '{}'::json) RETURNING id"))
        room_a = connection.scalar(text("INSERT INTO rooms (name, active, clinic_id) VALUES ('PR3 Scope Room A', true, :clinic_id) RETURNING id"), {"clinic_id": clinic_a})
        room_b = connection.scalar(text("INSERT INTO rooms (name, active, clinic_id) VALUES ('PR3 Scope Room B', true, :clinic_id) RETURNING id"), {"clinic_id": clinic_b})
        service = connection.scalar(text("INSERT INTO services (name, duration_minutes, price, active) VALUES ('PR3 Scope Service', 30, 1, true) RETURNING id"))
        resolved_episode = connection.scalar(text("INSERT INTO clinical_episodes (patient_id, title, start_date) VALUES (:patient_id, :title, DATE '2026-07-22') RETURNING id"), {"patient_id": patient, "title": f"{PREFIX}RESOLVED"})
        conflicting_episode = connection.scalar(text("INSERT INTO clinical_episodes (patient_id, title, start_date) VALUES (:patient_id, :title, DATE '2026-07-22') RETURNING id"), {"patient_id": patient, "title": f"{PREFIX}CONFLICTING"})

        def appointment(clinic_id: int, room_id: int, episode_id: int, start: str) -> int:
            return connection.scalar(text("""
                INSERT INTO appointments
                    (patient_id, service_id, provider_id, room_id, clinic_id, episode_id, date,
                     start_time, end_time, duration_minutes, status, source)
                VALUES (:patient_id, :service_id, :provider_id, :room_id, :clinic_id, :episode_id,
                        DATE '2026-07-22', CAST(:start AS time), CAST(:start AS time) + INTERVAL '30 minutes',
                        30, 'scheduled', 'manual') RETURNING id
            """), {"patient_id": patient, "service_id": service, "provider_id": provider, "room_id": room_id, "clinic_id": clinic_id, "episode_id": episode_id, "start": start})

        appointment_a = appointment(clinic_a, room_a, resolved_episode, "09:00")
        appointment(clinic_a, room_a, conflicting_episode, "10:00")
        appointment_b = appointment(clinic_b, room_b, conflicting_episode, "11:00")
        connection.execute(text("INSERT INTO lab_orders (patient_id, appointment_id, episode_id, ordered_at, notes) VALUES (:patient_id, :appointment_id, :episode_id, DATE '2026-07-22', :note)"), {"patient_id": patient, "appointment_id": appointment_a, "episode_id": resolved_episode, "note": f"{PREFIX}LAB-RESOLVED"})
        connection.execute(text("INSERT INTO lab_orders (patient_id, appointment_id, episode_id, ordered_at, notes) VALUES (:patient_id, :appointment_id, :episode_id, DATE '2026-07-22', :note)"), {"patient_id": patient, "appointment_id": appointment_b, "episode_id": resolved_episode, "note": f"{PREFIX}LAB-CONFLICTING"})
        connection.execute(text("INSERT INTO therapies (patient_id, episode_id, name, instructions, start_date) VALUES (:patient_id, :episode_id, :name, 'Synthetic', DATE '2026-07-22')"), {"patient_id": patient, "episode_id": resolved_episode, "name": f"{PREFIX}THERAPY"})
        connection.execute(text("INSERT INTO workflow_tasks (title, patient_id, appointment_id, episode_id) VALUES (:title, :patient_id, :appointment_id, :episode_id)"), {"title": f"{PREFIX}TASK-RESOLVED", "patient_id": patient, "appointment_id": appointment_a, "episode_id": resolved_episode})
        connection.execute(text("INSERT INTO workflow_tasks (title, patient_id, appointment_id, episode_id) VALUES (:title, :patient_id, :appointment_id, :episode_id)"), {"title": f"{PREFIX}TASK-CONFLICTING", "patient_id": patient, "appointment_id": appointment_b, "episode_id": resolved_episode})
        connection.execute(text("INSERT INTO api_keys (name, key_hash, active, scopes) VALUES (:name, :hash, true, '[]'::json)"), {"name": f"{PREFIX}LEGACY-KEY", "hash": "pr3-scope-migration-key-hash"})


def check() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        institution_a = connection.scalar(text("SELECT id FROM institutions WHERE code = 'pr3-scope-a'"))
        episode_rows = dict(connection.execute(text("SELECT title, institution_id FROM clinical_episodes WHERE title LIKE :prefix"), {"prefix": f"{PREFIX}%"}).all())
        lab_rows = dict(connection.execute(text("SELECT notes, institution_id FROM lab_orders WHERE notes LIKE :prefix"), {"prefix": f"{PREFIX}%"}).all())
        therapy_scope = connection.scalar(text("SELECT institution_id FROM therapies WHERE name = :name"), {"name": f"{PREFIX}THERAPY"})
        task_rows = dict(connection.execute(text("SELECT title, institution_id FROM workflow_tasks WHERE title LIKE :prefix"), {"prefix": f"{PREFIX}%"}).all())
        legacy_key_scope = connection.execute(text("SELECT clinic_id, institution_id FROM api_keys WHERE name = :name"), {"name": f"{PREFIX}LEGACY-KEY"}).one()
    assert episode_rows[f"{PREFIX}RESOLVED"] == institution_a
    assert episode_rows[f"{PREFIX}CONFLICTING"] is None
    assert lab_rows[f"{PREFIX}LAB-RESOLVED"] == institution_a
    assert lab_rows[f"{PREFIX}LAB-CONFLICTING"] is None
    assert therapy_scope == institution_a
    assert task_rows[f"{PREFIX}TASK-RESOLVED"] == institution_a
    assert task_rows[f"{PREFIX}TASK-CONFLICTING"] is None
    assert legacy_key_scope == (None, None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("seed", "check"))
    args = parser.parse_args()
    seed() if args.action == "seed" else check()
