from __future__ import annotations

from datetime import UTC, datetime, timedelta
from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
from secrets import token_urlsafe
import logging
import re
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.domain import AuditLog, User, UserSession
from app.services.request_ids import normalize_request_id


logger = logging.getLogger(__name__)
SESSION_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{64}$")
ANONYMOUS_AUDIT_WINDOW_MINUTES = 5
ANONYMOUS_AUDIT_RETENTION_DAYS = 90
SECURITY_AUDIT_CLEANUP_BATCH_SIZE = 100
SECURITY_AUDIT_REASON_CODES = frozenset(
    {
        "missing",
        "malformed",
        "unknown",
        "revoked",
        "expired",
        "inactive_user",
        "active",
        "session_hash_mismatch",
    }
)


@dataclass(frozen=True)
class SecurityAuditEventPolicy:
    action: str
    persistence_mode: Literal["individual", "bounded_counter"]
    aggregation_window_minutes: int | None
    retention_days: int | None
    include_actor_identity_in_key: bool


SECURITY_AUDIT_EVENT_POLICIES: dict[str, SecurityAuditEventPolicy] = {
    **{
        action: SecurityAuditEventPolicy(
            action=action,
            persistence_mode="individual",
            aggregation_window_minutes=None,
            retention_days=None,
            include_actor_identity_in_key=True,
        )
        for action in (
            "auth.browser_login_success",
            "auth.browser_logout",
            "auth.browser_session_revoked",
        )
    },
    **{
        action: SecurityAuditEventPolicy(
            action=action,
            persistence_mode="bounded_counter",
            aggregation_window_minutes=ANONYMOUS_AUDIT_WINDOW_MINUTES,
            retention_days=ANONYMOUS_AUDIT_RETENTION_DAYS,
            include_actor_identity_in_key=True,
        )
        for action in (
            "auth.browser_session_invalid",
            "auth.browser_csrf_invalid",
            "auth.browser_credential_conflict",
        )
    },
}


def _security_audit_policy(action: str) -> SecurityAuditEventPolicy:
    policy = SECURITY_AUDIT_EVENT_POLICIES.get(action)
    if policy is None:
        raise ValueError("Security audit action has no persistence policy")
    return policy


def _safe_reason_code(value: str) -> str:
    return value if value in SECURITY_AUDIT_REASON_CODES else "unknown"


def _safe_http_method(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.upper()
    return normalized if normalized in {"GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"} else None


def _safe_route_template(value: str | None) -> str | None:
    if value is None or len(value) > 160 or not value.startswith("/"):
        return None
    return value if re.fullmatch(r"/[A-Za-z0-9_{}./:-]*", value) else None


def hash_session_secret(raw: str) -> str:
    return sha256(raw.encode("utf-8")).hexdigest()


def create_user_session(db: Session, user: User) -> tuple[UserSession, str, str]:
    settings = get_settings()
    raw_session_token = token_urlsafe(48)
    raw_csrf_token = token_urlsafe(32)
    now = datetime.now(UTC)
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_secret(raw_session_token),
        csrf_token_hash=hash_session_secret(raw_csrf_token),
        created_at=now,
        expires_at=now + timedelta(minutes=settings.browser_session_minutes),
        last_seen_at=now,
    )
    db.add(session)
    db.flush()
    record_session_audit(db, "auth.browser_login_success", user_id=user.id, session_id=session.id)
    return session, raw_session_token, raw_csrf_token


def get_valid_session(db: Session, raw_session_token: str | None, *, touch: bool = True) -> UserSession | None:
    if not raw_session_token:
        return None
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_session_secret(raw_session_token)))
    if not session:
        return None
    now = datetime.now(UTC)
    revoked_at = session.revoked_at.replace(tzinfo=UTC) if session.revoked_at and session.revoked_at.tzinfo is None else session.revoked_at
    expires_at = session.expires_at.replace(tzinfo=UTC) if session.expires_at.tzinfo is None else session.expires_at
    if revoked_at is not None or expires_at <= now:
        return None
    if not session.user or not session.user.active:
        return None
    if touch:
        session.last_seen_at = now
        db.flush()
    return session


def revoke_session(db: Session, session: UserSession | None) -> bool:
    if session is None or session.revoked_at is not None:
        return False
    session.revoked_at = datetime.now(UTC)
    db.flush()
    record_session_audit(db, "auth.browser_logout", user_id=session.user_id, session_id=session.id)
    return True


def revoke_all_user_sessions(db: Session, user_id: int, *, except_session_id: int | None = None) -> int:
    sessions = db.scalars(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            *([] if except_session_id is None else [UserSession.id != except_session_id]),
        )
    ).all()
    now = datetime.now(UTC)
    for session in sessions:
        session.revoked_at = now
        record_session_audit(db, "auth.browser_session_revoked", user_id=user_id, session_id=session.id)
    db.flush()
    return len(sessions)


def cleanup_expired_sessions(db: Session, *, older_than: datetime | None = None) -> int:
    cutoff = older_than or datetime.now(UTC)
    result = db.execute(delete(UserSession).where(UserSession.expires_at < cutoff, UserSession.revoked_at.is_not(None)))
    return int(result.rowcount or 0)


def csrf_token_matches(session: UserSession, raw_csrf_token: str | None) -> bool:
    return bool(raw_csrf_token) and compare_digest(hash_session_secret(raw_csrf_token), session.csrf_token_hash)


def record_session_audit(db: Session, action: str, *, user_id: int | None = None, session_id: int | None = None, summary: str | None = None) -> None:
    policy = _security_audit_policy(action)
    if policy.persistence_mode != "individual":
        raise ValueError("Bounded security audit actions require independent persistence")
    db.add(
        AuditLog(
            scope_type="system_security",
            actor_type="user" if user_id else "system",
            actor_user_id=user_id,
            action=action,
            entity_type="user_session",
            entity_id=session_id,
            summary=summary,
        )
    )


def write_security_audit_event(
    bind,
    action: str,
    *,
    user_id: int | None = None,
    session_id: int | None = None,
    reason_code: str,
    request_id: str | None = None,
    method: str | None = None,
    route: str | None = None,
    aggregate_anonymous: bool = False,
    occurred_at: datetime | None = None,
) -> bool:
    """Persist sanitized authentication metadata outside the request transaction."""
    AuditSession = sessionmaker(bind=bind, expire_on_commit=False)
    canonical_request_id = normalize_request_id(request_id)
    try:
        with AuditSession.begin() as audit_db:
            now = occurred_at or datetime.now(UTC)
            policy = _security_audit_policy(action)
            safe_reason = _safe_reason_code(reason_code)
            safe_method = _safe_http_method(method)
            safe_route = _safe_route_template(route)
            values = {
                "scope_type": "system_security",
                "actor_type": "user" if user_id else "system",
                "actor_user_id": user_id,
                "action": action,
                "entity_type": "user_session",
                "entity_id": session_id,
                "summary": "Browser session security event.",
                "request_id": canonical_request_id,
                "after_json": {"reason_code": safe_reason, "method": safe_method, "route": safe_route},
                "occurrence_count": 1,
                "first_seen_at": now,
                "last_seen_at": now,
            }
            if policy.persistence_mode == "bounded_counter":
                window = policy.aggregation_window_minutes or ANONYMOUS_AUDIT_WINDOW_MINUTES
                bucket_minute = (now.minute // window) * window
                bucket = now.replace(minute=bucket_minute, second=0, microsecond=0)
                actor_material = f"{user_id or ''}|{session_id or ''}" if policy.include_actor_identity_in_key else ""
                safe_material = (
                    f"{action}|{safe_reason}|{safe_method or ''}|{safe_route or ''}|"
                    f"{actor_material}|{bucket.isoformat()}"
                )
                values["aggregation_key"] = sha256(safe_material.encode("utf-8")).hexdigest()
                values["request_id"] = None
                dialect_name = audit_db.get_bind().dialect.name
                insert_factory = postgresql_insert if dialect_name == "postgresql" else sqlite_insert if dialect_name == "sqlite" else None
                if insert_factory is None:
                    raise RuntimeError(f"Unsupported audit aggregation dialect: {dialect_name}")
                statement = insert_factory(AuditLog).values(**values)
                statement = statement.on_conflict_do_update(
                    index_elements=[AuditLog.aggregation_key],
                    set_={
                        "occurrence_count": AuditLog.occurrence_count + 1,
                        "last_seen_at": now,
                    },
                )
                audit_db.execute(statement)
                cutoff = now - timedelta(days=policy.retention_days or ANONYMOUS_AUDIT_RETENTION_DAYS)
                expired_ids = (
                    select(AuditLog.id)
                    .where(
                        AuditLog.aggregation_key.is_not(None),
                        AuditLog.last_seen_at.is_not(None),
                        AuditLog.last_seen_at < cutoff,
                    )
                    .order_by(AuditLog.last_seen_at, AuditLog.id)
                    .limit(SECURITY_AUDIT_CLEANUP_BATCH_SIZE)
                )
                audit_db.execute(
                    delete(AuditLog).where(AuditLog.id.in_(expired_ids))
                )
            else:
                audit_db.add(AuditLog(**values))
        return True
    except Exception as exc:
        logger.error(
            "Security audit persistence failed; request_id=%s action=%s error_type=%s",
            canonical_request_id,
            action,
            type(exc).__name__,
        )
        return False


def invalid_session_context(db: Session, raw_session_token: str | None) -> tuple[int | None, int | None, str]:
    if not raw_session_token:
        return None, None, "missing"
    if not SESSION_TOKEN_PATTERN.fullmatch(raw_session_token):
        return None, None, "malformed"
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_session_secret(raw_session_token)))
    if session is None:
        return None, None, "unknown"
    now = datetime.now(UTC)
    revoked_at = session.revoked_at.replace(tzinfo=UTC) if session.revoked_at and session.revoked_at.tzinfo is None else session.revoked_at
    expires_at = session.expires_at.replace(tzinfo=UTC) if session.expires_at.tzinfo is None else session.expires_at
    if revoked_at is not None:
        reason = "revoked"
    elif expires_at <= now:
        reason = "expired"
    elif not session.user or not session.user.active:
        reason = "inactive_user"
    else:
        reason = "active"
    return session.user_id, session.id, reason


def write_invalid_session_audit(db: Session, raw_session_token: str | None, request) -> None:
    user_id, session_id, reason = invalid_session_context(db, raw_session_token)
    route_object = request.scope.get("route")
    route = getattr(route_object, "path", None)
    write_security_audit_event(
        db.get_bind(),
        "auth.browser_session_invalid",
        user_id=user_id,
        session_id=session_id,
        reason_code=reason,
        request_id=getattr(request.state, "request_id", None),
        method=request.method,
        route=route,
        aggregate_anonymous=user_id is None and session_id is None,
    )


def write_invalid_csrf_audit(db: Session, session: UserSession, request) -> None:
    route_object = request.scope.get("route")
    write_security_audit_event(
        db.get_bind(),
        "auth.browser_csrf_invalid",
        user_id=session.user_id,
        session_id=session.id,
        reason_code="session_hash_mismatch",
        request_id=getattr(request.state, "request_id", None),
        method=request.method,
        route=getattr(route_object, "path", None),
    )


def write_credential_conflict_audit(db: Session, raw_session_token: str | None, request) -> None:
    user_id, session_id, session_state = invalid_session_context(db, raw_session_token)
    route_object = request.scope.get("route")
    write_security_audit_event(
        db.get_bind(),
        "auth.browser_credential_conflict",
        user_id=user_id,
        session_id=session_id,
        reason_code=session_state,
        request_id=getattr(request.state, "request_id", None),
        method=request.method,
        route=getattr(route_object, "path", None),
    )
