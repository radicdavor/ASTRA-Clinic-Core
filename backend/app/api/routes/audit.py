from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit
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

SensitiveAccessAction = Literal[
    "patient.viewed",
    "clinical_workspace.opened",
    "clinical_form.viewed",
    "signed_report.viewed",
    "source_document.viewed",
    "source_document.downloaded",
    "billing_details.viewed",
    "patient_export.created",
    "clinical_report.printed",
    "audit_log.viewed",
]

SensitiveAccessEntity = Literal[
    "Patient",
    "PatientJourney",
    "ClinicalFormInstance",
    "SignedClinicalReport",
    "ClinicalDocument",
    "Invoice",
    "PatientExport",
    "AuditLog",
]

SensitiveAccessSurface = Literal[
    "patient_workspace",
    "clinical_workspace",
    "daily_dashboard",
    "document_center",
    "report_viewer",
    "billing_panel",
    "audit_viewer",
]

ACTION_ENTITY_MAP: dict[str, set[str]] = {
    "patient.viewed": {"Patient"},
    "clinical_workspace.opened": {"PatientJourney"},
    "clinical_form.viewed": {"ClinicalFormInstance"},
    "signed_report.viewed": {"SignedClinicalReport"},
    "source_document.viewed": {"ClinicalDocument"},
    "source_document.downloaded": {"ClinicalDocument"},
    "billing_details.viewed": {"Invoice", "PatientJourney"},
    "patient_export.created": {"PatientExport", "Patient"},
    "clinical_report.printed": {"SignedClinicalReport"},
    "audit_log.viewed": {"AuditLog"},
}


class SensitiveAccessEventIn(BaseModel):
    action: SensitiveAccessAction
    entity_type: SensitiveAccessEntity
    entity_id: int | None = Field(default=None, ge=1)
    surface: SensitiveAccessSurface
    clinic_id: int | None = Field(default=None, ge=1)
    journey_id: int | None = Field(default=None, ge=1)


class SensitiveAccessEventOut(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: int | None


def _audit_sensitive_access(
    db: Session,
    payload: SensitiveAccessEventIn,
    actor: Actor,
    request: Request | None,
) -> AuditLog:
    allowed_entities = ACTION_ENTITY_MAP[payload.action]
    if payload.entity_type not in allowed_entities:
        raise HTTPException(status_code=422, detail="Audit događaj ne odgovara vrsti objekta")

    safe_payload = {
        "surface": payload.surface,
        "clinic_id": payload.clinic_id,
        "journey_id": payload.journey_id,
    }
    audit(
        db,
        payload.action,
        payload.entity_type,
        payload.entity_id,
        f"Sensitive access event: {payload.action}",
        actor.user_id,
        actor.actor_type,
        actor.api_key_id,
        None,
        safe_payload,
        request,
    )
    db.flush()
    return db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(1)).one()


@router.post("/audit/access-events", response_model=SensitiveAccessEventOut)
def record_sensitive_access_event(
    payload: SensitiveAccessEventIn,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("audit.access_events.write")),
):
    event = _audit_sensitive_access(db, payload, actor, request)
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
    items = db.scalars(stmt).all()
    _audit_sensitive_access(
        db,
        SensitiveAccessEventIn(action="audit_log.viewed", entity_type="AuditLog", entity_id=None, surface="audit_viewer"),
        actor,
        request,
    )
    db.commit()
    return items
