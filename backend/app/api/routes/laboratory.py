from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, CurrentUserContext, get_scoped_patient, require_active_clinic, require_medical_staff, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, Clinic, LabOrder, LabResult, LabTemplate
from app.schemas.laboratory import LabCancel, LabCollection, LabHistoryItem, LabOrderCreate, LabOrderOut, LabResultsUpdate, LabReview, LabTemplateOut
from app.services.clinical_scope import authorized_institution_id, get_institution_episode

router = APIRouter(prefix="/api/laboratory", tags=["laboratory"], dependencies=[Depends(require_medical_staff)])


def order_query(institution_id: int):
    return select(LabOrder).options(joinedload(LabOrder.patient), joinedload(LabOrder.results)).where(LabOrder.institution_id == institution_id)


def get_order(db: Session, order_id: int, institution_id: int) -> LabOrder:
    order = db.scalar(order_query(institution_id).where(LabOrder.id == order_id))
    if not order:
        raise HTTPException(404, detail="Laboratorijska narudzba nije pronadena")
    return order


def audit_scope(context: CurrentUserContext, institution_id: int) -> dict:
    return {"scope_type": "clinic", "clinic_id": context.active_clinic_id, "institution_id": institution_id}


@router.get("/templates", response_model=list[LabTemplateOut])
def list_templates(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_documents.read"))):
    return db.scalars(select(LabTemplate).where(LabTemplate.active.is_(True)).order_by(LabTemplate.condition, LabTemplate.name)).all()


@router.get("/orders", response_model=list[LabOrderOut])
def list_orders(patient_id: int | None = None, status: str | None = None, activity_date: date | None = None, activity: str = "ordered", db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.read"))):
    stmt = order_query(authorized_institution_id(context)).order_by(LabOrder.ordered_at.desc(), LabOrder.id.desc())
    if patient_id:
        stmt = stmt.where(LabOrder.patient_id == patient_id)
    if status:
        stmt = stmt.where(LabOrder.status == status)
    if activity_date:
        field = LabOrder.collected_at if activity == "collected" else LabOrder.ordered_at
        stmt = stmt.where(func.date(field) == activity_date)
    return db.scalars(stmt).unique().all()


@router.get("/orders/{order_id}", response_model=LabOrderOut)
def order_detail(order_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.read"))):
    return get_order(db, order_id, authorized_institution_id(context))


@router.get("/patients/{patient_id}/history", response_model=list[LabHistoryItem])
def patient_history(patient_id: int, test_name: str, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.read"))):
    get_scoped_patient(db, patient_id, context)
    rows = db.execute(
        select(LabOrder.id, LabOrder.ordered_at, LabResult.test_name, LabResult.value, LabResult.text_value, LabResult.unit, LabResult.flag)
        .join(LabResult, LabResult.order_id == LabOrder.id)
        .where(
            LabOrder.patient_id == patient_id,
            LabOrder.institution_id == authorized_institution_id(context),
            func.lower(LabResult.test_name) == test_name.lower(),
            LabOrder.status != "cancelled",
        )
        .order_by(LabOrder.ordered_at.desc())
    ).all()
    return [LabHistoryItem(order_id=row.id, ordered_at=row.ordered_at, test_name=row.test_name, value=row.value, text_value=row.text_value, unit=row.unit, flag=row.flag) for row in rows]


@router.post("/orders", response_model=LabOrderOut)
def create_order(payload: LabOrderCreate, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.write"))):
    get_scoped_patient(db, payload.patient_id, context)
    institution_id = authorized_institution_id(context)
    if payload.episode_id:
        episode = get_institution_episode(db, payload.episode_id, context)
        if episode.patient_id != payload.patient_id:
            raise HTTPException(422, detail="Epizoda ne pripada pacijentu")
    if payload.appointment_id:
        appointment = db.scalar(
            select(Appointment)
            .join(Clinic, Clinic.id == Appointment.clinic_id)
            .where(Appointment.id == payload.appointment_id, Clinic.institution_id == institution_id)
        )
        if not appointment or appointment.patient_id != payload.patient_id:
            raise HTTPException(422, detail="Termin ne pripada pacijentu ili ustanovi")
    tests = [test.model_dump() for test in payload.tests]
    if payload.template_id:
        template = db.get(LabTemplate, payload.template_id)
        if not template or not template.active:
            raise HTTPException(422, detail="Laboratorijski predlozak nije dostupan")
        tests = list(template.tests)
    if not tests:
        raise HTTPException(422, detail="Odaberite predlozak ili unesite barem jednu pretragu")
    data = payload.model_dump(exclude={"tests"})
    actor = context.actor
    order = LabOrder(**data, institution_id=institution_id, created_by=actor.user_id)
    order.results = [LabResult(**test, flag="pending") for test in tests]
    db.add(order)
    db.flush()
    audit(db, "create", "LabOrder", order.id, "Narucene laboratorijske pretrage", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(order), request, **audit_scope(context, institution_id))
    db.commit()
    return get_order(db, order.id, institution_id)


@router.post("/orders/{order_id}/collect", response_model=LabOrderOut)
def collect_sample(order_id: int, payload: LabCollection, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.write"))):
    institution_id = authorized_institution_id(context)
    order = get_order(db, order_id, institution_id)
    if order.status == "cancelled":
        raise HTTPException(409, detail="Otkazana narudzba ne moze se mijenjati")
    if order.collected_at:
        raise HTTPException(409, detail="Uzorak je vec evidentiran")
    before = snapshot(order)
    order.specimen_type = payload.specimen_type
    order.collected_at = datetime.now(timezone.utc)
    order.collected_by = context.actor.user_id
    order.status = "collected"
    db.flush()
    actor = context.actor
    audit(db, "sample_collected", "LabOrder", order.id, "Evidentiran uzorak", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(order), request, **audit_scope(context, institution_id))
    db.commit()
    return get_order(db, order.id, institution_id)


@router.put("/orders/{order_id}/results", response_model=LabOrderOut)
def save_results(order_id: int, payload: LabResultsUpdate, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.write"))):
    institution_id = authorized_institution_id(context)
    order = get_order(db, order_id, institution_id)
    if order.status in {"reviewed", "cancelled"}:
        raise HTTPException(409, detail="Zakljucani nalaz vise se ne moze mijenjati")
    by_id = {result.id: result for result in order.results}
    now = datetime.now(timezone.utc)
    for item in payload.results:
        result = by_id.get(item.id)
        if not result:
            raise HTTPException(422, detail="Pretraga ne pripada ovoj narudzbi")
        result.value, result.text_value, result.unit = item.value, item.text_value, item.unit
        result.reference_low, result.reference_high = item.reference_low, item.reference_high
        result.flag = "pending" if item.value is None and not item.text_value else "low" if item.value is not None and result.reference_low is not None and item.value < result.reference_low else "high" if item.value is not None and result.reference_high is not None and item.value > result.reference_high else "normal"
        result.resulted_at = now if result.flag != "pending" else None
    if payload.collected and not order.collected_at:
        order.collected_at = now
    order.status = "resulted" if all(result.flag != "pending" for result in order.results) else "collected" if order.collected_at else "ordered"
    db.flush()
    actor = context.actor
    audit(db, "results_update", "LabOrder", order.id, "Azurirani laboratorijski rezultati", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(order), request, **audit_scope(context, institution_id))
    db.commit()
    return get_order(db, order.id, institution_id)


@router.post("/orders/{order_id}/review", response_model=LabOrderOut)
def review(order_id: int, payload: LabReview, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.review"))):
    institution_id = authorized_institution_id(context)
    order = get_order(db, order_id, institution_id)
    if any(result.flag == "pending" for result in order.results):
        raise HTTPException(422, detail="Svi rezultati moraju biti uneseni prije pregleda")
    order.status = "reviewed"
    order.review_conclusion = payload.conclusion
    order.reviewed_by = context.actor.user_id
    order.reviewed_at = datetime.now(timezone.utc)
    db.flush()
    actor = context.actor
    audit(db, "review", "LabOrder", order.id, "Lijecnik pregledao laboratorijski nalaz", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(order), request, **audit_scope(context, institution_id))
    db.commit()
    return get_order(db, order.id, institution_id)


@router.post("/orders/{order_id}/cancel", response_model=LabOrderOut)
def cancel_order(order_id: int, payload: LabCancel, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("clinical_documents.write"))):
    institution_id = authorized_institution_id(context)
    order = get_order(db, order_id, institution_id)
    if order.status == "reviewed":
        raise HTTPException(409, detail="Pregledani nalaz ne moze se otkazati")
    if order.status == "cancelled":
        raise HTTPException(409, detail="Narudzba je vec otkazana")
    before = snapshot(order)
    order.status = "cancelled"
    order.cancelled_at = datetime.now(timezone.utc)
    order.cancelled_by = context.actor.user_id
    order.cancellation_reason = payload.reason
    db.flush()
    actor = context.actor
    audit(db, "cancel", "LabOrder", order.id, "Otkazana laboratorijska narudzba", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(order), request, **audit_scope(context, institution_id))
    db.commit()
    return get_order(db, order.id, institution_id)
