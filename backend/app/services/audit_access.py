from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit
from app.auth.dependencies import CurrentUserContext, get_scoped_patient
from app.models.domain import (
    AuditLog,
    ClinicalDocument,
    ClinicalFormInstance,
    Invoice,
    JourneyActivity,
    PatientJourney,
    SignedClinicalReport,
)


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


class SensitiveAccessEventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: SensitiveAccessAction
    entity_type: SensitiveAccessEntity
    entity_id: int | None = Field(default=None, ge=1)
    surface: SensitiveAccessSurface
    interaction_id: str | None = Field(default=None, min_length=8, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")


class SensitiveAccessEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    entity_type: str
    entity_id: int | None


@dataclass(frozen=True)
class AuditAccessEventDefinition:
    action: str
    entity_types: frozenset[str]
    required_permission: str
    enabled_for_direct_endpoint: bool = True


ACCESS_EVENT_DEFINITIONS: dict[str, AuditAccessEventDefinition] = {
    "patient.viewed": AuditAccessEventDefinition("patient.viewed", frozenset({"Patient"}), "patients.read"),
    "clinical_workspace.opened": AuditAccessEventDefinition(
        "clinical_workspace.opened",
        frozenset({"PatientJourney"}),
        "encounter.read",
    ),
    "clinical_form.viewed": AuditAccessEventDefinition(
        "clinical_form.viewed",
        frozenset({"ClinicalFormInstance"}),
        "clinical_forms.read",
    ),
    "signed_report.viewed": AuditAccessEventDefinition(
        "signed_report.viewed",
        frozenset({"SignedClinicalReport"}),
        "reports.read",
    ),
    "source_document.viewed": AuditAccessEventDefinition(
        "source_document.viewed",
        frozenset({"ClinicalDocument"}),
        "documents.view_source",
    ),
    "source_document.downloaded": AuditAccessEventDefinition(
        "source_document.downloaded",
        frozenset({"ClinicalDocument"}),
        "documents.view_source",
    ),
    "billing_details.viewed": AuditAccessEventDefinition(
        "billing_details.viewed",
        frozenset({"Invoice", "PatientJourney"}),
        "billing.read",
    ),
    "patient_export.created": AuditAccessEventDefinition(
        "patient_export.created",
        frozenset({"PatientExport"}),
        "patients.read",
        enabled_for_direct_endpoint=False,
    ),
    "clinical_report.printed": AuditAccessEventDefinition(
        "clinical_report.printed",
        frozenset({"SignedClinicalReport"}),
        "reports.print",
    ),
    "audit_log.viewed": AuditAccessEventDefinition("audit_log.viewed", frozenset({"AuditLog"}), "audit.read"),
}


def _ensure_event_permission(context: CurrentUserContext, definition: AuditAccessEventDefinition) -> None:
    if definition.required_permission not in context.permissions:
        raise HTTPException(status_code=403, detail=f"Nedostaje dozvola: {definition.required_permission}")


def _not_found() -> None:
    raise HTTPException(status_code=404, detail="Objekt nije pronađen")


def _scoped_journey(db: Session, journey_id: int, clinic_id: int) -> PatientJourney:
    journey = db.scalar(select(PatientJourney).where(PatientJourney.id == journey_id, PatientJourney.clinic_id == clinic_id))
    if journey is None:
        _not_found()
    return journey


def _scoped_form_instance(db: Session, instance_id: int, clinic_id: int) -> ClinicalFormInstance:
    item = db.scalar(
        select(ClinicalFormInstance)
        .join(JourneyActivity, JourneyActivity.id == ClinicalFormInstance.activity_id)
        .join(PatientJourney, PatientJourney.id == JourneyActivity.journey_id)
        .where(ClinicalFormInstance.id == instance_id, PatientJourney.clinic_id == clinic_id)
    )
    if item is None:
        _not_found()
    return item


def _scoped_signed_report(db: Session, report_id: int, clinic_id: int) -> SignedClinicalReport:
    item = db.scalar(
        select(SignedClinicalReport)
        .join(PatientJourney, PatientJourney.id == SignedClinicalReport.journey_id)
        .where(SignedClinicalReport.id == report_id, PatientJourney.clinic_id == clinic_id)
    )
    if item is None:
        _not_found()
    return item


def _scoped_document(db: Session, document_id: int, clinic_id: int) -> ClinicalDocument:
    document = db.get(ClinicalDocument, document_id)
    if document is None:
        _not_found()
    if document.clinic_id == clinic_id:
        return document
    if document.journey_id is not None:
        _scoped_journey(db, document.journey_id, clinic_id)
        return document
    _not_found()


def _scoped_invoice(db: Session, invoice_id: int, clinic_id: int) -> Invoice:
    invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id, Invoice.clinic_id == clinic_id))
    if invoice is None:
        _not_found()
    return invoice


def _resolve_scoped_entity(db: Session, payload: SensitiveAccessEventIn, context: CurrentUserContext) -> tuple[int | None, int | None]:
    if context.active_clinic_id is None:
        raise HTTPException(status_code=403, detail="Aktivna klinika nije razriješena")
    clinic_id = context.active_clinic_id
    if payload.action == "audit_log.viewed":
        return payload.entity_id, clinic_id
    if payload.entity_id is None:
        raise HTTPException(status_code=422, detail="ID objekta je obavezan za audit događaj")

    if payload.entity_type == "Patient":
        get_scoped_patient(db, payload.entity_id, context)
        return payload.entity_id, clinic_id
    if payload.entity_type == "PatientJourney":
        journey = _scoped_journey(db, payload.entity_id, clinic_id)
        return journey.id, journey.clinic_id
    if payload.entity_type == "ClinicalFormInstance":
        item = _scoped_form_instance(db, payload.entity_id, clinic_id)
        activity = db.get(JourneyActivity, item.activity_id)
        return item.id, activity.journey.clinic_id if activity and activity.journey else clinic_id
    if payload.entity_type == "SignedClinicalReport":
        item = _scoped_signed_report(db, payload.entity_id, clinic_id)
        journey = db.get(PatientJourney, item.journey_id)
        return item.id, journey.clinic_id if journey else clinic_id
    if payload.entity_type == "ClinicalDocument":
        item = _scoped_document(db, payload.entity_id, clinic_id)
        return item.id, item.clinic_id or clinic_id
    if payload.entity_type == "Invoice":
        item = _scoped_invoice(db, payload.entity_id, clinic_id)
        return item.id, item.clinic_id

    raise HTTPException(status_code=422, detail="Nepodržana vrsta objekta za audit događaj")


def _find_duplicate_interaction(
    db: Session,
    payload: SensitiveAccessEventIn,
    context: CurrentUserContext,
    entity_id: int | None,
) -> AuditLog | None:
    if not payload.interaction_id:
        return None
    entity_clause = AuditLog.entity_id.is_(None) if entity_id is None else AuditLog.entity_id == entity_id
    candidates = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.action == payload.action,
            AuditLog.entity_type == payload.entity_type,
            entity_clause,
            AuditLog.actor_type == context.actor.actor_type,
            AuditLog.actor_user_id == context.actor.user_id,
            AuditLog.actor_api_key_id == context.actor.api_key_id,
        )
        .order_by(AuditLog.id.desc())
        .limit(20)
    ).all()
    return next((item for item in candidates if (item.after_json or {}).get("interaction_id") == payload.interaction_id), None)


def audit_sensitive_access(
    db: Session,
    payload: SensitiveAccessEventIn,
    context: CurrentUserContext,
    request: Request | None,
    *,
    internal: bool = False,
) -> AuditLog:
    definition = ACCESS_EVENT_DEFINITIONS[payload.action]
    if payload.entity_type not in definition.entity_types:
        raise HTTPException(status_code=422, detail="Audit događaj ne odgovara vrsti objekta")
    if not internal and not definition.enabled_for_direct_endpoint:
        raise HTTPException(status_code=409, detail="Audit događaj se smije zapisati samo iz stvarnog radnog tijeka")
    _ensure_event_permission(context, definition)

    entity_id, clinic_id = _resolve_scoped_entity(db, payload, context)
    duplicate = _find_duplicate_interaction(db, payload, context, entity_id)
    if duplicate:
        return duplicate

    safe_payload = {
        "surface": payload.surface,
        "clinic_id": clinic_id,
        "interaction_id": payload.interaction_id,
    }
    audit(
        db,
        payload.action,
        payload.entity_type,
        entity_id,
        f"Sensitive access event: {payload.action}",
        context.actor.user_id,
        context.actor.actor_type,
        context.actor.api_key_id,
        None,
        safe_payload,
        request,
    )
    db.flush()
    return db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(1)).one()
