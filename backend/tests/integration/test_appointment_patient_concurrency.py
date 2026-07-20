from __future__ import annotations

from datetime import date, time
from queue import Empty, Queue
from threading import Event, Thread

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker

from app.models.domain import Appointment, Clinic, Patient, Provider, Room, Service
from app.services.appointments import validate_appointment_payload


pytestmark = pytest.mark.integration


APPOINTMENT_DATE = date(2026, 7, 6)


def _seed_concurrency_objects(db):
    patient = Patient(first_name="Concurrent", last_name="Patient")
    other_patient = Patient(first_name="Other", last_name="Patient")
    clinic_a = Clinic(name="Concurrency Clinic A")
    clinic_b = Clinic(name="Concurrency Clinic B")
    service = Service(name="Concurrency Service", duration_minutes=30, price=100)
    provider_a = Provider(
        full_name="dr. Concurrency A",
        specialty="QA",
        work_start=time(7, 0),
        work_end=time(20, 0),
        clinic=clinic_a,
    )
    provider_b = Provider(
        full_name="dr. Concurrency B",
        specialty="QA",
        work_start=time(7, 0),
        work_end=time(20, 0),
        clinic=clinic_b,
    )
    room_a = Room(name="Concurrency Room A", type="test", clinic=clinic_a)
    room_b = Room(name="Concurrency Room B", type="test", clinic=clinic_b)
    db.add_all([patient, other_patient, service, provider_a, provider_b, room_a, room_b])
    db.flush()
    ids = {
        "patient_id": patient.id,
        "other_patient_id": other_patient.id,
        "service_id": service.id,
        "provider_a_id": provider_a.id,
        "provider_b_id": provider_b.id,
        "room_a_id": room_a.id,
        "room_b_id": room_b.id,
        "clinic_a_id": clinic_a.id,
        "clinic_b_id": clinic_b.id,
    }
    db.commit()
    return ids


def _book_appointment(
    session_factory,
    *,
    results: Queue,
    ready: Event | None = None,
    inserted: Event | None = None,
    release: Event | None = None,
    **payload,
):
    with session_factory() as db:
        try:
            if ready:
                ready.set()
            duration = validate_appointment_payload(
                db,
                payload["date"],
                payload["start_time"],
                payload["end_time"],
                payload["provider_id"],
                payload["room_id"],
                "scheduled",
                "manual",
                service_id=payload["service_id"],
                patient_id=payload["patient_id"],
                appointment_id=payload.get("appointment_id"),
            )
            appointment = Appointment(
                patient_id=payload["patient_id"],
                provider_id=payload["provider_id"],
                room_id=payload["room_id"],
                clinic_id=payload["clinic_id"],
                service_id=payload["service_id"],
                date=payload["date"],
                start_time=payload["start_time"],
                end_time=payload["end_time"],
                duration_minutes=duration,
                status="scheduled",
                source="manual",
            )
            db.add(appointment)
            db.flush()
            if inserted:
                inserted.set()
            if release:
                release.wait(timeout=10)
            db.commit()
            results.put(("ok", appointment.id))
        except HTTPException as exc:
            db.rollback()
            results.put(("http_error", exc.status_code, exc.detail))
        except Exception as exc:  # pragma: no cover - keeps thread failures visible in pytest output
            db.rollback()
            results.put(("unexpected_error", repr(exc)))


def test_pg_serializes_overlapping_same_patient_creates(pg_db):
    ids = _seed_concurrency_objects(pg_db)
    session_factory = sessionmaker(bind=pg_db.get_bind(), expire_on_commit=False)
    results: Queue = Queue()
    first_inserted = Event()
    first_can_commit = Event()
    second_entered_service = Event()

    first_payload = {
        "patient_id": ids["patient_id"],
        "provider_id": ids["provider_a_id"],
        "room_id": ids["room_a_id"],
        "clinic_id": ids["clinic_a_id"],
        "service_id": ids["service_id"],
        "date": APPOINTMENT_DATE,
        "start_time": time(9, 0),
        "end_time": time(9, 30),
    }
    second_payload = {
        **first_payload,
        "provider_id": ids["provider_b_id"],
        "room_id": ids["room_b_id"],
        "clinic_id": ids["clinic_b_id"],
    }

    first = Thread(
        target=_book_appointment,
        kwargs={
            "session_factory": session_factory,
            "results": results,
            "inserted": first_inserted,
            "release": first_can_commit,
            **first_payload,
        },
    )
    first.start()
    assert first_inserted.wait(timeout=10)

    second = Thread(
        target=_book_appointment,
        kwargs={"session_factory": session_factory, "results": results, "ready": second_entered_service, **second_payload},
    )
    second.start()
    assert second_entered_service.wait(timeout=5)

    with pytest.raises(Empty):
        results.get(timeout=0.25)

    first_can_commit.set()
    outcomes = [results.get(timeout=10), results.get(timeout=10)]
    first.join(timeout=10)
    second.join(timeout=10)

    first_result = next(outcome for outcome in outcomes if outcome[0] == "ok")
    second_result = next(outcome for outcome in outcomes if outcome[0] == "http_error")
    assert first_result[0] == "ok"
    assert second_result[0] == "http_error"
    assert second_result[1] == 409
    assert second_result[2]["code"] == "patient_appointment_overlap"
    assert len(second_result[2]["conflicts"]) == 1
    assert pg_db.query(Appointment).count() == 1


def test_pg_allows_non_overlapping_same_patient_appointments(pg_db):
    ids = _seed_concurrency_objects(pg_db)
    session_factory = sessionmaker(bind=pg_db.get_bind(), expire_on_commit=False)
    results: Queue = Queue()

    first = Thread(
        target=_book_appointment,
        kwargs={
            "session_factory": session_factory,
            "results": results,
            "patient_id": ids["patient_id"],
            "provider_id": ids["provider_a_id"],
            "room_id": ids["room_a_id"],
            "clinic_id": ids["clinic_a_id"],
            "service_id": ids["service_id"],
            "date": APPOINTMENT_DATE,
            "start_time": time(9, 0),
            "end_time": time(9, 30),
        },
    )
    second = Thread(
        target=_book_appointment,
        kwargs={
            "session_factory": session_factory,
            "results": results,
            "patient_id": ids["patient_id"],
            "provider_id": ids["provider_b_id"],
            "room_id": ids["room_b_id"],
            "clinic_id": ids["clinic_b_id"],
            "service_id": ids["service_id"],
            "date": APPOINTMENT_DATE,
            "start_time": time(9, 30),
            "end_time": time(10, 0),
        },
    )

    first.start()
    second.start()
    outcomes = [results.get(timeout=10), results.get(timeout=10)]
    first.join(timeout=10)
    second.join(timeout=10)

    assert sorted(outcome[0] for outcome in outcomes) == ["ok", "ok"]
    assert pg_db.query(Appointment).count() == 2


def test_pg_allows_overlapping_different_patient_appointments(pg_db):
    ids = _seed_concurrency_objects(pg_db)
    session_factory = sessionmaker(bind=pg_db.get_bind(), expire_on_commit=False)
    results: Queue = Queue()

    first = Thread(
        target=_book_appointment,
        kwargs={
            "session_factory": session_factory,
            "results": results,
            "patient_id": ids["patient_id"],
            "provider_id": ids["provider_a_id"],
            "room_id": ids["room_a_id"],
            "clinic_id": ids["clinic_a_id"],
            "service_id": ids["service_id"],
            "date": APPOINTMENT_DATE,
            "start_time": time(11, 0),
            "end_time": time(11, 30),
        },
    )
    second = Thread(
        target=_book_appointment,
        kwargs={
            "session_factory": session_factory,
            "results": results,
            "patient_id": ids["other_patient_id"],
            "provider_id": ids["provider_b_id"],
            "room_id": ids["room_b_id"],
            "clinic_id": ids["clinic_b_id"],
            "service_id": ids["service_id"],
            "date": APPOINTMENT_DATE,
            "start_time": time(11, 0),
            "end_time": time(11, 30),
        },
    )

    first.start()
    second.start()
    outcomes = [results.get(timeout=10), results.get(timeout=10)]
    first.join(timeout=10)
    second.join(timeout=10)

    assert sorted(outcome[0] for outcome in outcomes) == ["ok", "ok"]
    assert pg_db.query(Appointment).count() == 2


def test_pg_patient_scheduling_lock_is_released_on_rollback(pg_db):
    ids = _seed_concurrency_objects(pg_db)
    session_factory = sessionmaker(bind=pg_db.get_bind(), expire_on_commit=False)

    with session_factory() as db:
        duration = validate_appointment_payload(
            db,
            APPOINTMENT_DATE,
            time(12, 0),
            time(12, 30),
            ids["provider_a_id"],
            ids["room_a_id"],
            "scheduled",
            "manual",
            service_id=ids["service_id"],
            patient_id=ids["patient_id"],
        )
        db.add(
            Appointment(
                patient_id=ids["patient_id"],
                provider_id=ids["provider_a_id"],
                room_id=ids["room_a_id"],
                clinic_id=ids["clinic_a_id"],
                service_id=ids["service_id"],
                date=APPOINTMENT_DATE,
                start_time=time(12, 0),
                end_time=time(12, 30),
                duration_minutes=duration,
                status="scheduled",
                source="manual",
            )
        )
        db.flush()
        db.rollback()

    with session_factory() as db:
        duration = validate_appointment_payload(
            db,
            APPOINTMENT_DATE,
            time(12, 0),
            time(12, 30),
            ids["provider_a_id"],
            ids["room_a_id"],
            "scheduled",
            "manual",
            service_id=ids["service_id"],
            patient_id=ids["patient_id"],
        )
        db.add(
            Appointment(
                patient_id=ids["patient_id"],
                provider_id=ids["provider_a_id"],
                room_id=ids["room_a_id"],
                clinic_id=ids["clinic_a_id"],
                service_id=ids["service_id"],
                date=APPOINTMENT_DATE,
                start_time=time(12, 0),
                end_time=time(12, 30),
                duration_minutes=duration,
                status="scheduled",
                source="manual",
            )
        )
        db.commit()

    assert pg_db.query(Appointment).count() == 1


def test_pg_update_uses_patient_overlap_validator(pg_db):
    ids = _seed_concurrency_objects(pg_db)
    session_factory = sessionmaker(bind=pg_db.get_bind(), expire_on_commit=False)

    first = Appointment(
        patient_id=ids["patient_id"],
        provider_id=ids["provider_a_id"],
        room_id=ids["room_a_id"],
        clinic_id=ids["clinic_a_id"],
        service_id=ids["service_id"],
        date=APPOINTMENT_DATE,
        start_time=time(13, 0),
        end_time=time(13, 30),
        duration_minutes=30,
        status="scheduled",
        source="manual",
    )
    candidate = Appointment(
        patient_id=ids["patient_id"],
        provider_id=ids["provider_b_id"],
        room_id=ids["room_b_id"],
        clinic_id=ids["clinic_b_id"],
        service_id=ids["service_id"],
        date=APPOINTMENT_DATE,
        start_time=time(14, 0),
        end_time=time(14, 30),
        duration_minutes=30,
        status="scheduled",
        source="manual",
    )
    pg_db.add_all([first, candidate])
    pg_db.commit()

    with session_factory() as db, pytest.raises(HTTPException) as exc_info:
        validate_appointment_payload(
            db,
            APPOINTMENT_DATE,
            time(13, 0),
            time(13, 30),
            ids["provider_b_id"],
            ids["room_b_id"],
            "scheduled",
            "manual",
            service_id=ids["service_id"],
            patient_id=ids["patient_id"],
            appointment_id=candidate.id,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "patient_appointment_overlap"
