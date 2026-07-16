from datetime import date, datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.domain import (
    ClinicalDocument,
    ClinicalFormInstance,
    JourneyActivity,
    PatientJourney,
    ReportDeliveryEvent,
    ReportPrintEvent,
    SignedClinicalReport,
    User,
)

def report_digest(rendered_content: str, structured_data: dict) -> str:
    canonical = json.dumps(structured_data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(f"{rendered_content}\n{canonical}".encode()).hexdigest()


def verify_report_integrity(report: SignedClinicalReport) -> None:
    if report.hash_algorithm != "sha256":
        raise HTTPException(409, detail="Algoritam provjere potpisanog nalaza nije podržan. Radnja je zaustavljena.")
    if report_digest(report.rendered_content, report.structured_data_json) != report.content_hash:
        raise HTTPException(409, detail="Integritet potpisanog nalaza nije potvrđen. Radnja je zaustavljena.")


def create_signed_report(db: Session, instance: ClinicalFormInstance, actor_user_id: int) -> SignedClinicalReport:
    existing = db.scalar(select(SignedClinicalReport).where(SignedClinicalReport.form_instance_id == instance.id))
    if existing:
        return existing
    if instance.status != "signed" or not instance.signed_at:
        raise HTTPException(409, detail="Izvještaj se može izraditi samo iz potpisanog obrasca")
    activity = db.get(JourneyActivity, instance.activity_id)
    journey = db.get(PatientJourney, activity.journey_id) if activity else None
    signer = db.get(User, actor_user_id)
    if not activity or not journey or not signer:
        raise HTTPException(409, detail="Nedostaje kontekst aktivnosti, dolaska ili potpisnika")
    previous = None
    version_number = 1
    if instance.amended_from_instance_id:
        previous = db.scalar(select(SignedClinicalReport).where(SignedClinicalReport.form_instance_id == instance.amended_from_instance_id))
        if previous:
            version_number = previous.version_number + 1
            previous.superseded_at = instance.signed_at
    document_type = instance.form_version.output_document_type
    title = f"{instance.form_version.definition.name} — potpisani nalaz"
    document = ClinicalDocument(
        patient_id=journey.patient_id,
        source_type="generated_signed_report",
        document_type=document_type,
        origin="ASTRA Clinic Core",
        document_date=date.today(),
        title=title,
        author=signer.full_name,
        institution="ASTRA Clinic",
        raw_text=instance.rendered_summary or "",
        review_status="signed",
        physician_reviewed=True,
        reviewed_by=actor_user_id,
        reviewed_at=instance.signed_at,
        appointment_id=activity.appointment_id,
        journey_id=journey.id,
        upload_channel="generated",
        lifecycle_status="reviewed",
        provenance_json={"form_instance_id": instance.id, "form_version_id": instance.form_version_id, "activity_id": activity.id},
        received_at=instance.signed_at,
    )
    db.add(document)
    db.flush()
    report = SignedClinicalReport(
        form_instance_id=instance.id,
        form_version_id=instance.form_version_id,
        clinical_document_id=document.id,
        activity_id=activity.id,
        journey_id=journey.id,
        patient_id=journey.patient_id,
        document_type=document_type,
        title=title,
        structured_data_json=dict(instance.data_json),
        rendered_content=instance.rendered_summary or "",
        version_number=version_number,
        signer_user_id=actor_user_id,
        signer_name=signer.full_name,
        signed_at=instance.signed_at,
        supersedes_report_id=previous.id if previous else None,
        content_hash=report_digest(instance.rendered_summary or "", dict(instance.data_json)),
        hash_algorithm="sha256",
    )
    db.add(report)
    db.flush()
    return report


def record_print(db: Session, report: SignedClinicalReport, actor_user_id: int, request_id: str | None) -> ReportPrintEvent:
    event = ReportPrintEvent(report_id=report.id, printed_by=actor_user_id, request_id=request_id)
    db.add(event)
    db.flush()
    return event


def queue_stub_deliveries(db: Session, reports: list[SignedClinicalReport], recipient: str, actor_user_id: int, acknowledge_superseded: bool, recipient_source: str = "patient_verified", alternate_reason: str | None = None, idempotency_key: str | None = None) -> list[ReportDeliveryEvent]:
    if any(report.superseded_at for report in reports) and not acknowledge_superseded:
        raise HTTPException(409, detail="Odabrana je zamijenjena verzija. Potrebna je izričita potvrda.")
    mode = get_settings().reminder_provider_mode
    if mode != "local_demo":
        raise HTTPException(503, detail="Produkcijski pružatelj dostave nalaza nije konfiguriran u ovom modulu")
    events = []
    for report in reports:
        verify_report_integrity(report)
        event_key = f"{idempotency_key}:{report.id}" if idempotency_key else None
        existing = db.scalar(select(ReportDeliveryEvent).where(ReportDeliveryEvent.idempotency_key == event_key)) if event_key else None
        if existing:
            events.append(existing)
            continue
        event = ReportDeliveryEvent(
            report_id=report.id,
            channel="email",
            recipient=recipient,
            status="queued_stub",
            provider_mode="local_demo",
            initiated_by=actor_user_id,
            approved_by=actor_user_id,
            correlation_id=str(uuid4()),
            recipient_source=recipient_source,
            alternate_recipient_reason=alternate_reason,
            idempotency_key=event_key,
        )
        db.add(event)
        events.append(event)
    db.flush()
    return events


def visit_documents(db: Session, journey_id: int) -> list[dict]:
    reports = db.scalars(select(SignedClinicalReport).where(SignedClinicalReport.journey_id == journey_id).order_by(SignedClinicalReport.signed_at, SignedClinicalReport.id)).all()
    result = []
    for report in reports:
        verify_report_integrity(report)
        print_count = db.scalar(select(func.count(ReportPrintEvent.id)).where(ReportPrintEvent.report_id == report.id)) or 0
        delivery = db.scalar(select(ReportDeliveryEvent).where(ReportDeliveryEvent.report_id == report.id).order_by(ReportDeliveryEvent.id.desc()).limit(1))
        result.append({"report": report, "print_count": print_count, "latest_delivery": delivery})
    return result
