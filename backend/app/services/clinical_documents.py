from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.models.domain import Appointment, ClinicalDocument, Patient, PatientClinicAssociation


class DocumentClassificationConflict(RuntimeError):
    pass


def confirm_document_classification(
    db: Session,
    document: ClinicalDocument,
    *,
    record_classification: str,
    reviewer_user_id: int,
    note: str | None,
    reviewed_at: datetime | None = None,
) -> ClinicalDocument:
    """Atomically transition one unclassified source exactly once."""
    now = reviewed_at or datetime.now(timezone.utc)
    provenance = dict(document.provenance_json or {})
    provenance["classification_review"] = {
        "record_classification": record_classification,
        "note": note,
        "reviewed_by": reviewer_user_id,
        "reviewed_at": now.isoformat(),
    }
    transition = db.execute(
        update(ClinicalDocument)
        .where(
            ClinicalDocument.id == document.id,
            ClinicalDocument.record_classification == "unclassified",
        )
        .values(
            record_classification=record_classification,
            is_clinical_record=record_classification == "clinical",
            classification_reviewed_by=reviewer_user_id,
            classification_reviewed_at=now,
            provenance_json=provenance,
        )
        .execution_options(synchronize_session=False)
    )
    if transition.rowcount != 1:
        raise DocumentClassificationConflict
    db.refresh(document)
    return document


def get_document_or_404(db: Session, document_id: int) -> ClinicalDocument:
    document = db.scalar(
        select(ClinicalDocument)
        .options(joinedload(ClinicalDocument.patient))
        .where(ClinicalDocument.id == document_id)
    )
    if not document:
        raise HTTPException(404, detail="Klinicki dokument nije pronaden")
    return document


def validate_document_provenance_links(
    db: Session,
    *,
    patient_id: int,
    clinic_id: int,
    appointment_id: int | None,
) -> Appointment | None:
    """Validate document ownership without disclosing a global patient match."""
    patient = db.scalar(
        select(Patient)
        .join(PatientClinicAssociation, PatientClinicAssociation.patient_id == Patient.id)
        .where(
            Patient.id == patient_id,
            PatientClinicAssociation.clinic_id == clinic_id,
            PatientClinicAssociation.active.is_(True),
        )
    )
    if patient is None:
        raise HTTPException(404, detail="Pacijent nije pronađen")
    if appointment_id is None:
        return None
    appointment = db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient_id,
            Appointment.clinic_id == clinic_id,
        )
    )
    if appointment is None:
        raise HTTPException(404, detail="Termin nije pronaden")
    return appointment


def extract_document_knowledge(document: ClinicalDocument) -> dict:
    text = (document.raw_text or "").lower()
    findings: list[str] = []
    recommendations: list[str] = []
    summary = "AI prijedlog: dokument nema dovoljno teksta za strukturirani sazetak. Manual review recommended."

    if "gerb" in text or "refluks" in text:
        findings.append("GERB/refluks naveden u dokumentu")
    if "adenom" in text or "polip" in text:
        findings.append("Prethodni polip/adenom naveden u dokumentu")
    if "h. pylori" in text or "helicobacter" in text:
        findings.append("H. pylori status naveden u dokumentu")
    if "gastroskop" in text:
        findings.append("Gastroskopija dokumentirana")
    if "kolonoskop" in text:
        findings.append("Kolonoskopija dokumentirana")
    if "patolog" in text or "biops" in text or "ph nalaz" in text:
        findings.append("Patologija/biopsija spomenuta u dokumentu")
    if "esomeprazol" in text or "pantoprazol" in text:
        findings.append("Terapija inhibitorom protonske pumpe spomenuta u dokumentu")
    if "kontrol" in text or "ponov" in text or "preporuc" in text or "preporuč" in text:
        recommendations.append("Dokument sadrzi preporuku ili kontrolu koju treba lijecnik pregledati")
    if "patologija pending" in text or "ceka se" in text or "pending" in text:
        recommendations.append("Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled")

    if findings or recommendations:
        summary = "AI prijedlog: strukturirani elementi su izdvojeni iz teksta dokumenta i cekaju lijecnicki pregled."
    return {"ai_summary": summary, "key_findings": findings, "recommendations": recommendations}


def has_extracted_content(document: ClinicalDocument) -> bool:
    return bool(document.ai_summary or document.key_findings or document.recommendations)


def initial_document_review_status(values: dict) -> str:
    if values.get("ai_summary") or values.get("key_findings") or values.get("recommendations"):
        return "needs_physician_review"
    return "draft"


def initial_ai_extraction_status(values: dict) -> str:
    if values.get("ai_summary") or values.get("key_findings") or values.get("recommendations"):
        return "edited"
    return "not_run"


def mark_document_needs_review(document: ClinicalDocument) -> None:
    document.review_status = "needs_physician_review" if has_extracted_content(document) or document.raw_text else "draft"
    document.physician_reviewed = False
    document.reviewed_by = None
    document.reviewed_at = None


def mark_document_ai_extraction_edited(document: ClinicalDocument, now: datetime) -> None:
    document.ai_extraction_status = "edited" if has_extracted_content(document) else "not_run"
    document.ai_extraction_updated_at = now if has_extracted_content(document) else None
