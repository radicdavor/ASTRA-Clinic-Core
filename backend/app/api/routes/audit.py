from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import AuditLog
from app.schemas.common import ErrorResponse

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

router = APIRouter(prefix="/api", tags=["audit"], responses=ERROR_RESPONSES)


@router.get("/audit-log")
def audit_log(
    entity_type: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    actor_type: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("audit.read")),
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
    return db.scalars(stmt).all()
