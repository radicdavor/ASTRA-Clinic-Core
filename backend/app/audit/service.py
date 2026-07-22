from typing import Any

from fastapi import Request
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.models.domain import AuditLog


SAFE_SNAPSHOT_FIELDS = frozenset(
    {
        "id",
        "patient_id",
        "clinic_id",
        "institution_id",
        "appointment_id",
        "journey_id",
        "episode_id",
        "activity_id",
        "service_id",
        "provider_id",
        "room_id",
        "invoice_id",
        "source_document_id",
        "status",
        "payment_status",
        "billing_status",
        "review_status",
        "lifecycle_status",
        "record_classification",
        "active",
        "physician_reviewed",
        "date",
        "start_time",
        "end_time",
        "duration_minutes",
        "quantity",
        "unit_price",
        "total",
        "created_at",
        "updated_at",
        "closed_at",
    }
)


def snapshot(obj: Any) -> dict[str, Any] | None:
    """Return an audit-safe operational projection, never a full ORM serialization."""
    if obj is None:
        return None
    result: dict[str, Any] = {}
    for column in inspect(obj).mapper.column_attrs:
        if column.key not in SAFE_SNAPSHOT_FIELDS:
            continue
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
    *,
    scope_type: str = "unscoped",
    clinic_id: int | None = None,
    institution_id: int | None = None,
) -> None:
    if request is not None and scope_type == "unscoped":
        request_clinic_id = getattr(request.state, "audit_clinic_id", None)
        if request_clinic_id is not None:
            scope_type = "clinic"
            clinic_id = request_clinic_id
            institution_id = getattr(request.state, "audit_institution_id", None)
    db.add(
        AuditLog(
            scope_type=scope_type,
            clinic_id=clinic_id,
            institution_id=institution_id,
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
