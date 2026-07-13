from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.domain import (
    ClinicalDocument,
    CommunicationEvent,
    DocumentRequest,
    Invoice,
    JourneyAISummary,
    JourneyAISummaryFact,
    LabOrder,
    PatientJourney,
)


LOCAL_SUMMARY_PROVIDER = "local-deterministic-source-index"
LOCAL_SUMMARY_MODEL = "program2-safe-stub-v1"


def _as_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def build_timeline(db: Session, journey: PatientJourney) -> list[dict]:
    appointment = journey.appointment
    appointment_time = datetime.combine(
        appointment.date,
        appointment.start_time,
        tzinfo=ZoneInfo("Europe/Zagreb"),
    )
    items = [{
        "date": appointment_time,
        "event_type": "appointment",
        "title": "Termin",
        "summary": f"Planirana usluga #{appointment.service_id}",
        "source_url": f"/appointments/{appointment.id}",
        "provenance": {"entity": "Appointment", "id": appointment.id},
        "review_state": appointment.status,
        "journey_id": journey.id,
    }]
    for event in journey.events:
        items.append({
            "date": _as_datetime(event.created_at), "event_type": event.event_type,
            "title": event.summary, "summary": None,
            "source_url": f"/patient-journeys/{journey.id}",
            "provenance": {"entity": "JourneyEvent", "id": event.id, "source_channel": event.source_channel},
            "review_state": None, "journey_id": journey.id,
        })
    documents = db.scalars(select(ClinicalDocument).where(ClinicalDocument.journey_id == journey.id)).all()
    for document in documents:
        items.append({
            "date": _as_datetime(document.received_at or document.created_at),
            "event_type": "clinical_document", "title": document.title,
            "summary": "Izvorni dokument dostupan",
            "source_url": f"/api/clinical-documents/{document.id}/source",
            "provenance": {"entity": "ClinicalDocument", "id": document.id, "checksum": document.checksum_sha256},
            "review_state": document.review_status, "journey_id": journey.id,
        })
    communications = db.scalars(select(CommunicationEvent).where(CommunicationEvent.journey_id == journey.id)).all()
    for event in communications:
        items.append({
            "date": _as_datetime(event.sent_at or event.scheduled_at or event.created_at),
            "event_type": "communication", "title": event.template_key,
            "summary": f"Kanal: {event.channel}", "source_url": None,
            "provenance": {"entity": "CommunicationEvent", "id": event.id, "correlation_id": event.correlation_id},
            "review_state": event.status, "journey_id": journey.id,
        })
    lab_orders = db.scalars(select(LabOrder).where(LabOrder.appointment_id == appointment.id)).all()
    for order in lab_orders:
        items.append({
            "date": datetime.combine(order.ordered_at, datetime.min.time(), tzinfo=ZoneInfo("Europe/Zagreb")),
            "event_type": "laboratory", "title": f"Laboratorijska narudžba #{order.id}",
            "summary": None, "source_url": f"/laboratory/{order.id}",
            "provenance": {"entity": "LabOrder", "id": order.id},
            "review_state": order.status, "journey_id": journey.id,
        })
    invoices = db.scalars(select(Invoice).where(Invoice.appointment_id == appointment.id)).all()
    for invoice in invoices:
        items.append({
            "date": datetime.combine(invoice.invoice_date, datetime.min.time(), tzinfo=ZoneInfo("Europe/Zagreb")),
            "event_type": "billing", "title": f"Račun {invoice.invoice_number}",
            "summary": None, "source_url": f"/invoices/{invoice.id}",
            "provenance": {"entity": "Invoice", "id": invoice.id},
            "review_state": invoice.status, "journey_id": journey.id,
        })
    return sorted(items, key=lambda item: item["date"], reverse=True)


def generate_local_summary(db: Session, journey: PatientJourney) -> JourneyAISummary:
    documents = db.scalars(select(ClinicalDocument).where(ClinicalDocument.journey_id == journey.id).order_by(ClinicalDocument.id)).all()
    missing_requests = db.scalars(
        select(DocumentRequest).where(
            DocumentRequest.journey_id == journey.id,
            DocumentRequest.mandatory.is_(True),
            DocumentRequest.status.notin_({"received", "resolved"}),
        )
    ).all()
    source_refs = [{"document_id": item.id, "url": f"/api/clinical-documents/{item.id}/source", "checksum": item.checksum_sha256} for item in documents]
    summary = JourneyAISummary(
        journey_id=journey.id,
        provider=LOCAL_SUMMARY_PROVIDER,
        model_name=LOCAL_SUMMARY_MODEL,
        status="pending_review",
        content_json={
            "label": "AI-generirani sažetak — obavezan pregled liječnika",
            "major_diagnoses": [], "prior_procedures": [], "allergies": [], "medications": [],
            "antiplatelet_or_anticoagulant_therapy": [], "diabetes_therapy": [],
            "pathology": [], "imaging": [],
            "open_questions": [f"Nedostaje: {item.title}" for item in missing_requests],
            "preparation_concerns": [],
        },
        source_refs_json=source_refs,
        limitations_json=[
            "Lokalni stub ne izvodi dijagnoze ni kliničke zaključke.",
            "Prazno polje znači da podatak nije izdvojen; ne znači normalan nalaz.",
            "Svaka tvrdnja mora biti pojedinačno ljudski pregledana.",
        ],
    )
    db.add(summary)
    db.flush()
    for document in documents:
        if document.physician_reviewed and document.ai_summary:
            statement = document.ai_summary
            confidence = Decimal("1.0000")
            limitation = "Preuzeto iz liječnički pregledanog sažetka dokumenta."
        else:
            statement = f"Dokument je dostupan: {document.title}"
            confidence = Decimal("1.0000")
            limitation = "Sadržaj dokumenta nije prihvaćen kao klinička činjenica."
        db.add(JourneyAISummaryFact(
            summary_id=summary.id, statement=statement, fact_type="source_fact",
            source_document_id=document.id, confidence=confidence, limitation=limitation,
        ))
    for request in missing_requests:
        db.add(JourneyAISummaryFact(
            summary_id=summary.id, statement=f"Nedostaje obvezni dokument: {request.title}",
            fact_type="missing_information", confidence=Decimal("1.0000"),
            limitation="Administrativno stanje zahtjeva; nije klinički nalaz.",
        ))
    if not documents and not missing_requests:
        db.add(JourneyAISummaryFact(
            summary_id=summary.id,
            statement="Nema izvornih dokumenata povezanih s ovim tijekom pacijenta.",
            fact_type="missing_information",
            confidence=Decimal("1.0000"),
            limitation="Nedostatak izvora nije normalan nalaz.",
        ))
    db.flush()
    return summary


def summary_query():
    return select(JourneyAISummary).options(selectinload(JourneyAISummary.facts))
