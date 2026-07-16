from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor
from app.models.domain import ClinicalDocument, JourneyActivity, PathologyCase, PathologyReportLink, PathologySpecimen, ProcedureIntervention, ReportDeliveryEvent, SignedClinicalReport
from app.services.patient_journeys import add_event


def create_case(db: Session, journey, activity: JourneyActivity, data: dict, actor: Actor, request: Request) -> tuple[PathologyCase, bool]:
    key = data.get("idempotency_key") or f"pathology-activity-{activity.id}"
    existing = db.scalar(select(PathologyCase).where(PathologyCase.idempotency_key == key))
    if existing:
        if existing.source_activity_id != activity.id:
            raise HTTPException(409, detail="Idempotency oznaka već pripada drugoj aktivnosti")
        return existing, False

    interventions = {}
    for specimen in data["specimens"]:
        intervention = db.get(ProcedureIntervention, specimen["source_intervention_id"])
        if not intervention or intervention.activity_id != activity.id:
            raise HTTPException(422, detail="Izvorna intervencija uzorka ne pripada odabranoj aktivnosti")
        if intervention.intervention_type not in {"biopsy", "polypectomy"}:
            raise HTTPException(422, detail="Patološki uzorak može nastati samo iz biopsije ili dohvaćene polipektomije")
        if intervention.intervention_type == "polypectomy" and intervention.retrieval_status not in {"retrieved", "collected"}:
            raise HTTPException(422, detail="Polipektomijski uzorak mora biti označen kao dohvaćen")
        interventions[intervention.id] = intervention

    collected = min(item["collection_time"] for item in data["specimens"])
    case = PathologyCase(
        patient_id=journey.patient_id,
        journey_id=journey.id,
        source_activity_id=activity.id,
        idempotency_key=key,
        status="specimens_ready",
        external_lab=data.get("external_lab"),
        created_by=actor.user_id,
        collected_at=collected,
    )
    db.add(case); db.flush()
    for item in data["specimens"]:
        db.add(PathologySpecimen(case_id=case.id, **item))
    db.flush()
    audit(db, "pathology_case_created", "PathologyCase", case.id, "Stvoren patološki slučaj s označenim uzorcima", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(case), request)
    add_event(db, journey, "pathology_case_created", "Stvoren patološki slučaj", actor, request, journey.current_stage, journey.current_stage, {"activity_id": activity.id, "pathology_case_id": case.id})
    return case, True


def link_result(db: Session, case: PathologyCase, document_id: int, actor: Actor, request: Request) -> None:
    document = db.get(ClinicalDocument, document_id)
    if not document or document.patient_id != case.patient_id:
        raise HTTPException(422, detail="Patološki nalaz mora pripadati istom pacijentu")
    existing = db.scalar(select(PathologyReportLink).where(PathologyReportLink.case_id == case.id, PathologyReportLink.clinical_document_id == document.id))
    if not existing:
        db.add(PathologyReportLink(case_id=case.id, clinical_document_id=document.id, linked_by=actor.user_id))
    now = datetime.now(timezone.utc)
    case.result_received_at = case.result_received_at or now
    case.status = "clinician_review_required"
    audit(db, "pathology_result_linked", "PathologyCase", case.id, "Izvorni patološki nalaz povezan; potreban pregled liječnika", actor.user_id, actor.actor_type, actor.api_key_id, None, {"clinical_document_id": document.id, "status": case.status}, request)


PATHOLOGY_TRANSITIONS = {
    "specimens_ready": {"sent_to_lab", "cancelled"},
    "sent_to_lab": {"received_by_lab", "awaiting_result", "cancelled"},
    "received_by_lab": {"awaiting_result", "cancelled"},
    "awaiting_result": {"cancelled"},
    "clinician_reviewed": {"patient_notification_ready"},
    "patient_notification_ready": {"patient_notified"},
    "patient_notified": {"closed"},
}


def transition_case(db: Session, case: PathologyCase, target: str, external_case_number: str | None, reason: str | None, actor: Actor, request: Request) -> None:
    if target == "closed":
        if case.status not in {"clinician_reviewed", "patient_notification_ready", "patient_notified"} or not case.communication_disposition:
            raise HTTPException(409, detail="Patološki slučaj zahtijeva dokumentiranu komunikacijsku odluku prije zatvaranja")
    elif target not in PATHOLOGY_TRANSITIONS.get(case.status, set()):
        raise HTTPException(409, detail=f"Prijelaz patologije {case.status} → {target} nije dopušten")
    if target == "cancelled" and not reason:
        raise HTTPException(422, detail="Otkazivanje patološkog slučaja zahtijeva razlog")
    if target == "patient_notified":
        delivered = db.scalar(select(ReportDeliveryEvent.id).join(SignedClinicalReport, SignedClinicalReport.id == ReportDeliveryEvent.report_id).join(PathologyReportLink, PathologyReportLink.clinical_document_id == SignedClinicalReport.clinical_document_id).where(PathologyReportLink.case_id == case.id, ReportDeliveryEvent.status == "delivered").limit(1))
        if not delivered:
            raise HTTPException(409, detail="Pacijent se može označiti obaviještenim tek nakon potvrđene dostave odobrene verzije nalaza")
    now = datetime.now(timezone.utc)
    before = snapshot(case)
    case.status = target
    if external_case_number: case.external_case_number = external_case_number
    if target == "sent_to_lab": case.sent_at = now
    elif target == "received_by_lab": case.lab_received_at = now
    elif target == "patient_notified": case.patient_notified_at = now
    elif target in {"closed", "cancelled"}: case.closed_at = now
    audit(db, "pathology_status_changed", "PathologyCase", case.id, reason or f"Patologija: {target}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(case), request)


def decide_communication(db: Session, case: PathologyCase, disposition: str, note: str | None, attempts: int, actor: Actor, request: Request) -> None:
    if case.status not in {"clinician_reviewed", "patient_notification_ready", "patient_notified"}:
        raise HTTPException(409, detail="Komunikacijska odluka moguća je tek nakon liječničkog pregleda")
    if disposition in {"direct_contact", "reviewed_at_follow_up_visit", "no_notification_required", "patient_declined", "transferred_to_external_care", "cancelled_as_duplicate"} and not note:
        raise HTTPException(422, detail="Odabrana komunikacijska odluka zahtijeva bilješku")
    if disposition == "unable_to_contact" and attempts < 3:
        raise HTTPException(422, detail="Nemoguć kontakt zahtijeva najmanje tri dokumentirana pokušaja")
    if disposition == "delivered_approved_report":
        delivered = db.scalar(select(ReportDeliveryEvent.id).join(SignedClinicalReport).join(PathologyReportLink, PathologyReportLink.clinical_document_id == SignedClinicalReport.clinical_document_id).where(PathologyReportLink.case_id == case.id, ReportDeliveryEvent.status == "delivered").limit(1))
        if not delivered:
            raise HTTPException(409, detail="Nema potvrđene dostave odobrenog nalaza")
    case.communication_disposition = disposition
    case.communication_note = note
    case.communication_attempts = attempts
    case.communication_decided_by = actor.user_id
    case.communication_decided_at = datetime.now(timezone.utc)
    audit(db, "pathology_communication_disposition", "PathologyCase", case.id, f"Komunikacijska odluka: {disposition}", actor.user_id, actor.actor_type, actor.api_key_id, None, {"disposition": disposition, "attempts": attempts}, request)


def review_result(db: Session, case: PathologyCase, actor: Actor, request: Request) -> None:
    if case.status != "clinician_review_required":
        raise HTTPException(409, detail="Patološki nalaz nije u stanju za liječnički pregled")
    case.status = "clinician_reviewed"
    case.reviewed_at = datetime.now(timezone.utc)
    case.reviewed_by = actor.user_id
    audit(db, "pathology_result_reviewed", "PathologyCase", case.id, "Liječnik je pregledao patološki nalaz", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(case), request)
