from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, active_clinic_memberships
from app.models.domain import (
    AuditLog,
    ClinicalDocument,
    ClinicalDocumentAddendum,
    Clinic,
    Institution,
    PatientClinicAssociation,
)
from app.services.clinical_documents import get_document_or_404


MEDICAL_STAFF_CATEGORY = "medical_staff"
CLINICAL_READ_PERMISSION = "clinical.documents.read_institution"
CLINICAL_EDIT_PERMISSION = "clinical.documents.edit_own_draft"
CLINICAL_ADDENDUM_PERMISSION = "clinical.documents.add_addendum"
SIGNED_OR_FINAL_DOCUMENT_STATUSES = {"signed", "reviewed"}
INSTITUTION_READABLE_RECORD_CLASSIFICATIONS = {"clinical"}
EDITABLE_CLINICAL_DOCUMENT_STATUSES = {"draft", "needs_physician_review", "reviewed"}


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


def actor_institution_ids(db: Session, actor: Actor) -> set[int]:
    if not actor.user:
        return set()
    return {
        membership.clinic.institution_id
        for membership in active_clinic_memberships(db, actor.user.id)
        if membership.clinic.institution_id is not None
    }


def actor_institution_context(db: Session, actor: Actor) -> tuple[set[int], set[str]]:
    return actor_institution_ids(db, actor), actor_institution_keys(db, actor)


def clinic_institution_id(db: Session, clinic_id: int | None) -> int | None:
    if clinic_id is None:
        return None
    clinic = db.get(Clinic, clinic_id)
    return clinic.institution_id if clinic else None


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


def document_institution_ids(db: Session, document: ClinicalDocument) -> set[int]:
    if document.clinic and document.clinic.institution_id is not None:
        return {document.clinic.institution_id}
    if document.clinic_id:
        clinic = db.get(Clinic, document.clinic_id)
        if clinic and clinic.institution_id is not None:
            return {clinic.institution_id}
    rows = db.scalars(
        select(Clinic.institution_id)
        .join(PatientClinicAssociation, PatientClinicAssociation.clinic_id == Clinic.id)
        .where(
            PatientClinicAssociation.patient_id == document.patient_id,
            PatientClinicAssociation.active.is_(True),
            Clinic.active.is_(True),
            Clinic.institution_id.is_not(None),
        )
    ).all()
    return {item for item in rows if item is not None}


def ensure_institution_clinical_read(db: Session, document: ClinicalDocument, actor: Actor) -> int | str:
    if not document.is_clinical_record:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Dokument nije dio kliničkog kartona")
    if document.record_classification not in INSTITUTION_READABLE_RECORD_CLASSIFICATIONS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Izvorni dokument nije klasificiran kao klinički")
    if not actor_is_medical_staff(actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Klinički dokument smije čitati samo ovlašteno medicinsko osoblje")
    actor_ids, actor_keys = actor_institution_context(db, actor)
    document_ids = document_institution_ids(db, document)
    id_overlap = actor_ids.intersection(document_ids)
    if id_overlap:
        return sorted(id_overlap)[0]
    document_keys = document_institution_keys(db, document)
    key_overlap = actor_keys.intersection(document_keys)
    if key_overlap:
        return sorted(key_overlap)[0]
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Klinicki dokument nije pronaden")


def resolve_actor_institution_context(db: Session, actor: Actor, requested_institution_id: int | None = None) -> int | None:
    if not actor_is_medical_staff(actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Klinički karton smije čitati samo ovlašteno medicinsko osoblje")
    institution_ids = actor_institution_ids(db, actor)
    if requested_institution_id is not None:
        institution = db.get(Institution, requested_institution_id)
        if requested_institution_id not in institution_ids or not institution or not institution.active:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Klinički karton nije pronađen")
        return requested_institution_id
    if len(institution_ids) == 1:
        return next(iter(institution_ids))
    if len(institution_ids) > 1:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Potreban je odabir ustanove")
    if actor_institution_keys(db, actor):
        return None
    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Korisnik nema aktivno članstvo ni u jednoj ustanovi")


def get_institution_scoped_clinical_document_for_read(
    db: Session,
    document_id: int,
    actor: Actor,
    request: Request | None = None,
    action: str = "clinical_document_viewed",
) -> ClinicalDocument:
    document = get_document_or_404(db, document_id)
    institution = ensure_institution_clinical_read(db, document, actor)
    existing_read_audit = db.scalar(
        select(AuditLog.id)
        .where(
            AuditLog.action == action,
            AuditLog.entity_type == "ClinicalDocument",
            AuditLog.entity_id == document.id,
            AuditLog.actor_user_id == actor.user_id,
            AuditLog.actor_api_key_id == actor.api_key_id,
        )
        .limit(1)
    )
    if existing_read_audit:
        return document
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
            "institution_id": institution if isinstance(institution, int) else None,
            "institution_key": institution if isinstance(institution, str) else None,
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
    institution_ids, institution_keys = actor_institution_context(db, actor)
    if not institution_ids and not institution_keys:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Korisnik nema aktivno članstvo ni u jednoj ustanovi")
    institution_filter = []
    if institution_ids:
        institution_filter.append(Clinic.institution_id.in_(institution_ids))
    if institution_keys:
        institution_filter.append(Clinic.institution_key.in_(institution_keys))
    return (
        select(ClinicalDocument)
        .options(joinedload(ClinicalDocument.patient), joinedload(ClinicalDocument.clinic))
        .outerjoin(Clinic, ClinicalDocument.clinic_id == Clinic.id)
        .where(
            ClinicalDocument.is_clinical_record.is_(True),
            ClinicalDocument.record_classification.in_(INSTITUTION_READABLE_RECORD_CLASSIFICATIONS),
            or_(*institution_filter, ClinicalDocument.clinic_id.is_(None)),
        )
    )


def get_authored_draft_for_edit(db: Session, document_id: int, actor: Actor) -> ClinicalDocument:
    document = get_document_or_404(db, document_id)
    ensure_institution_clinical_read(db, document, actor)
    can_edit_clinical_draft(actor, document)
    return document


def can_edit_clinical_draft(actor: Actor, document: ClinicalDocument) -> bool:
    if CLINICAL_EDIT_PERMISSION not in actor.permissions:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Nedostaje dozvola: {CLINICAL_EDIT_PERMISSION}")
    if document.review_status == "signed":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"code": "signed_document_immutable", "message": "Potpisani dokument je nepromjenjiv; koristite dopunu/addendum"},
        )
    if document.review_status not in EDITABLE_CLINICAL_DOCUMENT_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Samo nacrt kliničkog dokumenta može se standardno uređivati")
    if document.review_status == "draft" and document.author_user_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Legacy nacrt bez pouzdanog autora je samo za čitanje")
    if document.author_user_id is not None and document.author_user_id != actor.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Nacrt smije uređivati samo autor dokumenta")
    return True


def create_document_addendum(
    db: Session,
    document_id: int,
    reason: str,
    content: str,
    actor: Actor,
    request: Request | None = None,
) -> ClinicalDocumentAddendum:
    document = get_document_or_404(db, document_id)
    institution = ensure_institution_clinical_read(db, document, actor)
    if CLINICAL_ADDENDUM_PERMISSION not in actor.permissions:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Nedostaje dozvola: {CLINICAL_ADDENDUM_PERMISSION}")
    if document.review_status not in SIGNED_OR_FINAL_DOCUMENT_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Dopuna se dodaje samo na potpisani ili završni dokument")
    if actor.user_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Dopuna zahtijeva prijavljenog korisnika")
    addendum = ClinicalDocumentAddendum(
        original_document_id=document.id,
        original_document_type="clinical_document",
        patient_id=document.patient_id,
        institution_id=institution if isinstance(institution, int) else clinic_institution_id(db, document.clinic_id),
        clinic_id=document.clinic_id,
        author_user_id=actor.user_id,
        reason=reason,
        content=content,
        status="signed",
        signed_at=datetime.now(timezone.utc),
        signed_by_user_id=actor.user_id,
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
