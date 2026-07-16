from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor
from app.models.domain import ClinicalDocument, JourneyActivity, PathologyCase, PathologyReportLink, PathologySpecimen, ProcedureIntervention
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


def review_result(db: Session, case: PathologyCase, actor: Actor, request: Request) -> None:
    if case.status != "clinician_review_required":
        raise HTTPException(409, detail="Patološki nalaz nije u stanju za liječnički pregled")
    case.status = "clinician_reviewed"
    case.reviewed_at = datetime.now(timezone.utc)
    case.reviewed_by = actor.user_id
    audit(db, "pathology_result_reviewed", "PathologyCase", case.id, "Liječnik je pregledao patološki nalaz", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(case), request)
