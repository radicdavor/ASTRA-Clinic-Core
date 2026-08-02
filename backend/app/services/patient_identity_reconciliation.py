from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import audit
from app.models.domain import Patient, PatientClinicAssociation, PatientIdentityReconciliationRequest
from app.schemas.common import PatientCreate


FINAL_STATUSES = frozenset({"approved_link", "confirmed_distinct", "rejected_insufficient_evidence", "cancelled"})


def _text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.strip().casefold().split())
    return normalized or None


def _phone(value: str | None) -> str | None:
    if not value:
        return None
    prefix = "+" if value.strip().startswith("+") else ""
    digits = re.sub(r"\D", "", value)
    return f"{prefix}{digits}" if digits else None


def identity_snapshot(payload: PatientCreate) -> dict:
    return {
        "schema_version": 1,
        "first_name": payload.first_name.strip(),
        "last_name": payload.last_name.strip(),
        "date_of_birth": payload.date_of_birth.isoformat() if payload.date_of_birth else None,
        "oib": payload.oib,
        "email": str(payload.email).strip().casefold() if payload.email else None,
        "phone": payload.phone.strip() if payload.phone else None,
    }


def normalized_identity(snapshot: dict) -> dict:
    return {
        "first_name": _text(snapshot.get("first_name")),
        "last_name": _text(snapshot.get("last_name")),
        "date_of_birth": snapshot.get("date_of_birth"),
        "oib": snapshot.get("oib") if snapshot.get("oib") and len(snapshot["oib"]) == 11 and snapshot["oib"].isdigit() else None,
        "email": _text(snapshot.get("email")),
        "phone": _phone(snapshot.get("phone")),
    }


def identity_fingerprint(snapshot: dict) -> str:
    encoded = json.dumps(normalized_identity(snapshot), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def candidate_reasons(patient: Patient, submitted: dict) -> list[str]:
    candidate = normalized_identity({
        "first_name": patient.first_name, "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        "oib": patient.oib, "email": patient.email, "phone": patient.phone,
    })
    reasons: list[str] = []
    if submitted["oib"] and candidate["oib"] == submitted["oib"]:
        reasons.append("oib")
    if submitted["date_of_birth"] and candidate["date_of_birth"] == submitted["date_of_birth"]:
        if submitted["first_name"] and submitted["last_name"] and candidate["first_name"] == submitted["first_name"] and candidate["last_name"] == submitted["last_name"]:
            reasons.append("name_date_of_birth")
        if submitted["email"] and candidate["email"] == submitted["email"]:
            reasons.append("date_of_birth_email")
        if submitted["phone"] and candidate["phone"] == submitted["phone"]:
            reasons.append("date_of_birth_phone")
    return reasons


def find_candidates(db: Session, snapshot: dict) -> tuple[list[Patient], dict[str, list[str]]]:
    submitted = normalized_identity(snapshot)
    candidates: list[Patient] = []
    reasons: dict[str, list[str]] = {}
    for patient in db.scalars(select(Patient).order_by(Patient.id)).all():
        matched = candidate_reasons(patient, submitted)
        if matched:
            candidates.append(patient)
            reasons[str(patient.id)] = matched
    return candidates, reasons


def _audit(db: Session, request_obj: PatientIdentityReconciliationRequest, action: str, actor, request: Request, before: str | None, after: str, reason: str | None = None) -> None:
    audit(
        db, action, "PatientIdentityReconciliationRequest", None,
        "Kontrolirani pregled identiteta pacijenta", actor.user_id, actor.actor_type, actor.api_key_id,
        {"request_id": request_obj.id, "status": before} if before else None,
        {"request_id": request_obj.id, "status": after, "reason_recorded": bool(reason)}, request,
        scope_type="clinic", clinic_id=request_obj.requesting_clinic_id,
        institution_id=request_obj.requesting_institution_id,
    )


def create_patient_or_reconciliation(db: Session, payload: PatientCreate, clinic_id: int, institution_id: int, actor, request: Request) -> Patient | PatientIdentityReconciliationRequest:
    snapshot = identity_snapshot(payload)
    candidates, reasons = find_candidates(db, snapshot)
    clinic_patient_ids = set(db.scalars(select(PatientClinicAssociation.patient_id).where(PatientClinicAssociation.clinic_id == clinic_id, PatientClinicAssociation.active.is_(True))).all())
    if any(patient.id in clinic_patient_ids for patient in candidates):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Pacijent s tim identitetom već postoji u aktivnoj klinici")
    if candidates:
        fingerprint = identity_fingerprint(snapshot)
        existing = db.scalar(select(PatientIdentityReconciliationRequest).where(
            PatientIdentityReconciliationRequest.requesting_clinic_id == clinic_id,
            PatientIdentityReconciliationRequest.submitted_identity_fingerprint == fingerprint,
            PatientIdentityReconciliationRequest.status == "pending_review",
        ))
        if existing:
            return existing
        item = PatientIdentityReconciliationRequest(
            id=str(uuid4()), requesting_institution_id=institution_id, requesting_clinic_id=clinic_id,
            requested_by_user_id=actor.user_id, requested_by_api_key_id=actor.api_key_id,
            submitted_identity_snapshot=snapshot, submitted_identity_fingerprint=fingerprint,
            candidate_patient_ids=[patient.id for patient in candidates], match_reasons=reasons,
        )
        db.add(item)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(select(PatientIdentityReconciliationRequest).where(
                PatientIdentityReconciliationRequest.requesting_clinic_id == clinic_id,
                PatientIdentityReconciliationRequest.submitted_identity_fingerprint == fingerprint,
                PatientIdentityReconciliationRequest.status == "pending_review",
            ))
            if existing is None:
                raise
            return existing
        _audit(db, item, "patient_identity.requested", actor, request, None, "pending_review")
        db.commit()
        db.refresh(item)
        return item
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic_id, active=True, created_by_user_id=actor.user_id))
    audit(db, "create", "Patient", patient.id, "Kreiran pacijent", actor.user_id, actor.actor_type, actor.api_key_id, None, {"patient_id": patient.id, "clinic_id": clinic_id}, request)
    db.commit()
    db.refresh(patient)
    return patient


def lock_pending(db: Session, request_id: str) -> PatientIdentityReconciliationRequest:
    item = db.scalar(select(PatientIdentityReconciliationRequest).where(PatientIdentityReconciliationRequest.id == request_id).with_for_update())
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Zahtjev nije pronađen")
    if item.status != "pending_review":
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Zahtjev više nije otvoren za odluku")
    return item


def approve_link(db: Session, item: PatientIdentityReconciliationRequest, actor, request: Request, reason: str, candidate_patient_id: int | None) -> PatientIdentityReconciliationRequest:
    candidate_ids = [int(value) for value in item.candidate_patient_ids]
    selected_id = candidate_patient_id if candidate_patient_id is not None else (candidate_ids[0] if len(candidate_ids) == 1 else None)
    if selected_id is None or selected_id not in candidate_ids:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Povezivanje zahtijeva valjan odabir kandidata iz zahtjeva")
    patient = db.get(Patient, selected_id)
    if patient is None or not candidate_reasons(patient, normalized_identity(item.submitted_identity_snapshot)):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Kandidat više nije valjan")
    association = db.scalar(select(PatientClinicAssociation).where(PatientClinicAssociation.patient_id == patient.id, PatientClinicAssociation.clinic_id == item.requesting_clinic_id))
    if association is None:
        association = PatientClinicAssociation(patient_id=patient.id, clinic_id=item.requesting_clinic_id, active=True, created_by_user_id=actor.user_id)
        db.add(association)
    else:
        association.active = True
    item.status = "approved_link"; item.result_patient_id = patient.id; item.reviewed_at = datetime.now(timezone.utc); item.reviewed_by_user_id = actor.user_id; item.decision_reason = reason; item.version += 1
    _audit(db, item, "patient_identity.link_approved", actor, request, "pending_review", item.status, reason)
    audit(db, "patient_clinic_association_create", "PatientClinicAssociation", None, "Odobreno povezivanje pacijenta s klinikom", actor.user_id, actor.actor_type, actor.api_key_id, None, {"patient_id": patient.id, "clinic_id": item.requesting_clinic_id, "reconciliation_request_id": item.id}, request, scope_type="clinic", clinic_id=item.requesting_clinic_id, institution_id=item.requesting_institution_id)
    db.commit(); db.refresh(item)
    return item


def confirm_distinct(db: Session, item: PatientIdentityReconciliationRequest, actor, request: Request, reason: str) -> PatientIdentityReconciliationRequest:
    current, _ = find_candidates(db, item.submitted_identity_snapshot)
    original = {int(value) for value in item.candidate_patient_ids}
    if {patient.id for patient in current} - original:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Identitet se promijenio i zahtijeva novi pregled")
    # OIB is globally unique in the existing Patient contract. A reviewer may
    # confirm a distinct person only for weaker collisions; duplicating an OIB
    # would otherwise escape as a database IntegrityError.
    if item.submitted_identity_snapshot.get("oib") and any(
        "oib" in reasons for reasons in item.match_reasons.values()
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="OIB zahtijeva povezivanje s postojećim pacijentom")
    payload = PatientCreate.model_validate(item.submitted_identity_snapshot)
    patient = Patient(**payload.model_dump())
    db.add(patient); db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=item.requesting_clinic_id, active=True, created_by_user_id=actor.user_id))
    item.status = "confirmed_distinct"; item.result_patient_id = patient.id; item.reviewed_at = datetime.now(timezone.utc); item.reviewed_by_user_id = actor.user_id; item.decision_reason = reason; item.version += 1
    _audit(db, item, "patient_identity.distinct_confirmed", actor, request, "pending_review", item.status, reason)
    audit(db, "create", "Patient", patient.id, "Novi pacijent nakon kontrolirane odluke o različitom identitetu", actor.user_id, actor.actor_type, actor.api_key_id, None, {"patient_id": patient.id, "clinic_id": item.requesting_clinic_id, "reconciliation_request_id": item.id}, request, scope_type="clinic", clinic_id=item.requesting_clinic_id, institution_id=item.requesting_institution_id)
    db.commit(); db.refresh(item)
    return item


def finalize_without_patient(db: Session, item: PatientIdentityReconciliationRequest, actor, request: Request, status_value: str, reason: str) -> PatientIdentityReconciliationRequest:
    item.status = status_value; item.reviewed_at = datetime.now(timezone.utc); item.reviewed_by_user_id = actor.user_id; item.decision_reason = reason; item.version += 1
    action = "patient_identity.rejected" if status_value == "rejected_insufficient_evidence" else "patient_identity.cancelled"
    _audit(db, item, action, actor, request, "pending_review", status_value, reason)
    db.commit(); db.refresh(item)
    return item
