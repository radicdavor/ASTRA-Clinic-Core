from typing import Any

from fastapi import Request
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.models.domain import AuditLog


def snapshot(obj: Any) -> dict[str, Any] | None:
    if obj is None:
        return None
    result: dict[str, Any] = {}
    for column in inspect(obj).mapper.column_attrs:
        value = getattr(obj, column.key)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        elif hasattr(value, "__str__") and value.__class__.__module__ == "decimal":
            value = str(value)
        result[column.key] = value
    return result


def audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    summary: str | None = None,
    actor_user_id: int | None = None,
    actor_type: str = "user",
    actor_api_key_id: int | None = None,
    before_json: dict[str, Any] | None = None,
    after_json: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            actor_api_key_id=actor_api_key_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_json=before_json,
            after_json=after_json,
            summary=summary,
            request_id=getattr(request.state, "request_id", None) if request else None,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )
