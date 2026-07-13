from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import JourneyAISummary, JourneyAISummaryFact, PatientJourney
from app.schemas.journey_timeline import JourneySummaryOut, SummaryFactReview, TimelineItem
from app.services.journey_timeline import build_timeline, generate_local_summary, summary_query
from app.services.patient_journeys import add_event


router = APIRouter(prefix="/api/patient-journeys", tags=["journey-timeline"])


def get_journey(db: Session, journey_id: int) -> PatientJourney:
    journey = db.scalar(
        select(PatientJourney)
        .options(joinedload(PatientJourney.appointment), selectinload(PatientJourney.events))
        .where(PatientJourney.id == journey_id)
    )
    if not journey:
        raise HTTPException(404, detail="Putovanje pacijenta nije pronađeno")
    return journey


@router.get("/{journey_id}/timeline", response_model=list[TimelineItem])
def journey_timeline(
    journey_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("journey.read")),
):
    return build_timeline(db, get_journey(db, journey_id))


@router.post("/{journey_id}/summary", response_model=JourneySummaryOut)
def generate_summary(
    journey_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("summary.generate")),
):
    journey = get_journey(db, journey_id)
    summary = generate_local_summary(db, journey)
    add_event(db, journey, "ai_summary_generated", "Stvoren izvorno povezani AI sažetak; čeka pregled", actor, request, journey.current_stage, journey.current_stage, {"summary_id": summary.id})
    audit(db, "summary_generated", "JourneyAISummary", summary.id, "Stvoren lokalni izvorno povezani sažetak", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(summary), request)
    db.commit()
    return db.scalar(summary_query().where(JourneyAISummary.id == summary.id))


@router.get("/{journey_id}/summary", response_model=JourneySummaryOut)
def get_latest_summary(
    journey_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("journey.read")),
):
    get_journey(db, journey_id)
    summary = db.scalar(summary_query().where(JourneyAISummary.journey_id == journey_id).order_by(JourneyAISummary.generated_at.desc(), JourneyAISummary.id.desc()))
    if not summary:
        raise HTTPException(404, detail="Sažetak nije generiran")
    return summary


@router.patch("/{journey_id}/summary/{summary_id}/facts/{fact_id}", response_model=JourneySummaryOut)
def review_summary_fact(
    journey_id: int,
    summary_id: int,
    fact_id: int,
    payload: SummaryFactReview,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("summary.review")),
):
    summary = db.scalar(summary_query().where(JourneyAISummary.id == summary_id, JourneyAISummary.journey_id == journey_id))
    fact = db.get(JourneyAISummaryFact, fact_id)
    if not summary or not fact or fact.summary_id != summary.id:
        raise HTTPException(404, detail="Tvrdnja sažetka nije pronađena")
    before = snapshot(fact)
    fact.review_status = "accepted" if payload.action == "accept" else "rejected"
    fact.reviewed_by = actor.user_id
    fact.reviewed_at = datetime.now(timezone.utc)
    db.flush()
    if all(item.review_status != "pending_review" for item in summary.facts):
        summary.status = "reviewed"
        summary.reviewed_by = actor.user_id
        summary.reviewed_at = datetime.now(timezone.utc)
    audit(db, "summary_fact_reviewed", "JourneyAISummary", summary.id, f"Tvrdnja {fact.review_status}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(fact), request)
    db.commit()
    return db.scalar(summary_query().where(JourneyAISummary.id == summary.id))
