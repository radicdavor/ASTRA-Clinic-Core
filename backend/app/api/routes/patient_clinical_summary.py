from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import ClinicalDocument, Patient, PatientClinicalSummaryRecord
from app.schemas.common import ErrorResponse, PatientClinicalSummary, PatientClinicalSummaryRecordOut, PatientClinicalSummaryRecordUpdate
from app.services.patient_knowledge import GENERIC_OPEN_QUESTION_TEXT, add_knowledge_item, contains_unresolved_language, is_document_awaiting_physician_review, is_official_clinical_document, latest_patient_summary_record, latest_reviewed_document_updated_at, official_patient_documents_statement, summary_record_from_documents, summary_record_is_stale

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api", tags=["patient-clinical-summary"], responses=ERROR_RESPONSES)


def patch_model(obj, data: dict) -> None:
    for key, value in data.items():
        setattr(obj, key, value)


@router.get("/patients/{patient_id}/clinical-summary", response_model=PatientClinicalSummary)
def patient_clinical_summary(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_documents.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    documents = db.scalars(select(ClinicalDocument).where(ClinicalDocument.patient_id == patient_id).order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())).all()
    reviewed = [document for document in documents if is_official_clinical_document(document)]
    awaiting_review_count = len([document for document in documents if is_document_awaiting_physician_review(document)])
    reviewed_summary = latest_patient_summary_record(db, patient_id, ["reviewed"])
    draft_summary = latest_patient_summary_record(db, patient_id, ["draft_ai", "needs_review", "stale"])
    latest_document_updated_at = latest_reviewed_document_updated_at(reviewed)
    reviewed_summary_is_stale = summary_record_is_stale(reviewed_summary, latest_document_updated_at)
    draft_summary_is_stale = summary_record_is_stale(draft_summary, latest_document_updated_at)
    summary_warning = None
    if reviewed_summary_is_stale:
        summary_warning = "Pregledani sazetak je zastario jer postoje noviji pregledani dokumenti."
    elif draft_summary_is_stale:
        summary_warning = "AI draft sazetka je zastario jer postoje noviji pregledani dokumenti."
    summary = PatientClinicalSummary(
        patient_id=patient_id,
        generated_from_reviewed_documents=len(reviewed),
        awaiting_review_count=awaiting_review_count,
        reviewed_summary=reviewed_summary,
        draft_summary=draft_summary,
        reviewed_summary_is_stale=reviewed_summary_is_stale,
        draft_summary_is_stale=draft_summary_is_stale,
        latest_reviewed_document_updated_at=latest_document_updated_at,
        reviewed_summary_updated_at=reviewed_summary.updated_at if reviewed_summary else None,
        summary_warning=summary_warning,
        known_problems=[],
        completed_procedures=[],
        pathology=[],
        laboratory=[],
        imaging=[],
        current_therapy=[],
        open_questions=[],
        latest_recommendations=[],
    )
    for document in reviewed:
        source_text_blob = " ".join([document.raw_text or "", document.ai_summary or "", " ".join(document.key_findings or [])]).lower()
        for finding in document.key_findings or []:
            lower = finding.lower()
            if document.document_type in {"gastroscopy", "colonoscopy"} or "gastroskop" in lower or "kolonoskop" in lower:
                add_knowledge_item(summary.completed_procedures, finding, document)
            elif document.document_type == "pathology" or "patolog" in lower or "biops" in lower:
                add_knowledge_item(summary.pathology, finding, document)
            elif document.document_type == "laboratory":
                add_knowledge_item(summary.laboratory, finding, document)
            elif document.document_type == "radiology":
                add_knowledge_item(summary.imaging, finding, document)
            elif "terap" in lower or "esomeprazol" in lower or "pantoprazol" in lower:
                add_knowledge_item(summary.current_therapy, finding, document)
            else:
                add_knowledge_item(summary.known_problems, finding, document)
        for recommendation in document.recommendations or []:
            if contains_unresolved_language(recommendation):
                add_knowledge_item(summary.open_questions, recommendation, document, display_kind="open_question", severity="warning", requires_attention=True)
            else:
                add_knowledge_item(summary.latest_recommendations, recommendation, document)
        if document.document_type in {"pathology", "laboratory", "radiology"} and not document.key_findings:
            target = summary.pathology if document.document_type == "pathology" else summary.laboratory if document.document_type == "laboratory" else summary.imaging
            add_knowledge_item(target, document.ai_summary or document.title, document)
        if contains_unresolved_language(source_text_blob):
            add_knowledge_item(summary.open_questions, GENERIC_OPEN_QUESTION_TEXT, document, display_kind="open_question", severity="warning", requires_attention=True)
    return summary


@router.post("/patients/{patient_id}/clinical-summary/generate-draft", response_model=PatientClinicalSummaryRecordOut)
def generate_patient_clinical_summary_draft(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    reviewed = db.scalars(official_patient_documents_statement(patient_id).order_by(ClinicalDocument.document_date.desc().nulls_last(), ClinicalDocument.id.desc())).all()
    values = summary_record_from_documents(patient_id, reviewed)
    record = PatientClinicalSummaryRecord(**values)
    db.add(record)
    db.flush()
    audit(db, "patient_summary_draft_generated", "PatientClinicalSummary", record.id, "AI placeholder je generirao draft sazetka pacijenta", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(record), request)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/patients/{patient_id}/clinical-summary", response_model=PatientClinicalSummaryRecordOut)
def update_patient_clinical_summary_record(
    patient_id: int,
    payload: PatientClinicalSummaryRecordUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.write")),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    record = latest_patient_summary_record(db, patient_id, ["draft_ai", "needs_review", "stale", "reviewed"])
    if record is None:
        record = PatientClinicalSummaryRecord(patient_id=patient_id, status="needs_review", generated_by="physician")
        db.add(record)
        db.flush()
    before = snapshot(record)
    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("status") == "reviewed":
        update_data["status"] = "needs_review"
    patch_model(record, update_data)
    edited_fields = {"summary_text", "known_conditions", "key_findings", "open_items", "risks", "last_recommendations", "source_document_ids"}
    if edited_fields.intersection(update_data):
        record.status = "needs_review"
    if record.status == "reviewed":
        record.status = "needs_review"
        record.reviewed_by = None
        record.reviewed_at = None
    db.flush()
    audit(db, "patient_summary_edited", "PatientClinicalSummary", record.id, "Uredjen klinicki sazetak pacijenta prije potvrde", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(record), request)
    db.commit()
    db.refresh(record)
    return record


@router.post("/patients/{patient_id}/clinical-summary/review", response_model=PatientClinicalSummaryRecordOut)
def review_patient_clinical_summary_record(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("clinical_documents.review")),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    record = latest_patient_summary_record(db, patient_id, ["draft_ai", "needs_review", "stale"])
    if record is None:
        raise HTTPException(404, detail="Nema draft sazetka za potvrdu")
    reviewed_documents = db.scalars(official_patient_documents_statement(patient_id)).all()
    latest_document_updated_at = latest_reviewed_document_updated_at(reviewed_documents)
    if summary_record_is_stale(record, latest_document_updated_at):
        raise HTTPException(409, detail="Sazetak je zastario jer postoje noviji pregledani dokumenti. Generirajte novi draft prije potvrde.")
    before = snapshot(record)
    record.status = "reviewed"
    record.reviewed_by = actor.user_id
    record.reviewed_at = datetime.now(timezone.utc)
    db.flush()
    audit(db, "patient_summary_reviewed", "PatientClinicalSummary", record.id, "Lijecnik je potvrdio klinicki sazetak pacijenta", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(record), request)
    db.commit()
    db.refresh(record)
    return record
