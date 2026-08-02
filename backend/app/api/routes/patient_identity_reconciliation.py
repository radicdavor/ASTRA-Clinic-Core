from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit
from app.auth.dependencies import Actor, CurrentUserContext, require_active_clinic, require_permission
from app.core.database import get_db
from app.models.domain import Patient, PatientIdentityReconciliationRequest
from app.schemas.common import ErrorResponse, PatientIdentityReconciliationDecision, PatientIdentityReconciliationReviewItem, PatientIdentityReconciliationStatusOut
from app.services.patient_identity_reconciliation import approve_link, confirm_distinct, finalize_without_patient, lock_pending

router = APIRouter(prefix="/api/patient-identity-reconciliations", tags=["patient-identity-reconciliation"], responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})


def require_reconciliation_reviewer(actor: Actor = Depends(require_permission("patients.identity_reconciliation.review"))) -> Actor:
    if actor.actor_type != "user" or actor.user is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Pregled identiteta zahtijeva izričito ovlaštenog korisnika")
    return actor


def requester_out(item: PatientIdentityReconciliationRequest) -> PatientIdentityReconciliationStatusOut:
    return PatientIdentityReconciliationStatusOut(
        request_id=item.id, status=item.status, submitted_identity=item.submitted_identity_snapshot,
        result_patient_id=item.result_patient_id if item.status in {"approved_link", "confirmed_distinct"} else None,
        created_at=item.created_at, updated_at=item.updated_at,
    )


def _mask(value: str | None, visible: int = 2) -> str | None:
    if not value:
        return None
    return "*" * max(0, len(value) - visible) + value[-visible:]


def _review_identity(snapshot: dict) -> dict:
    return {
        "schema_version": snapshot.get("schema_version"),
        "first_name": snapshot.get("first_name"),
        "last_name": snapshot.get("last_name"),
        "date_of_birth": snapshot.get("date_of_birth"),
        "oib_masked": _mask(snapshot.get("oib"), 3),
        "email_masked": _mask(snapshot.get("email"), 5),
        "phone_masked": _mask(snapshot.get("phone"), 4),
    }


def review_out(db: Session, item: PatientIdentityReconciliationRequest) -> PatientIdentityReconciliationReviewItem:
    candidates = []
    for patient_id in item.candidate_patient_ids:
        patient = db.get(Patient, int(patient_id))
        if patient:
            candidates.append({"patient_id": patient.id, "first_name": patient.first_name, "last_name": patient.last_name, "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None, "oib_masked": _mask(patient.oib, 3), "email_masked": _mask(patient.email, 5), "phone_masked": _mask(patient.phone, 4)})
    return PatientIdentityReconciliationReviewItem(
        request_id=item.id, status=item.status, requesting_clinic_id=item.requesting_clinic_id,
        requesting_institution_id=item.requesting_institution_id, submitted_identity=_review_identity(item.submitted_identity_snapshot),
        candidates=candidates, match_reasons=item.match_reasons, created_at=item.created_at, updated_at=item.updated_at,
    )


def requester_item(db: Session, request_id: str, clinic_id: int) -> PatientIdentityReconciliationRequest:
    item = db.scalar(select(PatientIdentityReconciliationRequest).where(PatientIdentityReconciliationRequest.id == request_id, PatientIdentityReconciliationRequest.requesting_clinic_id == clinic_id))
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Zahtjev nije pronađen")
    return item


@router.get("/{request_id}", response_model=PatientIdentityReconciliationStatusOut)
def get_request_status(request_id: str, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("patients.write"))):
    item = requester_item(db, request_id, context.active_clinic_id)
    audit(db, "patient_identity.status_viewed", "PatientIdentityReconciliationRequest", None, "Otvoren status zahtjeva za pregled identiteta", context.actor.user_id, context.actor.actor_type, context.actor.api_key_id, None, {"request_id": item.id, "status": item.status}, request)
    db.commit()
    return requester_out(item)


@router.post("/{request_id}/cancel", response_model=PatientIdentityReconciliationStatusOut)
def cancel_request(request_id: str, payload: PatientIdentityReconciliationDecision, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("patients.write"))):
    requester_item(db, request_id, context.active_clinic_id)
    return requester_out(finalize_without_patient(db, lock_pending(db, request_id), context.actor, request, "cancelled", payload.reason))


@router.get("/review/pending", response_model=list[PatientIdentityReconciliationReviewItem])
def pending_review_queue(request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_reconciliation_reviewer)):
    items = db.scalars(select(PatientIdentityReconciliationRequest).where(PatientIdentityReconciliationRequest.status == "pending_review").order_by(PatientIdentityReconciliationRequest.created_at, PatientIdentityReconciliationRequest.id)).all()
    audit(db, "patient_identity.queue_viewed", "PatientIdentityReconciliationRequest", None, "Otvoren red za kontrolirani pregled identiteta", actor.user_id, actor.actor_type, actor.api_key_id, None, {"pending_count": len(items)}, request, scope_type="system")
    db.commit()
    return [review_out(db, item) for item in items]


@router.get("/review/{request_id}", response_model=PatientIdentityReconciliationReviewItem)
def review_detail(request_id: str, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_reconciliation_reviewer)):
    item = db.get(PatientIdentityReconciliationRequest, request_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Zahtjev nije pronađen")
    audit(db, "patient_identity.review_viewed", "PatientIdentityReconciliationRequest", None, "Otvoren minimalni identity comparison", actor.user_id, actor.actor_type, actor.api_key_id, None, {"request_id": item.id, "status": item.status}, request, scope_type="clinic", clinic_id=item.requesting_clinic_id, institution_id=item.requesting_institution_id)
    db.commit()
    return review_out(db, item)


@router.post("/review/{request_id}/approve-link", response_model=PatientIdentityReconciliationStatusOut)
def approve(request_id: str, payload: PatientIdentityReconciliationDecision, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_reconciliation_reviewer)):
    return requester_out(approve_link(db, lock_pending(db, request_id), actor, request, payload.reason, payload.candidate_patient_id))


@router.post("/review/{request_id}/confirm-distinct", response_model=PatientIdentityReconciliationStatusOut)
def distinct(request_id: str, payload: PatientIdentityReconciliationDecision, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_reconciliation_reviewer)):
    return requester_out(confirm_distinct(db, lock_pending(db, request_id), actor, request, payload.reason))


@router.post("/review/{request_id}/reject", response_model=PatientIdentityReconciliationStatusOut)
def reject(request_id: str, payload: PatientIdentityReconciliationDecision, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_reconciliation_reviewer)):
    return requester_out(finalize_without_patient(db, lock_pending(db, request_id), actor, request, "rejected_insufficient_evidence", payload.reason))
