from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import JourneyActivity, PatientJourney
from app.schemas.patient_journeys import JourneyActivityCreate, JourneyActivityOut, JourneyActivityStatusUpdate
from app.services.journey_activities import create_activity, get_activity, transition_activity


router = APIRouter(prefix="/api/patient-journeys", tags=["journey-activities"])


def get_journey(db: Session, journey_id: int) -> PatientJourney:
    journey = db.scalar(
        select(PatientJourney)
        .options(joinedload(PatientJourney.appointment))
        .where(PatientJourney.id == journey_id)
    )
    if not journey:
        raise HTTPException(404, detail="Tijek pacijenta nije pronađen")
    return journey


@router.get("/{journey_id}/activities", response_model=list[JourneyActivityOut])
def list_activities(
    journey_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("journey.read")),
):
    get_journey(db, journey_id)
    return db.scalars(
        select(JourneyActivity)
        .where(JourneyActivity.journey_id == journey_id)
        .order_by(JourneyActivity.sequence)
    ).all()


@router.post("/{journey_id}/activities", response_model=JourneyActivityOut, status_code=201)
def add_activity(
    journey_id: int,
    payload: JourneyActivityCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    journey = get_journey(db, journey_id)
    activity = create_activity(db, journey, payload.model_dump(), actor, request)
    db.commit()
    db.refresh(activity)
    return activity


@router.post("/{journey_id}/activities/{activity_id}/transition", response_model=JourneyActivityOut)
def change_activity_status(
    journey_id: int,
    activity_id: int,
    payload: JourneyActivityStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("journey.transition")),
):
    journey = get_journey(db, journey_id)
    activity = get_activity(db, journey_id, activity_id)
    transition_activity(db, journey, activity, payload.target_status, payload.reason, actor, request)
    db.commit()
    db.refresh(activity)
    return activity
