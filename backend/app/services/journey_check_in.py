import hashlib
import json
from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import Actor
from app.models.domain import JourneyBlocker, JourneyCheckIn, JourneyCheckInItem, JourneyEvent, PatientJourney
from app.services.patient_journeys import add_event, transition

DEFAULT_ITEMS = [
    ("identity", "patient_data_confirmed", "Opći podaci pacijenta potvrđeni", False),
    ("identity", "consent_status", "Status privole potvrđen", False),
    ("documents", "laboratory_results", "Potrebni laboratorijski nalazi", False),
    ("documents", "anesthesia_questionnaire", "Anesteziološki upitnik", False),
    ("documents", "informed_consent", "Informirani pristanak", False),
    ("preparation", "fasting_6h", "Post (6 sati)", False),
    ("preparation", "bowel_preparation_clear", "Priprema crijeva (stolica bistra)", False),
    ("preparation", "sedation_escort", "Pratnja nakon sedacije", False),
    ("preconditions", "pacemaker", "Elektrostimulator", False),
    ("preconditions", "current_medication", "Lijekovi koje pacijent uzima", False),
    ("preconditions", "drug_allergies", "Alergije na lijekove", False),
    ("preconditions", "other_medical_review", "Druga napomena za liječničku provjeru", False),
]

PRE_RECEPTION_STAGES = {"booked", "awaiting_forms", "awaiting_documents", "preparation_in_progress", "ready_for_arrival", "arrived", "check_in_review"}


def normalize_reception_completion_key(idempotency_key: str | None) -> str | None:
    if idempotency_key is None:
        return None
    cleaned = idempotency_key.strip()
    return cleaned or None


def reception_completion_fingerprint(items_by_key: dict[str, dict]) -> str:
    normalized = {
        key: {
            "note": (payload.get("note") or "").strip(),
            "details": payload.get("details") or {},
            "activity_ids": sorted({int(activity_id) for activity_id in payload.get("activity_ids", []) if str(activity_id).strip()}),
        }
        for key, payload in sorted(items_by_key.items())
    }
    body = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def find_reception_completion_event(db: Session, journey_id: int, idempotency_key: str | None) -> JourneyEvent | None:
    key = normalize_reception_completion_key(idempotency_key)
    if not key:
        return None
    return db.scalar(
        select(JourneyEvent)
        .where(JourneyEvent.journey_id == journey_id, JourneyEvent.event_type == "check_in_reception_completed")
        .where(JourneyEvent.metadata_json["idempotency_key"].as_string() == key)
        .order_by(JourneyEvent.id.desc())
        .limit(1)
    )


def start_check_in(db: Session, journey: PatientJourney, actor: Actor, request: Request):
    if journey.current_stage not in PRE_RECEPTION_STAGES:
        raise HTTPException(409, detail="Tijek pacijenta nije u fazi prijema")
    existing = db.query(JourneyCheckIn).filter_by(journey_id=journey.id).one_or_none()
    if existing:
        return existing
    now = datetime.now(timezone.utc)
    item = JourneyCheckIn(journey_id=journey.id, status="in_review", arrived_at=now, started_by=actor.user_id)
    db.add(item)
    db.flush()
    for position, (category, key, label, clinical) in enumerate(DEFAULT_ITEMS):
        db.add(JourneyCheckInItem(check_in_id=item.id, category=category, item_key=key, label=label, requires_clinician=clinical, position=position))
    journey.check_in_status = "in_review"
    journey.appointment.arrived_at = journey.appointment.arrived_at or now
    if journey.current_stage in {"booked", "awaiting_forms", "awaiting_documents", "preparation_in_progress"}:
        transition(db, journey, "ready_for_arrival", actor, request, "Pacijent stigao na prijem")
    if journey.current_stage == "ready_for_arrival":
        transition(db, journey, "arrived", actor, request, "Pacijent stigao")
    if journey.current_stage == "arrived":
        transition(db, journey, "check_in_review", actor, request, "Započeta prijemna provjera")
    db.flush()
    return item


def update_item(db: Session, journey: PatientJourney, check_in: JourneyCheckIn, item: JourneyCheckInItem, state: str, note: str | None, actor: Actor, request: Request):
    if item.requires_clinician and state in {"confirmed", "not_applicable"} and "checkin.clinical_review" not in actor.permissions:
        raise HTTPException(403, detail="Kliničku stavku mora potvrditi ovlašteni liječnik")
    before = item.state
    item.state = state
    item.note = note
    item.updated_by = actor.user_id
    if state in {"blocked", "requires_clinician_review"}:
        open_blocker = db.query(JourneyBlocker).filter_by(journey_id=journey.id, blocker_key=f"checkin:{item.item_key}", status="open").one_or_none()
        if not open_blocker:
            db.add(JourneyBlocker(journey_id=journey.id, blocker_key=f"checkin:{item.item_key}", category=item.category, title=item.label, details=note, is_clinical=item.requires_clinician or state == "requires_clinician_review", created_by=actor.user_id))
    db.flush()
    states = [current.state for current in check_in.items]
    if any(value == "blocked" for value in states):
        check_in.status = "blocked"
        journey.check_in_status = "blocked"
    elif any(value == "requires_clinician_review" for value in states):
        check_in.status = "in_review"
        journey.check_in_status = "in_review"
    elif states and all(value in {"confirmed", "not_applicable"} for value in states) and not any(blocker.status == "open" for blocker in journey.blockers):
        check_in.status = "ready"
        check_in.completed_at = datetime.now(timezone.utc)
        check_in.completed_by = actor.user_id
        journey.check_in_status = "ready"
        transition(db, journey, "ready_for_clinician", actor, request, "Prijemna provjera dovršena")
    else:
        check_in.status = "in_review"
        journey.check_in_status = "in_review"
    add_event(db, journey, "check_in_item_updated", f"{item.label}: {state}", actor, request, journey.current_stage, journey.current_stage, {"item_id": item.id, "before": before, "after": state})


def complete_reception_check_in(db: Session, journey: PatientJourney, check_in: JourneyCheckIn, items_by_key: dict[str, dict], actor: Actor, request: Request, idempotency_key: str | None = None, payload_fingerprint: str | None = None):
    red_flags = {
        key: payload
        for key, payload in items_by_key.items()
        if isinstance(payload.get("note"), str) and payload["note"].strip()
    }
    activity_ids = {activity.id for activity in journey.activities}
    changed = []
    for item in check_in.items:
        before = item.state
        if item.item_key == "patient_data_confirmed":
            item.state = "confirmed"
            item.note = None
            item.details_json = {}
            item.activity_ids_json = []
        elif item.item_key in red_flags:
            payload = red_flags[item.item_key]
            linked_activity_ids = [int(activity_id) for activity_id in payload.get("activity_ids", []) if int(activity_id) in activity_ids]
            item.state = "requires_clinician_review"
            item.note = payload["note"].strip()
            item.details_json = payload.get("details") or {}
            item.activity_ids_json = linked_activity_ids
            item.medical_disposition = None
            item.medical_disposition_note = None
            item.medical_reviewed_by = None
            item.medical_reviewed_at = None
        else:
            item.state = "not_applicable"
            item.note = None
            item.details_json = {}
            item.activity_ids_json = []
        item.updated_by = actor.user_id
        changed.append({"item_key": item.item_key, "before": before, "after": item.state, "note": item.note, "activity_ids": item.activity_ids_json})
    check_in.status = "ready"
    check_in.completed_at = datetime.now(timezone.utc)
    check_in.completed_by = actor.user_id
    journey.check_in_status = "ready"
    transition(db, journey, "ready_for_clinician", actor, request, "Prijem završen; pacijent čeka pregled/pretragu")
    add_event(
        db,
        journey,
        "check_in_reception_completed",
        "Prijem zavrsen",
        actor,
        request,
        "check_in_review",
        journey.current_stage,
        {"items": changed, "idempotency_key": normalize_reception_completion_key(idempotency_key), "payload_fingerprint": payload_fingerprint},
    )


def record_medical_disposition(db: Session, journey: PatientJourney, item: JourneyCheckInItem, disposition: str, note: str, actor: Actor, request: Request):
    if item.state != "requires_clinician_review":
        raise HTTPException(409, detail="Stavka ne čeka liječničku provjeru")
    before = {"state": item.state, "medical_disposition": item.medical_disposition}
    item.medical_disposition = disposition
    item.medical_disposition_note = note.strip()
    item.medical_reviewed_by = actor.user_id
    item.medical_reviewed_at = datetime.now(timezone.utc)
    if disposition in {"accepted_for_review", "proceed"}:
        item.state = "confirmed"
    elif disposition == "modify_plan":
        item.state = "requires_clinician_review"
    else:
        item.state = "blocked"
    item.updated_by = actor.user_id
    add_event(db, journey, "check_in_medical_disposition", f"{item.label}: {disposition}", actor, request, journey.current_stage, journey.current_stage, {"item_id": item.id, "before": before, "after": {"state": item.state, "medical_disposition": disposition}})
