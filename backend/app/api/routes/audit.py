from fastapi import APIRouter, Depends, Request
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


@router.get("/audit-log")
def audit_log(
    request: Request,
    entity_type: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    actor_type: str | None = None,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("audit.read")),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)
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
    return items
