from datetime import datetime, timezone
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from app.auth.dependencies import Actor
from app.models.domain import JourneyBlocker, JourneyCheckIn, JourneyCheckInItem, PatientJourney
from app.services.patient_journeys import add_event, transition

DEFAULT_ITEMS = [
    ("identity", "identity_confirmed", "Identitet potvrđen", False), ("identity", "contact_confirmed", "Kontaktni podaci potvrđeni", False),
    ("identity", "payer_confirmed", "Platitelj ili osiguranje potvrđeni", False), ("identity", "consent_confirmed", "Status privole potvrđen", False),
    ("documents", "referral", "Uputnica", False), ("documents", "laboratory_results", "Potrebni laboratorijski nalazi", False),
    ("documents", "prior_reports", "Raniji relevantni nalazi", False), ("documents", "anesthesia_questionnaire", "Anesteziološki upitnik", True),
    ("documents", "informed_consent", "Informirani pristanak", True), ("preparation", "fasting", "Post", True),
    ("preparation", "bowel_preparation", "Priprema crijeva", True), ("preparation", "escort", "Pratnja nakon sedacije", True),
    ("preconditions", "anticoagulants", "Antikoagulantna terapija", True), ("preconditions", "antiplatelets", "Antiagregacijska terapija", True),
    ("preconditions", "diabetes_therapy", "Terapija šećerne bolesti", True), ("preconditions", "allergies", "Alergije", True),
    ("preconditions", "pregnancy", "Trudnoća, gdje je relevantno", True), ("preconditions", "implants", "Elektrostimulator ili implantati", True),
]

def start_check_in(db: Session, journey: PatientJourney, actor: Actor, request: Request):
    if journey.current_stage not in {"ready_for_arrival", "arrived", "check_in_review"}: raise HTTPException(409, detail="Tijek pacijenta nije u fazi prijema")
    existing = db.query(JourneyCheckIn).filter_by(journey_id=journey.id).one_or_none()
    if existing: return existing
    now = datetime.now(timezone.utc); item = JourneyCheckIn(journey_id=journey.id, status="in_review", arrived_at=now, started_by=actor.user_id); db.add(item); db.flush()
    for position, (category, key, label, clinical) in enumerate(DEFAULT_ITEMS): db.add(JourneyCheckInItem(check_in_id=item.id, category=category, item_key=key, label=label, requires_clinician=clinical, position=position))
    journey.check_in_status="in_review"; journey.appointment.arrived_at=journey.appointment.arrived_at or now
    if journey.current_stage == "ready_for_arrival": transition(db, journey, "arrived", actor, request, "Pacijent stigao")
    if journey.current_stage == "arrived": transition(db, journey, "check_in_review", actor, request, "Započeta prijemna provjera")
    db.flush(); return item

def record_arrival(db: Session, journey: PatientJourney, actor: Actor, request: Request):
    if journey.current_stage != "ready_for_arrival":
        raise HTTPException(409, detail="Dolazak se može evidentirati samo kada tijek pacijenta čeka dolazak")
    now = datetime.now(timezone.utc)
    journey.appointment.arrived_at = journey.appointment.arrived_at or now
    transition(db, journey, "arrived", actor, request, "Pacijent stigao")
    db.flush()
    return journey

def update_item(db: Session, journey: PatientJourney, check_in: JourneyCheckIn, item: JourneyCheckInItem, state: str, note: str | None, actor: Actor, request: Request):
    if item.requires_clinician and state in {"confirmed", "not_applicable"} and "checkin.clinical_review" not in actor.permissions: raise HTTPException(403, detail="Kliničku stavku mora potvrditi ovlašteni liječnik")
    before=item.state; item.state=state; item.note=note; item.updated_by=actor.user_id
    if state in {"blocked", "requires_clinician_review"}:
        open_blocker=db.query(JourneyBlocker).filter_by(journey_id=journey.id, blocker_key=f"checkin:{item.item_key}", status="open").one_or_none()
        if not open_blocker: db.add(JourneyBlocker(journey_id=journey.id, blocker_key=f"checkin:{item.item_key}", category=item.category, title=item.label, details=note, is_clinical=item.requires_clinician, created_by=actor.user_id))
    db.flush(); states=[current.state for current in check_in.items]
    if any(value=="blocked" for value in states): check_in.status="blocked"; journey.check_in_status="blocked"
    elif any(value=="requires_clinician_review" for value in states): check_in.status="in_review"; journey.check_in_status="in_review"
    elif states and all(value in {"confirmed","not_applicable"} for value in states) and not any(blocker.status=="open" for blocker in journey.blockers):
        check_in.status="ready"; check_in.completed_at=datetime.now(timezone.utc); check_in.completed_by=actor.user_id; journey.check_in_status="ready"; transition(db, journey, "ready_for_clinician", actor, request, "Prijemna provjera dovršena")
    else: check_in.status="in_review"; journey.check_in_status="in_review"
    add_event(db, journey, "check_in_item_updated", f"{item.label}: {state}", actor, request, journey.current_stage, journey.current_stage, {"item_id":item.id,"before":before,"after":state})
