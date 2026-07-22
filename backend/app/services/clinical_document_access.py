from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, load_only

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, active_clinic_memberships
from app.models.domain import (
    AuditLog,
    ClinicalDocument,
    ClinicalDocumentAddendum,
    Clinic,
    Institution,
    SignedClinicalReport,
)
from app.services.clinical_documents import get_document_or_404
from app.services.reports import verify_report_integrity


MEDICAL_STAFF_CATEGORY = "medical_staff"
CLINICAL_READ_PERMISSION = "clinical.documents.read_institution"
CLINICAL_EDIT_PERMISSION = "clinical.documents.edit_own_draft"
CLINICAL_ADDENDUM_PERMISSION = "clinical.documents.add_addendum"
CLINICAL_REVIEW_PERMISSION = "clinical_documents.review"
SIGNED_OR_FINAL_DOCUMENT_STATUSES = {"signed", "reviewed"}
INSTITUTION_READABLE_RECORD_CLASSIFICATIONS = {"clinical"}
EDITABLE_CLINICAL_DOCUMENT_STATUSES = {"draft", "needs_physician_review", "reviewed"}


@dataclass(frozen=True)
class ClinicalDocumentCapabilities:
    can_edit: bool
    can_review: bool
    can_add_addendum: bool


@dataclass(frozen=True)
class ActorInstitutionScope:
    clinic_ids: tuple[int, ...]
    institution_ids: frozenset[int]
    institution_keys: frozenset[str]


def clinical_document_capabilities(actor: Actor, document: ClinicalDocument) -> ClinicalDocumentCapabilities:
    """Return UI capabilities from the same author, permission and status rules used by writes.

    The caller must still use a scoped loader before exposing the document. These
    flags are presentation hints; write endpoints remain authoritative.
    """
    return ClinicalDocumentCapabilities(
        can_edit=bool(
            actor.user_id
            and CLINICAL_EDIT_PERMISSION in actor.permissions
            and document.author_user_id == actor.user_id
            and document.review_status in EDITABLE_CLINICAL_DOCUMENT_STATUSES
        ),
        can_review=bool(
            CLINICAL_REVIEW_PERMISSION in actor.permissions
            and document.review_status != "signed"
        ),
        can_add_addendum=bool(
            CLINICAL_ADDENDUM_PERMISSION in actor.permissions
            and document.review_status in SIGNED_OR_FINAL_DOCUMENT_STATUSES
        ),
    )


def actor_is_medical_staff(actor: Actor) -> bool:
    return bool(
        actor.user
        and actor.user.role
        and actor.user.role.professional_category == MEDICAL_STAFF_CATEGORY
        and CLINICAL_READ_PERMISSION in actor.permissions
    )


def actor_institution_keys(db: Session, actor: Actor) -> set[str]:
    return set(actor_institution_scope(db, actor).institution_keys)


def actor_institution_ids(db: Session, actor: Actor) -> set[int]:
    return set(actor_institution_scope(db, actor).institution_ids)


def actor_institution_scope(db: Session, actor: Actor) -> ActorInstitutionScope:
    if not actor.user:
        return ActorInstitutionScope((), frozenset(), frozenset())
    memberships = active_clinic_memberships(db, actor.user.id)
    return ActorInstitutionScope(
        clinic_ids=tuple(membership.clinic_id for membership in memberships),
        institution_ids=frozenset(
            membership.clinic.institution_id
            for membership in memberships
            if membership.clinic.institution_id is not None
        ),
        institution_keys=frozenset(membership.clinic.institution_key for membership in memberships),
    )


def actor_institution_context(db: Session, actor: Actor) -> tuple[set[int], set[str]]:
    scope = actor_institution_scope(db, actor)
    return set(scope.institution_ids), set(scope.institution_keys)


def clinic_institution_id(db: Session, clinic_id: int | None) -> int | None:
    if clinic_id is None:
        return None
    clinic = db.get(Clinic, clinic_id)
    return clinic.institution_id if clinic else None


def institution_id_for_clinic(db: Session, clinic_id: int | None) -> int | None:
    clinic = db.get(Clinic, clinic_id) if clinic_id is not None else None
    return clinic.institution_id if clinic else None


def require_document_institution_for_clinic(db: Session, clinic_id: int | None) -> int:
    institution_id = institution_id_for_clinic(db, clinic_id)
    if institution_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Nije moguće dokazati ustanovu kliničkog dokumenta")
    return institution_id


def validate_document_provenance(db: Session, document: ClinicalDocument) -> None:
    if document.institution_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Klinički dokument nema razriješeno podrijetlo ustanove")
    clinic_institution_id = institution_id_for_clinic(db, document.clinic_id)
    if clinic_institution_id is not None and clinic_institution_id != document.institution_id:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Klinika i ustanova kliničkog dokumenta nisu usklađene")


def ensure_institution_clinical_read(
    db: Session,
    document: ClinicalDocument,
    actor: Actor,
    actor_scope: ActorInstitutionScope | None = None,
) -> int | str:
    if not document.is_clinical_record:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Dokument nije dio kliničkog kartona")
    if document.record_classification not in INSTITUTION_READABLE_RECORD_CLASSIFICATIONS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Izvorni dokument nije klasificiran kao klinički")
    if not actor_is_medical_staff(actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Klinički dokument smije čitati samo ovlašteno medicinsko osoblje")
    scope = actor_scope or actor_institution_scope(db, actor)
    if document.institution_id is not None and document.institution_id in scope.institution_ids:
        return document.institution_id
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Klinicki dokument nije pronaden")


def resolve_actor_institution_context(db: Session, actor: Actor, requested_institution_id: int | None = None) -> int | None:
    if not actor_is_medical_staff(actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Klinički karton smije čitati samo ovlašteno medicinsko osoblje")
    scope = actor_institution_scope(db, actor)
    institution_ids = scope.institution_ids
    if requested_institution_id is not None:
        institution = db.get(Institution, requested_institution_id)
        if requested_institution_id not in institution_ids or not institution or not institution.active:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Klinički karton nije pronađen")
        return requested_institution_id
    if len(institution_ids) == 1:
        return next(iter(institution_ids))
    if len(institution_ids) > 1:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Potreban je odabir ustanove")
    if scope.institution_keys:
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
    actor_scope = actor_institution_scope(db, actor)
    institution = ensure_institution_clinical_read(db, document, actor, actor_scope)
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
            "actor_clinic_ids": list(actor_scope.clinic_ids),
            "document_clinic_id": document.clinic_id,
            "patient_id": document.patient_id,
        },
        request,
    )
    return document


def institution_scoped_clinical_documents_statement(db: Session, actor: Actor):
    return (
        institution_provenance_scoped_documents_statement(db, actor)
        .options(joinedload(ClinicalDocument.patient), joinedload(ClinicalDocument.clinic))
        .where(
            ClinicalDocument.is_clinical_record.is_(True),
            ClinicalDocument.record_classification.in_(INSTITUTION_READABLE_RECORD_CLASSIFICATIONS),
        )
    )


def institution_provenance_scoped_documents_statement(db: Session, actor: Actor):
    """Scope every document lifecycle state by canonical institution provenance."""
    if not actor_is_medical_staff(actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Kliničke dokumente smije čitati samo ovlašteno medicinsko osoblje")
    scope = actor_institution_scope(db, actor)
    institution_ids = scope.institution_ids
    if not institution_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Korisnik nema aktivno članstvo ni u jednoj ustanovi")
    return select(ClinicalDocument).where(ClinicalDocument.institution_id.in_(institution_ids))


def institution_scoped_clinical_record_metadata_statement(
    db: Session,
    actor: Actor,
    resolved_institution_id: int | None,
):
    """Return only columns required by the paginated clinical-record directory."""
    if not actor_is_medical_staff(actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Klinicke dokumente smije citati samo ovlasteno medicinsko osoblje")
    if resolved_institution_id is not None:
        scope_filter = ClinicalDocument.institution_id == resolved_institution_id
    else:
        scope = actor_institution_scope(db, actor)
        if not scope.institution_ids:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Korisnik nema aktivno clanstvo ni u jednoj ustanovi")
        scope_filter = ClinicalDocument.institution_id.in_(scope.institution_ids)
    return (
        select(ClinicalDocument)
        .options(
            load_only(
                ClinicalDocument.id,
                ClinicalDocument.patient_id,
                ClinicalDocument.document_date,
                ClinicalDocument.created_at,
                ClinicalDocument.clinic_id,
                ClinicalDocument.institution_id,
                ClinicalDocument.document_type,
                ClinicalDocument.title,
                ClinicalDocument.author,
                ClinicalDocument.author_professional_role,
                ClinicalDocument.review_status,
                ClinicalDocument.reviewed_at,
                ClinicalDocument.author_user_id,
            ),
            joinedload(ClinicalDocument.clinic).load_only(Clinic.id, Clinic.name),
        )
        .where(
            ClinicalDocument.is_clinical_record.is_(True),
            ClinicalDocument.record_classification.in_(INSTITUTION_READABLE_RECORD_CLASSIFICATIONS),
            scope_filter,
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
    signed_report_id: int | None = None,
) -> ClinicalDocumentAddendum:
    document = get_document_or_404(db, document_id)
    institution = ensure_institution_clinical_read(db, document, actor)
    if CLINICAL_ADDENDUM_PERMISSION not in actor.permissions:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Nedostaje dozvola: {CLINICAL_ADDENDUM_PERMISSION}")
    if document.review_status not in SIGNED_OR_FINAL_DOCUMENT_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Dopuna se dodaje samo na potpisani ili završni dokument")
    if actor.user_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Dopuna zahtijeva prijavljenog korisnika")
    report = db.get(SignedClinicalReport, signed_report_id) if signed_report_id is not None else db.scalar(
        select(SignedClinicalReport).where(SignedClinicalReport.clinical_document_id == document.id)
    )
    if report is not None:
        if report.clinical_document_id != document.id:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Potpisani nalaz ne pripada izvornom dokumentu")
        verify_report_integrity(report)
        signed_report_id = report.id
    addendum = ClinicalDocumentAddendum(
        original_document_id=document.id,
        signed_report_id=signed_report_id,
        original_document_type="signed_clinical_report" if signed_report_id is not None else "clinical_document",
        patient_id=document.patient_id,
        institution_id=institution,
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
