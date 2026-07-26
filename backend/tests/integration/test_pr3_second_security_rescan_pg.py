from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, UTC

import pytest

from app.core.security import hash_password
from app.models.domain import AuditLog, Role, User
from app.services.sessions import write_security_audit_event


pytestmark = pytest.mark.integration


def test_all_bounded_security_event_classes_are_retention_eligible(pg_db):
    old = datetime.now(UTC) - timedelta(days=91)
    actions = (
        ("auth.browser_session_invalid", "unknown"),
        ("auth.browser_csrf_invalid", "session_hash_mismatch"),
        ("auth.browser_credential_conflict", "active"),
    )
    for action, reason in actions:
        assert write_security_audit_event(
            pg_db.get_bind(),
            action,
            reason_code=reason,
            method="GET",
            route="/auth/session",
            occurred_at=old,
        )

    assert write_security_audit_event(
        pg_db.get_bind(),
        "auth.browser_session_invalid",
        reason_code="unknown",
        method="GET",
        route="/auth/session",
    )

    pg_db.expire_all()
    events = pg_db.query(AuditLog).all()
    assert len(events) == 1
    assert events[0].action == "auth.browser_session_invalid"
    last_seen_at = events[0].last_seen_at
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=UTC)
    assert last_seen_at > old


def test_postgresql_bounded_audit_upsert_is_atomic_and_actor_separated(pg_db):
    role = Role(name="audit-test-role", description="Synthetic audit concurrency role")
    pg_db.add(role)
    pg_db.flush()
    first = User(
        email="audit-first@test.local",
        full_name="Audit First",
        password_hash=hash_password("synthetic"),
        role_id=role.id,
    )
    second = User(
        email="audit-second@test.local",
        full_name="Audit Second",
        password_hash=hash_password("synthetic"),
        role_id=role.id,
    )
    pg_db.add_all([first, second])
    pg_db.commit()
    bind = pg_db.get_bind()
    occurred_at = datetime.now(UTC).replace(second=0, microsecond=0)

    def write_first():
        return write_security_audit_event(
            bind,
            "auth.browser_csrf_invalid",
            user_id=first.id,
            reason_code="session_hash_mismatch",
            method="POST",
            route="/api/patients",
            occurred_at=occurred_at,
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert all(pool.map(lambda _index: write_first(), range(100)))

    assert write_security_audit_event(
        bind,
        "auth.browser_csrf_invalid",
        user_id=second.id,
        reason_code="session_hash_mismatch",
        method="POST",
        route="/api/patients",
        occurred_at=occurred_at,
    )
    pg_db.expire_all()
    events = pg_db.query(AuditLog).filter(AuditLog.action == "auth.browser_csrf_invalid").all()
    assert len(events) == 2
    counts = {event.actor_user_id: event.occurrence_count for event in events}
    assert counts == {first.id: 100, second.id: 1}
    assert all(event.aggregation_key for event in events)
