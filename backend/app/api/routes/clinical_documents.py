from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, active_clinic_memberships, get_current_actor, require_permission
from app.core.database import get_db
from app.models.domain import AuditLog, ClinicalDocument, ClinicalDocumentAddendum, Patient
from app.schemas.common import ClinicalDocumentAddendumCreate, ClinicalDocumentAddendumOut, ClinicalDocumentCreate, ClinicalDocumentOut, ClinicalDocumentUpdate, ClinicalDocumentUpload, ClinicalEvidenceTimelineItem, ErrorResponse
from app.services.clinical_document_access import actor_institution_scope, clinical_document_capabilities, create_document_addendum, ensure_institution_clinical_read, get_authored_draft_for_edit, get_institution_scoped_clinical_document_for_read, institution_scoped_clinical_documents_statement, require_document_institution_for_clinic, validate_document_provenance
from app.services.clinical_documents import extract_document_knowledge, get_document_or_404, has_extracted_content, initial_ai_extraction_status, initial_document_review_status, mark_document_ai_extraction_edited, mark_document_needs_review, validate_document_links
from app.services.clinical_evidence_timeline import classify_audit_log

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api", tags=["clinical-documents"], responses=ERROR_RESPONSES)


def patch_model(obj, data: dict) -> None:
    for key, value in data.items():
        setattr(obj, key, value)


def default_document_clinic_id(db: Session, payload_clinic_id: int | None, appointment_id: int | None, actor: Actor) -> int | None:
    from app.models.domain import Appointment, Clinic

    if actor.user is None:
        raise HTTPException(403, detail="Upis kliničkog dokumenta zahtijeva prijavljenog korisnika")
    appointment = db.get(Appointment, appointment_id) if appointment_id is not None else None
    if appointment_id is not None and appointment is None:
        raise HTTPException(404, detail="Termin nije pronađen")
    if payload_clinic_id is not None and appointment and appointment.clinic_id != payload_clinic_id:
        raise HTTPException(422, detail="Dokument i termin moraju pripadati istoj klinici")
    resolved_clinic_id = payload_clinic_id if payload_clinic_id is not None else (appointment.clinic_id if appointment else None)
    if resolved_clinic_id is not None:
        clinic = db.get(Clinic, resolved_clinic_id)
        if not clinic or not clinic.active:
            raise HTTPException(404, detail="Klinika nije pronađena")
        if clinic.institution_id is None or clinic.institution_id not in actor_institution_scope(db, actor).institution_ids:
            raise HTTPException(404, detail="Klinika nije pronađena")
        return resolved_clinic_id
    memberships = active_clinic_memberships(db, actor.user_id)
    return memberships[0].clinic_id if memberships else None


@router.get("/clinical-documents", response_model=list[ClinicalDocumentOut])
def list_clinical_documents(
    patient_id: int | None = None,
    document_type: str | None = None,
    source_type: str | None = None,
    physician_reviewed: bool | None = None,
    review_status: str | None = None,
    q: str | None = None,
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    stmt = institution_scoped_clinical_documents_statement(db, actor).order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())
    if patient_id:
        stmt = stmt.where(ClinicalDocument.patient_id == patient_id)
    if document_type:
        stmt = stmt.where(ClinicalDocument.document_type == document_type)
    if source_type:
        stmt = stmt.where(ClinicalDocument.source_type == source_type)
    if physician_reviewed is not None:
        stmt = stmt.where(ClinicalDocument.physician_reviewed.is_(physician_reviewed))
    if review_status:
        stmt = stmt.where(ClinicalDocument.review_status == review_status)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(ClinicalDocument.title.ilike(like), ClinicalDocument.origin.ilike(like), ClinicalDocument.institution.ilike(like), ClinicalDocument.raw_text.ilike(like), ClinicalDocument.ai_summary.ilike(like)))
    return db.scalars(stmt.limit(limit)).all()


@router.post("/clinical-documents", response_model=ClinicalDocumentOut)
def create_clinical_document(
    payload: ClinicalDocumentCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    values = payload.model_dump()
    values["clinic_id"] = default_document_clinic_id(db, values.get("clinic_id"), values.get("appointment_id"), actor)
    validate_document_links(db, payload.patient_id, payload.appointment_id)
    values["institution_id"] = require_document_institution_for_clinic(db, values["clinic_id"])
    now = datetime.now(timezone.utc)
    initial_ai_status = initial_ai_extraction_status(values)
    document = ClinicalDocument(
        **values,
        review_status=initial_document_review_status(values),
        ai_extraction_status=initial_ai_status,
        ai_extraction_generated_at=now if initial_ai_status != "not_run" else None,
        ai_extraction_updated_at=now if initial_ai_status != "not_run" else None,
        physician_reviewed=False,
        author_user_id=actor.user_id,
        author_professional_role=actor.user.role.name if actor.user and actor.user.role else None,
        is_clinical_record=True,
    )
    db.add(document)
    db.flush()
    audit(db, "create", "ClinicalDocument", document.id, f"Dodan klinicki dokument: {document.title}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.post("/patients/{patient_id}/clinical-documents", response_model=ClinicalDocumentOut)
def create_patient_clinical_document(
    patient_id: int,
    payload: ClinicalDocumentCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    if payload.patient_id != patient_id:
        raise HTTPException(422, detail="Dokument mora pripadati pacijentu iz rute")
    return create_clinical_document(payload, request, db, actor)


@router.post("/clinical-documents/upload", response_model=ClinicalDocumentOut)
def upload_clinical_document(
    payload: ClinicalDocumentUpload,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    attachment_path = f"local-placeholder/{payload.attachment_name}" if payload.attachment_name else None
    clinic_id = default_document_clinic_id(db, payload.clinic_id, payload.appointment_id, actor)
    validate_document_links(db, payload.patient_id, payload.appointment_id)
    document = ClinicalDocument(
        patient_id=payload.patient_id,
        clinic_id=clinic_id,
        institution_id=require_document_institution_for_clinic(db, clinic_id),
        title=payload.title,
        source_type=payload.source_type,
        document_type=payload.document_type,
        origin=payload.origin,
        document_date=payload.document_date,
        author=payload.author,
        institution=payload.institution,
        raw_text=payload.raw_text,
        attachment_path=attachment_path,
        appointment_id=payload.appointment_id,
        review_status="draft",
        ai_extraction_status="not_run",
        physician_reviewed=False,
        author_user_id=actor.user_id,
        author_professional_role=actor.user.role.name if actor.user and actor.user.role else None,
        is_clinical_record=True,
        record_classification="unclassified",
    )
    db.add(document)
    db.flush()
    audit(db, "upload", "ClinicalDocument", document.id, f"Upload placeholder dokumenta: {document.title}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.get("/clinical-documents/search", response_model=list[ClinicalDocumentOut])
def search_clinical_documents(q: str, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    like = f"%{q}%"
    return db.scalars(
        institution_scoped_clinical_documents_statement(db, actor)
        .where(or_(ClinicalDocument.title.ilike(like), ClinicalDocument.origin.ilike(like), ClinicalDocument.institution.ilike(like), ClinicalDocument.raw_text.ilike(like), ClinicalDocument.ai_summary.ilike(like)))
        .order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())
        .limit(50)
    ).all()


@router.get("/clinical-documents/{document_id}", response_model=ClinicalDocumentOut)
def get_clinical_document(document_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    document = get_institution_scoped_clinical_document_for_read(db, document_id, actor, request)
    capabilities = clinical_document_capabilities(actor, document)
    response = ClinicalDocumentOut.model_validate(document).model_copy(
        update={
            "can_edit": capabilities.can_edit,
            "can_review": capabilities.can_review,
            "can_add_addendum": capabilities.can_add_addendum,
        }
    )
    db.commit()
    return response


@router.get("/clinical-documents/{document_id}/evidence-timeline", response_model=list[ClinicalEvidenceTimelineItem])
def clinical_document_evidence_timeline(document_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    document = get_document_or_404(db, document_id)
    ensure_institution_clinical_read(db, document, actor)
    logs = db.scalars(select(AuditLog).where(AuditLog.entity_type == "ClinicalDocument", AuditLog.entity_id == document_id).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())).all()
    items: list[ClinicalEvidenceTimelineItem] = []
    access_only_actions = {"clinical_document_viewed", "source_document_viewed", "signed_report_viewed", "source_document_printed"}
    for log in logs:
        if log.action in access_only_actions:
            continue
        classification = classify_audit_log(log)
        items.append(
            ClinicalEvidenceTimelineItem(
                id=log.id,
                action=log.action,
                object_type=log.entity_type,
                object_id=log.entity_id,
                message=log.summary,
                actor_type=log.actor_type,
                actor_user_id=log.actor_user_id,
                actor_api_key_id=log.actor_api_key_id,
                created_at=log.created_at,
                clinical_event_category=classification.clinical_event_category,
                clinical_event_label=classification.clinical_event_label,
                knowledge_impact=classification.knowledge_impact,
                is_clinical_evidence_event=classification.is_clinical_evidence_event,
            )
        )
    return items


@router.patch("/clinical-documents/{document_id}", response_model=ClinicalDocumentOut)
def update_clinical_document(
    document_id: int,
    payload: ClinicalDocumentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    document = get_authored_draft_for_edit(db, document_id, actor)
    update_data = payload.model_dump(exclude_unset=True)
    for field in ("patient_id", "clinic_id", "appointment_id"):
        if field in update_data and update_data[field] != getattr(document, field):
            raise HTTPException(409, detail="Podrijetlo kliničkog dokumenta je nepromjenjivo")
    if document.checksum_sha256 and "attachment_path" in update_data and update_data["attachment_path"] != document.attachment_path:
        raise HTTPException(409, detail="Putanja pohranjenog izvornog dokumenta je nepromjenjiva")
    validate_document_links(db, update_data.get("patient_id", document.patient_id), update_data.get("appointment_id", document.appointment_id))
    before = snapshot(document)
    patch_model(document, update_data)
    validate_document_provenance(db, document)
    review_reset_fields = {"raw_text", "ai_summary", "key_findings", "recommendations"}
    if review_reset_fields.intersection(update_data):
        now = datetime.now(timezone.utc)
        extraction_fields = {"ai_summary", "key_findings", "recommendations"}
        if extraction_fields.intersection(update_data) or "raw_text" in update_data:
            mark_document_ai_extraction_edited(document, now)
        mark_document_needs_review(document)
    db.flush()
    extraction_fields = {"ai_summary", "key_findings", "recommendations"}
    action = "ai_document_extraction_edited" if extraction_fields.intersection(update_data) else "update"
    summary = "Uredjen AI prijedlog prije lijecnicke potvrde" if action == "ai_document_extraction_edited" else f"Azuriran klinicki dokument: {document.title}"
    audit(db, action, "ClinicalDocument", document.id, summary, actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.post("/clinical-documents/{document_id}/addenda", response_model=ClinicalDocumentAddendumOut)
def add_clinical_document_addendum(
    document_id: int,
    payload: ClinicalDocumentAddendumCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    addendum = create_document_addendum(db, document_id, payload.reason, payload.content, actor, request)
    db.commit()
    db.refresh(addendum)
    return addendum


@router.get("/clinical-documents/{document_id}/addenda", response_model=list[ClinicalDocumentAddendumOut])
def list_clinical_document_addenda(
    document_id: int,
    request: Request,
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical.documents.read_institution")),
):
    get_institution_scoped_clinical_document_for_read(db, document_id, actor, request, "clinical_document_addenda_viewed")
    addenda = db.scalars(
        select(ClinicalDocumentAddendum)
        .where(ClinicalDocumentAddendum.original_document_id == document_id)
        .order_by(ClinicalDocumentAddendum.created_at.desc(), ClinicalDocumentAddendum.id.desc())
        .limit(limit)
    ).all()
    db.commit()
    return list(reversed(addenda))


@router.post("/clinical-documents/{document_id}/extract", response_model=ClinicalDocumentOut)
def extract_clinical_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.review")),
):
    document = get_institution_scoped_clinical_document_for_read(db, document_id, actor, request)
    before = snapshot(document)
    now = datetime.now(timezone.utc)
    patch_model(document, extract_document_knowledge(document))
    document.ai_extraction_status = "generated"
    document.ai_extraction_generated_at = now
    document.ai_extraction_updated_at = now
    document.review_status = "needs_physician_review"
    document.physician_reviewed = False
    document.reviewed_by = None
    document.reviewed_at = None
    db.flush()
    audit(db, "ai_document_extracted", "ClinicalDocument", document.id, "AI placeholder je predlozio strukturirani sazetak dokumenta", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.post("/clinical-documents/{document_id}/review", response_model=ClinicalDocumentOut)
def review_clinical_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    document = get_institution_scoped_clinical_document_for_read(db, document_id, actor, request)
    before = snapshot(document)
    now = datetime.now(timezone.utc)
    document.review_status = "reviewed"
    if has_extracted_content(document):
        document.ai_extraction_status = "accepted"
        document.ai_extraction_updated_at = now
    document.physician_reviewed = True
    document.reviewed_by = actor.user_id
    document.reviewed_at = now
    db.flush()
    audit(db, "clinical_document_reviewed", "ClinicalDocument", document.id, "Lijecnik je pregledao klinicki dokument", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.post("/clinical-documents/{document_id}/reject-summary", response_model=ClinicalDocumentOut)
def reject_clinical_document_summary(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    document = get_institution_scoped_clinical_document_for_read(db, document_id, actor, request)
    before = snapshot(document)
    document.ai_summary = None
    document.key_findings = []
    document.recommendations = []
    document.ai_extraction_status = "rejected"
    document.ai_extraction_updated_at = datetime.now(timezone.utc)
    document.review_status = "draft"
    if document.author_user_id is None:
        document.author_user_id = actor.user_id
    document.physician_reviewed = False
    document.reviewed_by = None
    document.reviewed_at = None
    db.flush()
    audit(db, "ai_document_summary_rejected", "ClinicalDocument", document.id, "Lijecnik je odbio AI sazetak dokumenta", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return get_document_or_404(db, document.id)


@router.get("/patients/{patient_id}/clinical-documents", response_model=list[ClinicalDocumentOut])
def patient_clinical_documents(
    patient_id: int,
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    return db.scalars(
        institution_scoped_clinical_documents_statement(db, actor)
        .where(ClinicalDocument.patient_id == patient_id)
        .order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())
        .limit(limit)
    ).all()
