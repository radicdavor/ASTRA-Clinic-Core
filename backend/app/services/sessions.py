from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from hmac import compare_digest
from secrets import token_urlsafe
import logging
import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.domain import AuditLog, User, UserSession


logger = logging.getLogger(__name__)
SESSION_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{64}$")


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
    db.add(
        AuditLog(
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
) -> bool:
    """Persist sanitized authentication metadata outside the request transaction."""
    AuditSession = sessionmaker(bind=bind, expire_on_commit=False)
    try:
        with AuditSession.begin() as audit_db:
            audit_db.add(
                AuditLog(
                    actor_type="user" if user_id else "system",
                    actor_user_id=user_id,
                    action=action,
                    entity_type="user_session",
                    entity_id=session_id,
                    summary="Browser session security event.",
                    request_id=request_id,
                    after_json={"reason_code": reason_code, "method": method, "route": route},
                )
            )
        return True
    except Exception as exc:
        logger.error(
            "Security audit persistence failed; request_id=%s action=%s error_type=%s",
            request_id,
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
