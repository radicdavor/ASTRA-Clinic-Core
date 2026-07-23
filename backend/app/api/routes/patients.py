from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, CurrentUserContext, get_current_actor, get_scoped_patient, require_active_clinic
from app.core.database import get_db
from app.models.domain import Appointment, ClinicalDocument, ClinicalDocumentAddendum, ClinicalEpisode, ClinicalFinding, ClinicalOpenQuestion, Invoice, Patient, PatientClinicAssociation
from app.schemas.common import ClinicalEpisodeOut, ClinicalEvidenceTimelineListResponse, ClinicalFindingDetailResponse, ClinicalFindingListResponse, ClinicalFindingReadItem, ClinicalOpenQuestionDetailResponse, ClinicalOpenQuestionListResponse, ClinicalOpenQuestionReadItem, ErrorResponse, InvoiceOut, PatientAppointmentAvailabilityOut, PatientClinicalRecordItem, PatientClinicalRecordResponse, PatientCreate, PatientIdentityOut, PatientOut, PatientUpdate
from app.services.clinical_evidence_timeline import list_patient_clinical_evidence_timeline
from app.services.appointments import minimal_appointment_conflict, patient_appointment_availability_stmt
from app.services.clinical_document_access import clinical_document_capabilities, institution_scoped_clinical_record_metadata_statement, resolve_actor_institution_context
from app.services.clinical_scope import authorized_institution_id

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


def clinical_record_item(
    document: ClinicalDocument,
    addendum_count: int,
    actor: Actor,
) -> PatientClinicalRecordItem:
    capabilities = clinical_document_capabilities(actor, document)
    return PatientClinicalRecordItem(
        document_id=document.id,
        patient_id=document.patient_id,
        date=document.document_date,
        created_at=document.created_at,
        clinic_id=document.clinic_id,
        clinic_name=document.clinic.name if document.clinic else None,
        specialty=None,
        document_type=document.document_type,
        title=document.title,
        author=document.author,
        author_professional_role=document.author_professional_role,
        status=document.review_status,
        signed_at=document.reviewed_at if document.review_status == "signed" else None,
        addendum_count=addendum_count,
        can_edit=capabilities.can_edit,
        can_add_addendum=capabilities.can_add_addendum,
    )


def normalize_dt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def patient_stale_detail(patient: Patient) -> dict:
    return {
        "code": "stale_patient",
        "message": "Podaci pacijenta u meduvremenu su promijenjeni. Vas unos nije prepisan.",
        "current_updated_at": patient.updated_at.isoformat() if patient.updated_at else None,
        "server_values": {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "oib": patient.oib,
            "phone": patient.phone,
            "email": patient.email,
            "notes": patient.notes,
        },
    }


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


def open_question_read_item(question: ClinicalOpenQuestion) -> ClinicalOpenQuestionReadItem:
    return ClinicalOpenQuestionReadItem(
        id=question.id,
        question_key=question.question_key,
        patient_id=question.patient_id,
        finding_id=question.finding_id,
        source_type=question.source_type,
        source_label=question.source_label,
        source_reference_summary=question.source_reference,
        label=question.label,
        status=question.status,
        requires_clinician_review=question.requires_clinician_review,
        reviewed_at=question.reviewed_at,
        reviewed_by_user_id=question.reviewed_by_user_id,
        limitations=question.limitations_json or [],
        created_at=question.created_at,
        updated_at=question.updated_at,
    )


def open_question_detail_response(question: ClinicalOpenQuestion) -> ClinicalOpenQuestionDetailResponse:
    return ClinicalOpenQuestionDetailResponse(
        **open_question_read_item(question).model_dump(),
        source_reference=question.source_reference,
        linked_finding_key=question.finding.finding_key if question.finding else None,
        review_note=None,
    )


@router.post("/patients", response_model=PatientOut)
def create_patient(
    payload: PatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("patients.write")),
):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    flush_or_conflict(db)
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=context.active_clinic_id, active=True, created_by_user_id=context.user.id))
    audit(db, "create", "Patient", patient.id, f"{patient.first_name} {patient.last_name}", context.actor.user_id, context.actor.actor_type, context.actor.api_key_id, None, snapshot(patient), request)
    audit(db, "patient_clinic_association_create", "PatientClinicAssociation", None, "Pacijent povezan s aktivnom klinikom", context.actor.user_id, context.actor.actor_type, context.actor.api_key_id, None, {"patient_id": patient.id, "clinic_id": context.active_clinic_id}, request)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient


@router.get("/patients", response_model=list[PatientIdentityOut])
def list_patients(
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=50),
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("patients.read")),
):
    stmt = select(Patient).order_by(Patient.last_name, Patient.first_name, Patient.id).limit(limit)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Patient.phone.ilike(like), Patient.email.ilike(like), Patient.oib.ilike(like)))
    return db.scalars(stmt).all()


@router.get("/patients/possible-duplicates", response_model=list[PatientIdentityOut])
def possible_patient_duplicates(
    first_name: str | None = None,
    last_name: str | None = None,
    date_of_birth: date | None = None,
    phone: str | None = None,
    email: str | None = None,
    oib: str | None = None,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("patients.read")),
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


@router.get("/patients/{patient_id}", response_model=PatientIdentityOut)
def get_patient(patient_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("patients.read"))):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, detail="Pacijent nije pronađen")
    return patient


@router.get("/patients/{patient_id}/clinical-record", response_model=PatientClinicalRecordResponse)
def patient_clinical_record(
    patient_id: int,
    request: Request,
    institution_id: int | None = None,
    document_type: str | None = None,
    clinic_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, detail="Pacijent nije pronađen")
    resolved_institution_id = resolve_actor_institution_context(db, actor, institution_id)
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    stmt = institution_scoped_clinical_record_metadata_statement(db, actor, resolved_institution_id).where(ClinicalDocument.patient_id == patient_id)
    if document_type:
        stmt = stmt.where(ClinicalDocument.document_type == document_type)
    if clinic_id:
        stmt = stmt.where(ClinicalDocument.clinic_id == clinic_id)
    if date_from:
        stmt = stmt.where(or_(ClinicalDocument.document_date >= date_from, ClinicalDocument.document_date.is_(None)))
    if date_to:
        stmt = stmt.where(or_(ClinicalDocument.document_date <= date_to, ClinicalDocument.document_date.is_(None)))
    total = scalar_count(
        db,
        stmt.with_only_columns(func.count(ClinicalDocument.id), maintain_column_froms=True).order_by(None),
    )
    documents = db.scalars(
        stmt.order_by(
            ClinicalDocument.document_date.desc().nulls_last(),
            ClinicalDocument.created_at.desc(),
            ClinicalDocument.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()
    addendum_counts = dict(
        db.execute(
            select(ClinicalDocumentAddendum.original_document_id, func.count(ClinicalDocumentAddendum.id))
            .where(ClinicalDocumentAddendum.original_document_id.in_([item.id for item in documents] or [-1]))
            .group_by(ClinicalDocumentAddendum.original_document_id)
        ).all()
    )
    items = [
        clinical_record_item(document, int(addendum_counts.get(document.id, 0)), actor)
        for document in documents
    ]
    audit(
        db,
        "clinical_history.opened",
        "Patient",
        patient.id,
        "Otvoren je klinički karton ustanove",
        actor.user_id,
        actor.actor_type,
        actor.api_key_id,
        None,
        {"patient_id": patient.id, "institution_id": resolved_institution_id, "count": len(items), "limit": limit, "offset": offset},
        request,
    )
    db.commit()
    return PatientClinicalRecordResponse(patient_id=patient.id, institution_id=resolved_institution_id, count=total, items=items)


@router.get("/patients/{patient_id}/clinical-findings", response_model=ClinicalFindingListResponse)
def patient_clinical_findings(
    patient_id: int,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("clinical_findings.read")),
):
    """Read-only source-linked findings; not diagnosis, treatment, task, outcome evidence or patient messaging."""
    get_scoped_patient(db, patient_id, context)
    institution_id = authorized_institution_id(context)
    findings = db.scalars(
        select(ClinicalFinding)
        .where(
            ClinicalFinding.patient_id == patient_id,
            ClinicalFinding.institution_id == institution_id,
        )
        .order_by(ClinicalFinding.created_at.desc(), ClinicalFinding.id.desc())
    ).all()
    items = [finding_read_item(finding) for finding in findings]
    return ClinicalFindingListResponse(patient_id=patient_id, findings=items, count=len(items))


@router.get("/patients/{patient_id}/clinical-findings/{finding_id}", response_model=ClinicalFindingDetailResponse)
def patient_clinical_finding_detail(
    patient_id: int,
    finding_id: int,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("clinical_findings.read")),
):
    """Read-only source-linked finding detail; not diagnosis, treatment, task, outcome evidence or patient messaging."""
    get_scoped_patient(db, patient_id, context)
    institution_id = authorized_institution_id(context)
    finding = db.scalar(
        select(ClinicalFinding).where(
            ClinicalFinding.id == finding_id,
            ClinicalFinding.patient_id == patient_id,
            ClinicalFinding.institution_id == institution_id,
        )
    )
    if not finding:
        raise HTTPException(404, detail="Finding nije pronaden")
    return ClinicalFindingDetailResponse(**finding_read_item(finding).model_dump())


@router.get("/patients/{patient_id}/clinical-open-questions", response_model=ClinicalOpenQuestionListResponse)
def patient_clinical_open_questions(
    patient_id: int,
    finding_id: int | None = None,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("clinical_open_questions.read")),
):
    """Read-only source-linked open questions; not review, diagnosis, treatment, task, outcome evidence or patient messaging."""
    get_scoped_patient(db, patient_id, context)
    institution_id = authorized_institution_id(context)
    stmt = (
        select(ClinicalOpenQuestion)
        .options(joinedload(ClinicalOpenQuestion.finding))
        .where(
            ClinicalOpenQuestion.patient_id == patient_id,
            ClinicalOpenQuestion.institution_id == institution_id,
        )
        .order_by(ClinicalOpenQuestion.created_at.desc(), ClinicalOpenQuestion.id.desc())
    )
    if finding_id is not None:
        if not db.scalar(
            select(ClinicalFinding.id).where(
                ClinicalFinding.id == finding_id,
                ClinicalFinding.patient_id == patient_id,
                ClinicalFinding.institution_id == institution_id,
            )
        ):
            raise HTTPException(404, detail="Finding nije pronaden za pacijenta")
        stmt = stmt.where(ClinicalOpenQuestion.finding_id == finding_id)
    questions = db.scalars(stmt).all()
    items = [open_question_read_item(question) for question in questions]
    return ClinicalOpenQuestionListResponse(patient_id=patient_id, questions=items, count=len(items))


@router.get("/patients/{patient_id}/clinical-open-questions/{question_id}", response_model=ClinicalOpenQuestionDetailResponse)
def patient_clinical_open_question_detail(
    patient_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("clinical_open_questions.read")),
):
    """Read-only source-linked open question detail; not review, diagnosis, treatment, task, outcome evidence or patient messaging."""
    get_scoped_patient(db, patient_id, context)
    institution_id = authorized_institution_id(context)
    question = db.scalar(
        select(ClinicalOpenQuestion)
        .options(joinedload(ClinicalOpenQuestion.finding))
        .where(
            ClinicalOpenQuestion.id == question_id,
            ClinicalOpenQuestion.patient_id == patient_id,
            ClinicalOpenQuestion.institution_id == institution_id,
        )
    )
    if not question:
        raise HTTPException(404, detail="Open question nije pronaden")
    return open_question_detail_response(question)


@router.get("/patients/{patient_id}/clinical-evidence-timeline", response_model=ClinicalEvidenceTimelineListResponse)
def patient_clinical_evidence_timeline(
    patient_id: int,
    event_type: str | None = None,
    source_type: str | None = None,
    requires_review: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("clinical_evidence_timeline.read")),
):
    """GET-only source-linked clinical evidence timeline; not workflow, decision, task, outcome evidence or messaging."""
    get_scoped_patient(db, patient_id, context)
    institution_id = authorized_institution_id(context)
    events = list_patient_clinical_evidence_timeline(
        db,
        patient_id=patient_id,
        institution_id=institution_id,
        event_type=event_type,
        source_type=source_type,
        requires_review=requires_review,
        date_from=date_from,
        date_to=date_to,
    )
    return ClinicalEvidenceTimelineListResponse(patient_id=patient_id, events=events, count=len(events))


@router.get("/patients/{patient_id}/appointments", response_model=list[PatientAppointmentAvailabilityOut])
def patient_appointments(
    patient_id: int,
    limit: int = Query(default=200, ge=1, le=200),
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("appointments.patient_availability.read")),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    appointments = db.scalars(
        patient_appointment_availability_stmt(patient_id)
        .options(joinedload(Appointment.clinic), joinedload(Appointment.service), joinedload(Appointment.provider))
        .limit(limit)
    ).all()
    return [minimal_appointment_conflict(appointment) for appointment in appointments]


@router.get("/patients/{patient_id}/episodes", response_model=list[ClinicalEpisodeOut])
def patient_episodes(patient_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("episodes.read"))):
    get_scoped_patient(db, patient_id, context)
    stmt = (
        select(ClinicalEpisode)
        .options(joinedload(ClinicalEpisode.patient), joinedload(ClinicalEpisode.owner_provider))
        .where(
            ClinicalEpisode.patient_id == patient_id,
            ClinicalEpisode.institution_id == authorized_institution_id(context),
        )
        .order_by(ClinicalEpisode.status, ClinicalEpisode.start_date.desc())
    )
    return [episode_with_count(db, episode) for episode in db.scalars(stmt).all()]


@router.get("/patients/{patient_id}/invoices", response_model=list[InvoiceOut])
def patient_invoices(
    patient_id: int,
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("billing.read")),
):
    get_scoped_patient(db, patient_id, context)
    return db.scalars(
        select(Invoice)
        .where(Invoice.patient_id == patient_id, Invoice.clinic_id == context.active_clinic_id)
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .limit(limit)
    ).all()


@router.patch("/patients/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    context: CurrentUserContext = Depends(require_active_clinic("patients.write")),
):
    patient = get_scoped_patient(db, patient_id, context)
    actor = context.actor
    before = snapshot(patient)
    updates = payload.model_dump(exclude_unset=True)
    expected_updated_at = updates.pop("expected_updated_at", None)
    if expected_updated_at is not None and normalize_dt(expected_updated_at) != normalize_dt(patient.updated_at):
        raise HTTPException(409, detail=patient_stale_detail(patient))
    if "email" in updates and (updates["email"] or "").lower() != (patient.email or "").lower():
        patient.email_verified_at = None
    patch_model(patient, updates)
    flush_or_conflict(db)
    audit(db, "update", "Patient", patient.id, "Ažuriran pacijent", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(patient), request)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient
