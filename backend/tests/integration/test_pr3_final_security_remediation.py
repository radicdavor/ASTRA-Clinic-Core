from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Event

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.audit.service import audit
from app.models.domain import AuditLog
from app.services.sessions import write_security_audit_event


pytestmark = pytest.mark.integration


def test_postgresql_anonymous_audit_aggregation_is_concurrency_safe(pg_db):
    bind = pg_db.get_bind()
    occurred_at = datetime.now(UTC).replace(second=0, microsecond=0)

    def write_probe(_index: int) -> bool:
        return write_security_audit_event(
            bind,
            "auth.browser_session_invalid",
            reason_code="unknown",
            method="GET",
            route="/auth/session",
            aggregate_anonymous=True,
            occurred_at=occurred_at,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(write_probe, range(40)))

    assert all(results)
    pg_db.expire_all()
    events = pg_db.scalars(
        select(AuditLog).where(AuditLog.action == "auth.browser_session_invalid")
    ).all()
    assert len(events) == 1
    assert events[0].occurrence_count == 40
    assert events[0].aggregation_key is not None


def test_postgresql_audit_creation_keeps_exact_flushed_object_across_later_commit(pg_db):
    bind = pg_db.get_bind()
    SessionLocal = sessionmaker(bind=bind, expire_on_commit=False)
    first_flushed = Event()
    second_committed = Event()
    results: dict[str, tuple[int, str]] = {}

    def first_writer() -> None:
        with SessionLocal.begin() as session:
            event = audit(session, "first_event", "Appointment", 101)
            session.flush()
            first_flushed.set()
            assert second_committed.wait(timeout=10)
            results["first"] = (event.id, event.action)

    def second_writer() -> None:
        assert first_flushed.wait(timeout=10)
        with SessionLocal.begin() as session:
            event = audit(session, "second_event", "Appointment", 202)
            session.flush()
            results["second"] = (event.id, event.action)
        second_committed.set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(first_writer)
        second = executor.submit(second_writer)
        first.result(timeout=20)
        second.result(timeout=20)

    assert results["first"][1] == "first_event"
    assert results["second"][1] == "second_event"
    assert results["first"][0] != results["second"][0]
