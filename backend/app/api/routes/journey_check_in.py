from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import JourneyCheckIn, JourneyCheckInItem, PatientJourney
from app.schemas.journey_check_in import CheckInItemUpdate, CheckInMedicalDisposition, CheckInOut, ReceptionCheckInComplete
from app.services.journey_check_in import complete_reception_check_in, find_reception_completion_event, reception_completion_fingerprint, record_medical_disposition, start_check_in, update_item

router = APIRouter(prefix="/api/patient-journeys", tags=["journey-check-in"])


def journey_query():
    return select(PatientJourney).options(joinedload(PatientJourney.appointment), selectinload(PatientJourney.blockers))


def checkin_query():
    return select(JourneyCheckIn).options(selectinload(JourneyCheckIn.items))


def get_journey(db, id):
    item = db.scalar(journey_query().where(PatientJourney.id == id))
    if not item:
        raise HTTPException(404, detail="Tijek pacijenta nije pronađen")
    return item


@router.post("/{journey_id}/check-in", response_model=CheckInOut)
def begin(journey_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("checkin.update"))):
    journey = get_journey(db, journey_id)
    before = snapshot(journey)
    item = start_check_in(db, journey, actor, request)
    audit(db, "checkin_started", "PatientJourney", journey.id, "Započeta prijemna provjera", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(journey), request)
    db.commit()
    return db.scalar(checkin_query().where(JourneyCheckIn.id == item.id))


@router.get("/{journey_id}/check-in", response_model=CheckInOut)
def detail(journey_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("journey.read"))):
    item = db.scalar(checkin_query().where(JourneyCheckIn.journey_id == journey_id))
    if not item:
        raise HTTPException(404, detail="Prijemna provjera nije započeta")
    return item


@router.patch("/{journey_id}/check-in/items/{item_id}", response_model=CheckInOut)
def change_item(journey_id: int, item_id: int, payload: CheckInItemUpdate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("checkin.update"))):
    journey = get_journey(db, journey_id)
    check_in = db.scalar(checkin_query().where(JourneyCheckIn.journey_id == journey_id))
    item = db.get(JourneyCheckInItem, item_id)
    if not check_in or not item or item.check_in_id != check_in.id:
        raise HTTPException(404, detail="Stavka prijemne provjere nije pronađena")
    before = snapshot(item)
    update_item(db, journey, check_in, item, payload.state, payload.note, actor, request)
    audit(db, "checkin_item_changed", "PatientJourney", journey.id, item.label, actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request)
    db.commit()
    return db.scalar(checkin_query().where(JourneyCheckIn.id == check_in.id))


@router.post("/{journey_id}/check-in/confirm-administrative", response_model=CheckInOut)
def confirm_administrative(journey_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("checkin.update"))):
    journey = get_journey(db, journey_id)
    check_in = db.scalar(checkin_query().where(JourneyCheckIn.journey_id == journey_id))
    if not check_in:
        raise HTTPException(404, detail="Prijemna provjera nije započeta")
    changed = []
    for item in check_in.items:
        if item.item_key != "patient_data_confirmed" or item.requires_clinician or item.state in {"confirmed", "not_applicable"}:
            continue
        before = snapshot(item)
        update_item(db, journey, check_in, item, "confirmed", item.note, actor, request)
        changed.append(item.item_key)
        audit(db, "checkin_item_changed", "PatientJourney", journey.id, item.label, actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request)
    audit(db, "checkin_administrative_confirmed", "PatientJourney", journey.id, "Opći podaci pacijenta potvrđeni", actor.user_id, actor.actor_type, actor.api_key_id, None, {"items": changed}, request)
    db.commit()
    return db.scalar(checkin_query().where(JourneyCheckIn.id == check_in.id))


@router.post("/{journey_id}/check-in/complete-reception", response_model=CheckInOut)
def complete_reception(journey_id: int, payload: ReceptionCheckInComplete, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("checkin.update"))):
    journey = get_journey(db, journey_id)
    before = snapshot(journey)
    check_in = db.scalar(checkin_query().where(JourneyCheckIn.journey_id == journey_id))
    if not check_in:
        check_in = start_check_in(db, journey, actor, request)
        db.flush()
        check_in = db.scalar(checkin_query().where(JourneyCheckIn.id == check_in.id))
    known = {item.item_key for item in check_in.items}
    unknown = [item.item_key for item in payload.items if item.item_key not in known]
    if unknown:
        raise HTTPException(422, detail=f"Nepoznata prijemna stavka: {', '.join(unknown)}")
    items_by_key = {item.item_key: {"note": item.note, "details": item.details, "activity_ids": item.activity_ids} for item in payload.items}
    payload_fingerprint = reception_completion_fingerprint(items_by_key)
    existing_event = find_reception_completion_event(db, journey.id, payload.idempotency_key)
    if existing_event:
        metadata = existing_event.metadata_json or {}
        if metadata.get("payload_fingerprint") != payload_fingerprint:
            raise HTTPException(409, detail={"code": "idempotency_conflict", "message": "Ova oznaka dovrsetka prijema vec je iskoristena za drugi sadrzaj."})
        return db.scalar(checkin_query().where(JourneyCheckIn.id == check_in.id))
    if journey.current_stage not in {"arrived", "check_in_review"}:
        raise HTTPException(409, detail="Prijem se može završiti samo prije pregleda")
    complete_reception_check_in(
        db,
        journey,
        check_in,
        items_by_key,
        actor,
        request,
        payload.idempotency_key,
        payload_fingerprint,
    )
    audit(db, "checkin_reception_completed", "PatientJourney", journey.id, "Prijem završen; pacijent čeka pregled/pretragu", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(journey), request)
    db.commit()
    return db.scalar(checkin_query().where(JourneyCheckIn.id == check_in.id))


@router.post("/{journey_id}/check-in/items/{item_id}/medical-disposition", response_model=CheckInOut)
def medical_disposition(journey_id: int, item_id: int, payload: CheckInMedicalDisposition, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("checkin.clinical_review"))):
    journey = get_journey(db, journey_id)
    check_in = db.scalar(checkin_query().where(JourneyCheckIn.journey_id == journey_id))
    item = db.get(JourneyCheckInItem, item_id)
    if not check_in or not item or item.check_in_id != check_in.id:
        raise HTTPException(404, detail="Stavka prijemne provjere nije pronađena")
    before = snapshot(item)
    record_medical_disposition(db, journey, item, payload.disposition, payload.note, actor, request)
    audit(db, "checkin_medical_disposition", "PatientJourney", journey.id, item.label, actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request)
    db.commit()
    return db.scalar(checkin_query().where(JourneyCheckIn.id == check_in.id))
