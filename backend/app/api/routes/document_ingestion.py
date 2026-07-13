from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import DocumentProcessingJob, DocumentRequest, PatientJourney
from app.schemas.document_ingestion import DocumentIngestionOut, DocumentJobOut
from app.services.document_ingestion import (
    ingest_source_document,
    process_classification_job,
    process_ocr_job,
    queue_classification,
    queue_ocr,
    source_path,
)
from app.services.patient_journeys import add_event


router = APIRouter(prefix="/api", tags=["document-ingestion"])


def get_journey(db: Session, journey_id: int) -> PatientJourney:
    journey = db.scalar(
        select(PatientJourney)
        .options(joinedload(PatientJourney.appointment))
        .where(PatientJourney.id == journey_id)
    )
    if not journey:
        raise HTTPException(404, detail="Tijek pacijenta nije pronađen")
    return journey


def get_job(db: Session, document_id: int, job_id: int) -> DocumentProcessingJob:
    job = db.scalar(
        select(DocumentProcessingJob)
        .options(joinedload(DocumentProcessingJob.document))
        .where(
            DocumentProcessingJob.id == job_id,
            DocumentProcessingJob.clinical_document_id == document_id,
        )
    )
    if not job:
        raise HTTPException(404, detail="Posao obrade dokumenta nije pronađen")
    return job


@router.post("/patient-journeys/{journey_id}/documents/ingest", response_model=DocumentIngestionOut)
async def ingest_document(
    journey_id: int,
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form("other"),
    upload_channel: str = Form("staff_upload"),
    document_date: date | None = Form(None),
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("documents.upload")),
):
    journey = get_journey(db, journey_id)
    if upload_channel in {"reception_scan", "direct_scan"} and "documents.scan" not in actor.permissions:
        raise HTTPException(403, detail="Nedostaje dozvola: documents.scan")
    content = await file.read()
    document = ingest_source_document(
        db,
        journey,
        content,
        file.filename or "document",
        file.content_type or "application/octet-stream",
        upload_channel,
        title,
        document_type,
        document_date,
        actor.user_id,
    )
    requested = db.scalar(
        select(DocumentRequest).where(
            DocumentRequest.journey_id == journey.id,
            DocumentRequest.document_type == document_type,
            DocumentRequest.status == "requested",
        ).order_by(DocumentRequest.id)
    )
    if requested:
        requested.status = "received"
        requested.clinical_document_id = document.id
    journey.document_status = "partial"
    add_event(
        db,
        journey,
        "document_received",
        f"Zaprimljen izvorni dokument: {document.title}",
        actor,
        request,
        journey.current_stage,
        journey.current_stage,
        {"document_id": document.id, "upload_channel": upload_channel, "checksum": document.checksum_sha256},
    )
    audit(db, "document_received", "ClinicalDocument", document.id, f"Izvorni dokument pohranjen: {document.title}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(document), request)
    db.commit()
    db.refresh(document)
    return document


@router.get("/clinical-documents/{document_id}/source")
def open_document_source(
    document_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("documents.view_source")),
):
    from app.models.domain import ClinicalDocument

    document = db.get(ClinicalDocument, document_id)
    if not document:
        raise HTTPException(404, detail="Klinički dokument nije pronađen")
    path = source_path(document)
    return FileResponse(path, media_type=document.mime_type, filename=document.original_filename or path.name)


@router.post("/clinical-documents/{document_id}/ocr", response_model=DocumentJobOut)
def create_ocr_job(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("documents.review")),
):
    from app.models.domain import ClinicalDocument

    document = db.get(ClinicalDocument, document_id)
    if not document:
        raise HTTPException(404, detail="Klinički dokument nije pronađen")
    job = queue_ocr(db, document)
    audit(db, "ocr_queued", "ClinicalDocument", document.id, "Dokument stavljen u OCR red", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(job), request)
    db.commit()
    db.refresh(job)
    return job


@router.post("/clinical-documents/{document_id}/ocr/{job_id}/process", response_model=DocumentJobOut)
def run_ocr_job(
    document_id: int,
    job_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("documents.review")),
):
    job = get_job(db, document_id, job_id)
    before = snapshot(job)
    job = process_ocr_job(db, job)
    audit(db, "ocr_completed" if job.status == "completed" else "ocr_failed", "ClinicalDocument", document_id, f"OCR obrada: {job.status}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(job), request)
    db.commit()
    db.refresh(job)
    return job


@router.get("/clinical-documents/{document_id}/processing-jobs", response_model=list[DocumentJobOut])
def list_processing_jobs(
    document_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("documents.view_source")),
):
    return db.scalars(
        select(DocumentProcessingJob)
        .where(DocumentProcessingJob.clinical_document_id == document_id)
        .order_by(DocumentProcessingJob.id.desc())
    ).all()


@router.post("/clinical-documents/{document_id}/classification", response_model=DocumentJobOut)
def create_classification_job(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("documents.review")),
):
    from app.models.domain import ClinicalDocument

    document = db.get(ClinicalDocument, document_id)
    if not document:
        raise HTTPException(404, detail="Klinički dokument nije pronađen")
    job = queue_classification(db, document)
    audit(db, "classification_queued", "ClinicalDocument", document.id, "Dokument stavljen u red za klasifikaciju", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(job), request)
    db.commit()
    db.refresh(job)
    return job


@router.post("/clinical-documents/{document_id}/classification/{job_id}/process", response_model=DocumentJobOut)
def run_classification_job(
    document_id: int,
    job_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("documents.review")),
):
    job = get_job(db, document_id, job_id)
    before = snapshot(job)
    job = process_classification_job(db, job)
    audit(db, "document_classified", "ClinicalDocument", document_id, "Stvoren kandidat klasifikacije; čeka ljudski pregled", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(job), request)
    db.commit()
    db.refresh(job)
    return job
