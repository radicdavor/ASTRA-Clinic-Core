from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Patient, PatientJourney, ReportDeliveryEvent, SignedClinicalReport
from app.schemas.reports import ReportDeliveryOut, ReportDeliveryRequest, ReportPrintOut, SignedReportOut, VisitDocumentOut
from app.services.reports import queue_stub_deliveries, record_print, verify_report_integrity, visit_documents

router = APIRouter(prefix="/api", tags=["signed-reports"])


def report_or_404(db: Session, report_id: int) -> SignedClinicalReport:
    report = db.get(SignedClinicalReport, report_id)
    if not report:
        raise HTTPException(404, detail="Potpisani nalaz nije pronađen")
    return report


@router.get("/patient-journeys/{journey_id}/visit-documents", response_model=list[VisitDocumentOut])
def list_visit_documents(journey_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("documents.view_source"))):
    if not db.get(PatientJourney, journey_id):
        raise HTTPException(404, detail="Dolazak nije pronađen")
    return visit_documents(db, journey_id)


@router.get("/signed-reports/{report_id}", response_model=SignedReportOut)
def preview_report(report_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("reports.read"))):
    report = report_or_404(db, report_id)
    verify_report_integrity(report)
    return report


@router.post("/signed-reports/{report_id}/print", response_model=ReportPrintOut)
def print_report(report_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("reports.print"))):
    if actor.user_id is None:
        raise HTTPException(403, detail="Ispis zahtijeva prijavljenog korisnika")
    report = report_or_404(db, report_id)
    verify_report_integrity(report)
    event = record_print(db, report, actor.user_id, getattr(request.state, "request_id", None))
    audit(db, "signed_report_printed", "SignedClinicalReport", report.id, "Ispisana je točna potpisana verzija nalaza", actor.user_id, actor.actor_type, actor.api_key_id, None, {"print_event_id": event.id}, request)
    db.commit()
    db.refresh(event)
    return event


@router.post("/patient-journeys/{journey_id}/visit-documents/deliver", response_model=list[ReportDeliveryOut])
def deliver_reports(journey_id: int, payload: ReportDeliveryRequest, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("reports.send"))):
    if actor.user_id is None:
        raise HTTPException(403, detail="Dostava zahtijeva prijavljenog ovlaštenog korisnika")
    reports = db.scalars(select(SignedClinicalReport).where(SignedClinicalReport.id.in_(payload.report_ids), SignedClinicalReport.journey_id == journey_id)).all()
    if len(reports) != len(set(payload.report_ids)):
        raise HTTPException(404, detail="Jedan ili više potpisanih nalaza ne pripadaju ovom dolasku")
    journey = db.get(PatientJourney, journey_id)
    patient = db.get(Patient, journey.patient_id)
    if payload.recipient_source == "patient_verified":
        if not patient.email or not patient.email_verified_at or str(payload.recipient).lower() != patient.email.lower():
            raise HTTPException(409, detail="Zadana adresa mora biti potvrđena e-pošta pacijenta")
    elif "reports.send_alternate_recipient" not in actor.permissions:
        raise HTTPException(403, detail="Alternativni primatelj zahtijeva posebno ovlaštenje")
    elif not payload.alternate_recipient_reason:
        raise HTTPException(422, detail="Alternativni primatelj zahtijeva razlog")
    events = queue_stub_deliveries(
        db, reports, str(payload.recipient), actor.user_id, payload.acknowledge_superseded,
        payload.recipient_source, payload.alternate_recipient_reason, payload.idempotency_key,
    )
    for event in events:
        audit(db, "signed_report_delivery_queued", "ReportDeliveryEvent", event.id, "Dostava je evidentirana u demo/stub redu; nije potvrđeno slanje pacijentu", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(event), request)
    db.commit()
    return events


@router.get("/signed-reports/{report_id}/delivery-history", response_model=list[ReportDeliveryOut])
def delivery_history(report_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("reports.delivery_history"))):
    report_or_404(db, report_id)
    return db.scalars(select(ReportDeliveryEvent).where(ReportDeliveryEvent.report_id == report_id).order_by(ReportDeliveryEvent.id.desc())).all()
