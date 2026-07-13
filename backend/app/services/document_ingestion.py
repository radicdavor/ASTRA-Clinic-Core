from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.domain import ClinicalDocument, DocumentProcessingJob, PatientJourney


ALLOWED_UPLOAD_CHANNELS = {
    "web_upload",
    "ai_secretary_email",
    "staff_upload",
    "reception_scan",
    "direct_scan",
    "external_integration",
}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/tiff", "text/plain"}


@dataclass(frozen=True)
class OCRResult:
    status: str
    text: str | None = None
    confidence: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class ClassificationResult:
    label: str
    confidence: float


@dataclass(frozen=True)
class EmailIngestionEnvelope:
    message_id: str
    sender: str
    attachment_names: tuple[str, ...]


@dataclass(frozen=True)
class EmailIngestionReview:
    status: str
    reason: str


def evaluate_email_ingestion(envelope: EmailIngestionEnvelope) -> EmailIngestionReview:
    """Mailbox-free boundary: no sender is auto-linked to a patient or journey."""
    if not envelope.attachment_names:
        return EmailIngestionReview(status="rejected", reason="Poruka nema privitak")
    return EmailIngestionReview(
        status="manual_review_required",
        reason="Pošiljatelj i tijek pacijenta moraju biti ljudski potvrđeni prije pohrane",
    )


class LocalDemoOCRProvider:
    """Deterministic test/demo boundary; it is not a PDF or image OCR engine."""

    name = "local-demo-text-only"

    def process(self, source_path: Path, mime_type: str) -> OCRResult:
        if mime_type != "text/plain":
            return OCRResult(status="failed", error="OCR provider nije konfiguriran za PDF ili sliku")
        try:
            return OCRResult(status="completed", text=source_path.read_text(encoding="utf-8"), confidence=1.0)
        except (OSError, UnicodeError) as exc:
            return OCRResult(status="failed", error=f"Tekst nije moguće pročitati: {exc}")


class LocalDemoClassificationProvider:
    """Metadata-only candidate classifier. The human-selected document type remains authoritative."""

    name = "local-demo-metadata-only"

    def process(self, document: ClinicalDocument) -> ClassificationResult:
        text = f"{document.title} {document.original_filename or ''}".lower()
        candidates = {
            "laboratory": ("laborator", "lab", "krv", "nalaz"),
            "gastroscopy": ("gastroskop", "egd"),
            "colonoscopy": ("kolonoskop",),
            "pathology": ("patolog", "biops"),
            "imaging": ("ultrazvuk", "ct", "mr", "rendgen"),
        }
        for label, keywords in candidates.items():
            if any(keyword in text for keyword in keywords):
                return ClassificationResult(label=label, confidence=0.75)
        return ClassificationResult(label="other", confidence=0.20)


def _storage_root() -> Path:
    root = Path(get_settings().document_storage_path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def source_path(document: ClinicalDocument) -> Path:
    if not document.attachment_path:
        raise HTTPException(404, detail="Izvorna datoteka nije pohranjena")
    root = _storage_root()
    path = (root / document.attachment_path).resolve()
    if root not in path.parents:
        raise HTTPException(409, detail="Neispravna putanja izvornog dokumenta")
    if not path.is_file():
        raise HTTPException(404, detail="Izvorna datoteka nije pronađena")
    if document.checksum_sha256 and sha256(path.read_bytes()).hexdigest() != document.checksum_sha256:
        raise HTTPException(409, detail="Kontrolni zbroj izvornog dokumenta nije valjan")
    return path


def ingest_source_document(
    db: Session,
    journey: PatientJourney,
    content: bytes,
    filename: str,
    mime_type: str,
    upload_channel: str,
    title: str,
    document_type: str,
    document_date,
    actor_user_id: int | None,
) -> ClinicalDocument:
    settings = get_settings()
    if upload_channel not in ALLOWED_UPLOAD_CHANNELS:
        raise HTTPException(422, detail="Nepoznat kanal zaprimanja dokumenta")
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, detail="Dopušteni su PDF, JPEG, PNG, TIFF i tekst")
    if not content:
        raise HTTPException(422, detail="Datoteka je prazna")
    if len(content) > settings.document_max_upload_bytes:
        raise HTTPException(413, detail="Datoteka je veća od dopuštene veličine")

    digest = sha256(content).hexdigest()
    suffix = Path(filename).suffix.lower()[:12]
    relative_path = Path(str(journey.id)) / f"{uuid4().hex}{suffix}"
    path = _storage_root() / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

    now = datetime.now(timezone.utc)
    document = ClinicalDocument(
        patient_id=journey.patient_id,
        appointment_id=journey.appointment_id,
        journey_id=journey.id,
        clinical_episode_id=journey.appointment.episode_id,
        source_type="uploaded" if upload_channel != "reception_scan" else "scanned",
        document_type=document_type,
        document_date=document_date,
        title=title,
        attachment_path=relative_path.as_posix(),
        upload_channel=upload_channel,
        original_filename=Path(filename).name,
        mime_type=mime_type,
        checksum_sha256=digest,
        file_size_bytes=len(content),
        lifecycle_status="stored",
        provenance_json={"channel": upload_channel, "actor_user_id": actor_user_id},
        received_at=now,
        review_status="draft",
        ai_extraction_status="not_run",
        physician_reviewed=False,
    )
    db.add(document)
    db.flush()
    return document


def queue_ocr(db: Session, document: ClinicalDocument) -> DocumentProcessingJob:
    if not document.attachment_path:
        raise HTTPException(409, detail="OCR zahtijeva pohranjeni izvorni dokument")
    if document.lifecycle_status not in {"stored", "ocr_failed"}:
        raise HTTPException(409, detail="Dokument nije spreman za OCR")
    document.lifecycle_status = "ocr_pending"
    job = DocumentProcessingJob(
        clinical_document_id=document.id,
        job_type="ocr",
        provider=LocalDemoOCRProvider.name,
        status="pending",
    )
    db.add(job)
    db.flush()
    return job


def process_ocr_job(db: Session, job: DocumentProcessingJob) -> DocumentProcessingJob:
    if job.job_type != "ocr" or job.status not in {"pending", "failed"}:
        raise HTTPException(409, detail="OCR posao nije spreman za obradu")
    document = job.document
    job.status = "running"
    job.attempts += 1
    job.started_at = datetime.now(timezone.utc)
    result = LocalDemoOCRProvider().process(source_path(document), document.mime_type or "")
    job.completed_at = datetime.now(timezone.utc)
    if result.status == "completed":
        job.status = "completed"
        job.result_metadata_json = {"confidence": result.confidence}
        document.ocr_text = result.text
        document.raw_text = document.raw_text or result.text
        document.extraction_confidence = result.confidence
        document.lifecycle_status = "ocr_completed"
    else:
        job.status = "failed"
        job.error_message = result.error
        document.lifecycle_status = "ocr_failed"
    db.flush()
    return job


def queue_classification(db: Session, document: ClinicalDocument) -> DocumentProcessingJob:
    if document.lifecycle_status not in {"stored", "ocr_completed", "ocr_failed"}:
        raise HTTPException(409, detail="Dokument nije spreman za klasifikaciju")
    document.lifecycle_status = "classification_pending"
    job = DocumentProcessingJob(
        clinical_document_id=document.id,
        job_type="classification",
        provider=LocalDemoClassificationProvider.name,
        status="pending",
    )
    db.add(job)
    db.flush()
    return job


def process_classification_job(db: Session, job: DocumentProcessingJob) -> DocumentProcessingJob:
    if job.job_type != "classification" or job.status not in {"pending", "failed"}:
        raise HTTPException(409, detail="Klasifikacijski posao nije spreman za obradu")
    job.status = "running"
    job.attempts += 1
    job.started_at = datetime.now(timezone.utc)
    result = LocalDemoClassificationProvider().process(job.document)
    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)
    job.result_metadata_json = {"candidate_label": result.label, "confidence": result.confidence}
    provenance = dict(job.document.provenance_json or {})
    provenance["classification_candidate"] = {
        "label": result.label,
        "confidence": result.confidence,
        "provider": LocalDemoClassificationProvider.name,
        "review_required": True,
    }
    job.document.provenance_json = provenance
    job.document.classification_confidence = result.confidence
    job.document.lifecycle_status = "classified"
    job.document.review_status = "needs_physician_review"
    db.flush()
    return job
