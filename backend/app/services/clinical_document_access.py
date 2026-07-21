from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, active_clinic_memberships
from app.models.domain import (
    ClinicalDocument,
    ClinicalDocumentAddendum,
    Clinic,
    PatientClinicAssociation,
)
from app.services.clinical_documents import get_document_or_404


MEDICAL_STAFF_CATEGORY = "medical_staff"
CLINICAL_READ_PERMISSION = "clinical.documents.read_institution"
CLINICAL_EDIT_PERMISSION = "clinical.documents.edit_own_draft"
CLINICAL_ADDENDUM_PERMISSION = "clinical.documents.add_addendum"
SIGNED_OR_FINAL_DOCUMENT_STATUSES = {"signed", "reviewed"}


def actor_is_medical_staff(actor: Actor) -> bool:
    return bool(
        actor.user
        and actor.user.role
        and actor.user.role.professional_category == MEDICAL_STAFF_CATEGORY
        and CLINICAL_READ_PERMISSION in actor.permissions
    )


def actor_institution_keys(db: Session, actor: Actor) -> set[str]:
    if not actor.user:
        return set()
    return {membership.clinic.institution_key for membership in active_clinic_memberships(db, actor.user.id)}


def document_institution_keys(db: Session, document: ClinicalDocument) -> set[str]:
    if document.clinic:
        return {document.clinic.institution_key}
    if document.clinic_id:
        clinic = db.get(Clinic, document.clinic_id)
        return {clinic.institution_key} if clinic else set()
    rows = db.scalars(
        select(Clinic.institution_key)
        .join(PatientClinicAssociation, PatientClinicAssociation.clinic_id == Clinic.id)
        .where(
            PatientClinicAssociation.patient_id == document.patient_id,
            PatientClinicAssociation.active.is_(True),
            Clinic.active.is_(True),
        )
    ).all()
    return set(rows) or {"default"}


def ensure_institution_clinical_read(
    db: Session,
    document: ClinicalDocument,
    actor: Actor,
) -> str:
    if not document.is_clinical_record:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Dokument nije dio kliničkog kartona")
    if not actor_is_medical_staff(actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Klinički dokument smije čitati samo ovlašteno medicinsko osoblje")
    actor_institutions = actor_institution_keys(db, actor)
    document_institutions = document_institution_keys(db, document)
    overlap = actor_institutions.intersection(document_institutions)
    if not overlap:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Klinicki dokument nije pronaden")
    return sorted(overlap)[0]


def get_institution_scoped_clinical_document_for_read(
    db: Session,
    document_id: int,
    actor: Actor,
    request: Request | None = None,
    action: str = "clinical_document_viewed",
) -> ClinicalDocument:
    document = get_document_or_404(db, document_id)
    institution_key = ensure_institution_clinical_read(db, document, actor)
    audit(
        db,
        action,
        "ClinicalDocument",
        document.id,
        "Otvoren je klinički dokument unutar ustanove",
        actor.user_id,
        actor.actor_type,
        actor.api_key_id,
        None,
        {
            "institution_key": institution_key,
            "actor_clinic_ids": [membership.clinic_id for membership in active_clinic_memberships(db, actor.user_id)] if actor.user_id else [],
            "document_clinic_id": document.clinic_id,
            "patient_id": document.patient_id,
        },
        request,
    )
    return document


def institution_scoped_clinical_documents_statement(db: Session, actor: Actor):
    if not actor_is_medical_staff(actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Kliničke dokumente smije čitati samo ovlašteno medicinsko osoblje")
    institutions = actor_institution_keys(db, actor)
    if not institutions:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Korisnik nema aktivno članstvo ni u jednoj ustanovi")
    return (
        select(ClinicalDocument)
        .options(joinedload(ClinicalDocument.patient), joinedload(ClinicalDocument.clinic))
        .outerjoin(Clinic, ClinicalDocument.clinic_id == Clinic.id)
        .where(
            ClinicalDocument.is_clinical_record.is_(True),
            or_(Clinic.institution_key.in_(institutions), ClinicalDocument.clinic_id.is_(None)),
        )
    )


def get_authored_draft_for_edit(db: Session, document_id: int, actor: Actor) -> ClinicalDocument:
    document = get_document_or_404(db, document_id)
    ensure_institution_clinical_read(db, document, actor)
    if CLINICAL_EDIT_PERMISSION not in actor.permissions:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Nedostaje dozvola: {CLINICAL_EDIT_PERMISSION}")
    if document.review_status == "signed":
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Potpisani dokument je nepromjenjiv; koristite dopunu/addendum")
    if document.review_status not in {"draft", "needs_physician_review", "reviewed"}:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Samo nepotpisani dokument može se standardno uređivati")
    if document.author_user_id is not None and document.author_user_id != actor.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Nacrt smije uređivati samo autor dokumenta")
    return document


def create_document_addendum(
    db: Session,
    document_id: int,
    reason: str,
    content: str,
    actor: Actor,
    request: Request | None = None,
) -> ClinicalDocumentAddendum:
    document = get_document_or_404(db, document_id)
    ensure_institution_clinical_read(db, document, actor)
    if CLINICAL_ADDENDUM_PERMISSION not in actor.permissions:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Nedostaje dozvola: {CLINICAL_ADDENDUM_PERMISSION}")
    if document.review_status not in SIGNED_OR_FINAL_DOCUMENT_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Dopuna se dodaje samo na potpisani ili završni dokument")
    if actor.user_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Dopuna zahtijeva prijavljenog korisnika")
    addendum = ClinicalDocumentAddendum(
        original_document_id=document.id,
        author_user_id=actor.user_id,
        reason=reason,
        content=content,
        status="signed",
        signed_at=datetime.now(timezone.utc),
    )
    db.add(addendum)
    db.flush()
    audit(
        db,
        "clinical_document_addendum_created",
        "ClinicalDocumentAddendum",
        addendum.id,
        "Dodana je klinička dopuna bez izmjene originalnog dokumenta",
        actor.user_id,
        actor.actor_type,
        actor.api_key_id,
        None,
        snapshot(addendum),
        request,
    )
    return addendum
