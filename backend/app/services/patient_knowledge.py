from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import ClinicalDocument, PatientClinicalSummaryRecord
from app.schemas.common import PatientKnowledgeItem, PatientKnowledgeSource


DOCUMENT_REVIEW_AWAITING_STATUSES = {"extracted", "needs_physician_review"}


def source_for_document(document: ClinicalDocument) -> PatientKnowledgeSource:
    return PatientKnowledgeSource(
        document_id=document.id,
        title=document.title,
        document_type=document.document_type,
        source_type=document.source_type,
        origin=document.origin,
        document_date=document.document_date,
    )


def knowledge_item(text: str, document: ClinicalDocument) -> PatientKnowledgeItem:
    return PatientKnowledgeItem(text=text, sources=[source_for_document(document)])


def add_knowledge_item(items: list[PatientKnowledgeItem], text: str | None, document: ClinicalDocument) -> None:
    cleaned = (text or "").strip()
    if not cleaned:
        return
    source = source_for_document(document)
    if not source.document_id:
        return
    normalized = " ".join(cleaned.lower().split())
    for item in items:
        if " ".join(item.text.lower().split()) == normalized:
            if all(existing.document_id != source.document_id for existing in item.sources):
                item.sources.append(source)
            return
    items.append(PatientKnowledgeItem(text=cleaned, sources=[source]))


def is_official_clinical_document(document: ClinicalDocument) -> bool:
    return document.physician_reviewed is True and document.review_status == "reviewed"


def is_document_awaiting_physician_review(document: ClinicalDocument) -> bool:
    return document.review_status in DOCUMENT_REVIEW_AWAITING_STATUSES


def latest_patient_summary_record(db: Session, patient_id: int, statuses: list[str] | None = None) -> PatientClinicalSummaryRecord | None:
    stmt = select(PatientClinicalSummaryRecord).where(PatientClinicalSummaryRecord.patient_id == patient_id)
    if statuses:
        stmt = stmt.where(PatientClinicalSummaryRecord.status.in_(statuses))
    return db.scalar(stmt.order_by(PatientClinicalSummaryRecord.updated_at.desc(), PatientClinicalSummaryRecord.id.desc()))


def official_patient_documents_statement(patient_id: int | None = None):
    stmt = select(ClinicalDocument).where(ClinicalDocument.physician_reviewed.is_(True), ClinicalDocument.review_status == "reviewed")
    if patient_id is not None:
        stmt = stmt.where(ClinicalDocument.patient_id == patient_id)
    return stmt


def latest_reviewed_document_updated_at(documents: list[ClinicalDocument]) -> datetime | None:
    timestamps = [document.updated_at for document in documents if document.updated_at is not None]
    return max(timestamps) if timestamps else None


def summary_record_is_stale(record: PatientClinicalSummaryRecord | None, latest_document_updated_at: datetime | None) -> bool:
    return bool(record and latest_document_updated_at and record.updated_at and latest_document_updated_at > record.updated_at)


def latest_summary_records_by_patient(records: list[PatientClinicalSummaryRecord]) -> dict[int, PatientClinicalSummaryRecord]:
    latest: dict[int, PatientClinicalSummaryRecord] = {}
    for record in records:
        if record.patient_id not in latest:
            latest[record.patient_id] = record
    return latest


def summary_record_from_documents(patient_id: int, documents: list[ClinicalDocument]) -> dict:
    source_ids = [document.id for document in documents]
    findings: list[str] = []
    recommendations: list[str] = []
    open_items: list[str] = []
    known_conditions: list[str] = []
    for document in documents:
        for finding in document.key_findings or []:
            target = known_conditions if "gerb" in finding.lower() or "polip" in finding.lower() or "adenom" in finding.lower() else findings
            if finding not in target:
                target.append(finding)
        for recommendation in document.recommendations or []:
            if "ceka" in recommendation.lower() or "pending" in recommendation.lower() or "otvoreno" in recommendation.lower():
                if recommendation not in open_items:
                    open_items.append(recommendation)
            elif recommendation not in recommendations:
                recommendations.append(recommendation)
    summary_text = "AI draft sazetak pacijenta iz pregledanih dokumenata. Lijecnik mora urediti i potvrditi prije sluzbene uporabe."
    if known_conditions or findings:
        summary_text = "AI draft: " + "; ".join((known_conditions + findings)[:5])
    return {
        "patient_id": patient_id,
        "summary_text": summary_text,
        "known_conditions": known_conditions,
        "key_findings": findings,
        "open_items": open_items,
        "risks": [],
        "last_recommendations": recommendations,
        "source_document_ids": source_ids,
        "status": "draft_ai",
        "generated_by": "ai_placeholder",
    }
