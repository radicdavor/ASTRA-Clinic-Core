from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, get_current_actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, ClinicalEpisode, ClinicalFinding, Invoice, Patient
from app.schemas.common import AppointmentOut, ClinicalEpisodeOut, ClinicalFindingDetailResponse, ClinicalFindingListResponse, ClinicalFindingReadItem, ErrorResponse, InvoiceOut, PatientCreate, PatientOut, PatientUpdate

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api", tags=["patients"], responses=ERROR_RESPONSES)


def patch_model(obj, data: dict) -> None:
    for key, value in data.items():
        setattr(obj, key, value)


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail="Zapis s istim jedinstvenim identifikatorom vec postoji") from exc


def flush_or_conflict(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail="Zapis s istim jedinstvenim identifikatorom vec postoji") from exc


def scalar_count(db: Session, stmt) -> int:
    return int(db.scalar(stmt) or 0)


def episode_with_count(db: Session, episode: ClinicalEpisode) -> ClinicalEpisodeOut:
    data = ClinicalEpisodeOut.model_validate(episode)
    data.appointment_count = scalar_count(db, select(func.count(Appointment.id)).where(Appointment.episode_id == episode.id))
    return data


def finding_read_item(finding: ClinicalFinding) -> ClinicalFindingReadItem:
    return ClinicalFindingReadItem(
        id=finding.id,
        finding_key=finding.finding_key,
        patient_id=finding.patient_id,
        source_type=finding.source_type,
        source_label=finding.source_label,
        source_reference=finding.source_reference,
        source_document_id=finding.source_document_id,
        label=finding.label,
        category=finding.category,
        lifecycle_status=finding.lifecycle_status,
        requires_review=finding.requires_review,
        reviewed_at=finding.reviewed_at,
        reviewed_by_user_id=finding.reviewed_by_user_id,
        limitations=finding.limitations_json or [],
        schema_version=finding.schema_version,
        created_at=finding.created_at,
        updated_at=finding.updated_at,
    )


def require_findings_read_user(actor: Actor) -> Actor:
    if actor.actor_type != "user" or actor.user_id is None:
        raise HTTPException(403, detail="Findings read zahtijeva prijavljenog korisnika")
    if "clinical_findings.read" not in actor.permissions:
        raise HTTPException(403, detail="Nedostaje dozvola: clinical_findings.read")
    return actor


@router.post("/patients", response_model=PatientOut)
def create_patient(
    payload: PatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("patients.write")),
):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    flush_or_conflict(db)
    audit(db, "create", "Patient", patient.id, f"{patient.first_name} {patient.last_name}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(patient), request)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient


@router.get("/patients", response_model=list[PatientOut])
def list_patients(q: str | None = None, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("patients.read"))):
    stmt = select(Patient).order_by(Patient.last_name, Patient.first_name)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Patient.phone.ilike(like), Patient.email.ilike(like), Patient.oib.ilike(like)))
    return db.scalars(stmt).all()


@router.get("/patients/possible-duplicates", response_model=list[PatientOut])
def possible_patient_duplicates(
    first_name: str | None = None,
    last_name: str | None = None,
    date_of_birth: date | None = None,
    phone: str | None = None,
    email: str | None = None,
    oib: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("patients.read")),
):
    conditions = []
    if oib:
        conditions.append(Patient.oib == oib.strip())
    if first_name and last_name:
        name_match = [Patient.first_name.ilike(first_name.strip()), Patient.last_name.ilike(last_name.strip())]
        if date_of_birth:
            conditions.append(and_(*name_match, Patient.date_of_birth == date_of_birth))
        if phone:
            conditions.append(and_(*name_match, Patient.phone == phone.strip()))
        if email:
            conditions.append(and_(*name_match, Patient.email == email.strip()))
        if not date_of_birth and not phone and not email:
            conditions.append(and_(*name_match))
    if not conditions:
        return []
    stmt = select(Patient).where(or_(*conditions)).order_by(Patient.last_name, Patient.first_name).limit(10)
    return db.scalars(stmt).all()


@router.get("/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("patients.read"))):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, detail="Pacijent nije pronaÄ‘en")
    return patient


@router.get("/patients/{patient_id}/clinical-findings", response_model=ClinicalFindingListResponse)
def patient_clinical_findings(
    patient_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """Read-only source-linked findings; not diagnosis, treatment, task, outcome evidence or patient messaging."""
    require_findings_read_user(actor)
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    findings = db.scalars(
        select(ClinicalFinding)
        .where(ClinicalFinding.patient_id == patient_id)
        .order_by(ClinicalFinding.created_at.desc(), ClinicalFinding.id.desc())
    ).all()
    items = [finding_read_item(finding) for finding in findings]
    return ClinicalFindingListResponse(patient_id=patient_id, findings=items, count=len(items))


@router.get("/patients/{patient_id}/clinical-findings/{finding_id}", response_model=ClinicalFindingDetailResponse)
def patient_clinical_finding_detail(
    patient_id: int,
    finding_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """Read-only source-linked finding detail; not diagnosis, treatment, task, outcome evidence or patient messaging."""
    require_findings_read_user(actor)
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    finding = db.scalar(
        select(ClinicalFinding).where(
            ClinicalFinding.id == finding_id,
            ClinicalFinding.patient_id == patient_id,
        )
    )
    if not finding:
        raise HTTPException(404, detail="Finding nije pronaden")
    return ClinicalFindingDetailResponse(**finding_read_item(finding).model_dump())


@router.get("/patients/{patient_id}/appointments", response_model=list[AppointmentOut])
def patient_appointments(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    return db.scalars(
        select(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room))
        .where(Appointment.patient_id == patient_id)
        .order_by(Appointment.date.desc(), Appointment.start_time.desc())
    ).all()


@router.get("/patients/{patient_id}/episodes", response_model=list[ClinicalEpisodeOut])
def patient_episodes(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("episodes.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    stmt = (
        select(ClinicalEpisode)
        .options(joinedload(ClinicalEpisode.patient), joinedload(ClinicalEpisode.owner_provider))
        .where(ClinicalEpisode.patient_id == patient_id)
        .order_by(ClinicalEpisode.status, ClinicalEpisode.start_date.desc())
    )
    return [episode_with_count(db, episode) for episode in db.scalars(stmt).all()]


@router.get("/patients/{patient_id}/invoices", response_model=list[InvoiceOut])
def patient_invoices(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    return db.scalars(select(Invoice).where(Invoice.patient_id == patient_id).order_by(Invoice.invoice_date.desc(), Invoice.id.desc())).all()


@router.patch("/patients/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("patients.write")),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, detail="Pacijent nije pronaÄ‘en")
    before = snapshot(patient)
    patch_model(patient, payload.model_dump(exclude_unset=True))
    flush_or_conflict(db)
    audit(db, "update", "Patient", patient.id, "AĹľuriran pacijent", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(patient), request)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient
