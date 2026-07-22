from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUserContext, require_active_clinic
from app.core.database import get_db
from app.models.domain import AuditLog
from app.schemas.common import ErrorResponse
from app.services.audit_access import SensitiveAccessEventIn, SensitiveAccessEventOut, audit_sensitive_access

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

router = APIRouter(prefix="/api", tags=["audit"], responses=ERROR_RESPONSES)


class ClinicAuditEventOut(BaseModel):
    """PHI-safe clinic audit projection; raw snapshots are intentionally excluded."""

    model_config = ConfigDict(extra="forbid")

    id: int
    scope_type: str
    clinic_id: int
    institution_id: int | None
    actor_type: str
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    request_id: str | None
    changed_fields: list[str]
    status: str | None
    reason_code: str | None
    created_at: datetime


def clinic_audit_projection(event: AuditLog) -> ClinicAuditEventOut:
    before_fields = set((event.before_json or {}).keys())
    after_fields = set((event.after_json or {}).keys())
    after = event.after_json or {}
    status = after.get("status")
    reason_code = after.get("reason_code")
    return ClinicAuditEventOut(
        id=event.id,
        scope_type="clinic",
        clinic_id=event.clinic_id,
        institution_id=event.institution_id,
        actor_type=event.actor_type,
        actor_user_id=event.actor_user_id,
        action=event.action,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        request_id=event.request_id,
        changed_fields=sorted(before_fields | after_fields),
        status=status if isinstance(status, str) else None,
        reason_code=reason_code if isinstance(reason_code, str) else None,
        created_at=event.created_at,
    )


@router.post("/audit/access-events", response_model=SensitiveAccessEventOut)
def record_sensitive_access_event(
    payload: SensitiveAccessEventIn,
    request: Request,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("audit.access_events.write")),
):
    event = audit_sensitive_access(db, payload, context, request)
    db.commit()
    db.refresh(event)
    return event


@router.get("/audit-log", response_model=list[ClinicAuditEventOut])
def audit_log(
    request: Request,
    entity_type: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    actor_type: str | None = None,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("audit.read")),
):
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.scope_type == "clinic",
            AuditLog.clinic_id == context.active_clinic_id,
            AuditLog.clinic_id.is_not(None),
        )
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(200)
    )
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor_type:
        stmt = stmt.where(AuditLog.actor_type == actor_type)
    items = db.scalars(stmt).all()
    audit_sensitive_access(
        db,
        SensitiveAccessEventIn(action="audit_log.viewed", entity_type="AuditLog", entity_id=None, surface="audit_viewer"),
        context,
        request,
        internal=True,
    )
    db.commit()
    return [clinic_audit_projection(item) for item in items]
