from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, ClinicalEpisode, LabOrder, LabResult, LabTemplate, Patient
from app.schemas.laboratory import LabCancel, LabCollection, LabHistoryItem, LabOrderCreate, LabOrderOut, LabResultsUpdate, LabReview, LabTemplateOut

router = APIRouter(prefix="/api/laboratory", tags=["laboratory"])

def query(): return select(LabOrder).options(joinedload(LabOrder.patient), joinedload(LabOrder.results))
def get_order(db: Session, order_id: int):
    order=db.scalar(query().where(LabOrder.id==order_id))
    if not order: raise HTTPException(404, detail="Laboratorijska narudžba nije pronađena")
    return order

@router.get("/templates", response_model=list[LabTemplateOut])
def list_templates(db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.read"))):
    return db.scalars(select(LabTemplate).where(LabTemplate.active.is_(True)).order_by(LabTemplate.condition,LabTemplate.name)).all()

@router.get("/orders", response_model=list[LabOrderOut])
def list_orders(patient_id:int|None=None,status:str|None=None,activity_date:date|None=None,activity:str="ordered",db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.read"))):
    stmt=query().order_by(LabOrder.ordered_at.desc(),LabOrder.id.desc())
    if patient_id: stmt=stmt.where(LabOrder.patient_id==patient_id)
    if status: stmt=stmt.where(LabOrder.status==status)
    if activity_date:
        field=LabOrder.collected_at if activity=="collected" else LabOrder.ordered_at
        stmt=stmt.where(func.date(field)==activity_date)
    return db.scalars(stmt).unique().all()

@router.get("/orders/{order_id}", response_model=LabOrderOut)
def order_detail(order_id:int,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.read"))):
    return get_order(db,order_id)

@router.get("/patients/{patient_id}/history", response_model=list[LabHistoryItem])
def patient_history(patient_id:int,test_name:str,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.read"))):
    if not db.get(Patient,patient_id): raise HTTPException(404,detail="Pacijent nije pronađen")
    rows=db.execute(select(LabOrder.id,LabOrder.ordered_at,LabResult.test_name,LabResult.value,LabResult.text_value,LabResult.unit,LabResult.flag).join(LabResult,LabResult.order_id==LabOrder.id).where(LabOrder.patient_id==patient_id,func.lower(LabResult.test_name)==test_name.lower(),LabOrder.status!="cancelled").order_by(LabOrder.ordered_at.desc())).all()
    return [LabHistoryItem(order_id=row.id,ordered_at=row.ordered_at,test_name=row.test_name,value=row.value,text_value=row.text_value,unit=row.unit,flag=row.flag) for row in rows]

@router.post("/orders", response_model=LabOrderOut)
def create_order(payload:LabOrderCreate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.write"))):
    if not db.get(Patient,payload.patient_id): raise HTTPException(404,detail="Pacijent nije pronađen")
    if payload.episode_id:
        episode=db.get(ClinicalEpisode,payload.episode_id)
        if not episode or episode.patient_id!=payload.patient_id: raise HTTPException(422,detail="Epizoda ne pripada pacijentu")
    if payload.appointment_id:
        appointment=db.get(Appointment,payload.appointment_id)
        if not appointment or appointment.patient_id!=payload.patient_id: raise HTTPException(422,detail="Termin ne pripada pacijentu")
    tests=[test.model_dump() for test in payload.tests]
    if payload.template_id:
        template=db.get(LabTemplate,payload.template_id)
        if not template or not template.active: raise HTTPException(422,detail="Laboratorijski predložak nije dostupan")
        tests=list(template.tests)
    if not tests: raise HTTPException(422,detail="Odaberite predložak ili unesite barem jednu pretragu")
    data=payload.model_dump(exclude={"tests"}); order=LabOrder(**data,created_by=actor.user_id)
    order.results=[LabResult(**test,flag="pending") for test in tests]
    db.add(order); db.flush(); audit(db,"create","LabOrder",order.id,f"Naručene laboratorijske pretrage za pacijenta {payload.patient_id}",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(order),request); db.commit()
    return get_order(db,order.id)

@router.post("/orders/{order_id}/collect", response_model=LabOrderOut)
def collect_sample(order_id:int,payload:LabCollection,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.write"))):
    order=get_order(db,order_id)
    if order.status=="cancelled": raise HTTPException(409,detail="Otkazana narudžba ne može se mijenjati")
    if order.collected_at: raise HTTPException(409,detail="Uzorak je već evidentiran")
    before=snapshot(order);order.specimen_type=payload.specimen_type;order.collected_at=datetime.now(timezone.utc);order.collected_by=actor.user_id;order.status="collected"
    db.flush();audit(db,"sample_collected","LabOrder",order.id,f"Evidentiran uzorak ({payload.specimen_type})",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(order),request);db.commit();return get_order(db,order.id)

@router.put("/orders/{order_id}/results", response_model=LabOrderOut)
def save_results(order_id:int,payload:LabResultsUpdate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.write"))):
    order=get_order(db,order_id)
    if order.status in {"reviewed","cancelled"}: raise HTTPException(409,detail="Zaključani nalaz više se ne može mijenjati")
    by_id={r.id:r for r in order.results}; now=datetime.now(timezone.utc)
    for item in payload.results:
        result=by_id.get(item.id)
        if not result: raise HTTPException(422,detail="Pretraga ne pripada ovoj narudžbi")
        result.value=item.value; result.text_value=item.text_value; result.unit=item.unit; result.reference_low=item.reference_low; result.reference_high=item.reference_high
        result.flag="pending" if item.value is None and not item.text_value else "low" if item.value is not None and result.reference_low is not None and item.value<result.reference_low else "high" if item.value is not None and result.reference_high is not None and item.value>result.reference_high else "normal"
        result.resulted_at=now if result.flag!="pending" else None
    if payload.collected and not order.collected_at: order.collected_at=now
    order.status="resulted" if all(r.flag!="pending" for r in order.results) else "collected" if order.collected_at else "ordered"
    db.flush(); audit(db,"results_update","LabOrder",order.id,"Ažurirani laboratorijski rezultati",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(order),request); db.commit(); return get_order(db,order.id)

@router.post("/orders/{order_id}/review", response_model=LabOrderOut)
def review(order_id:int,payload:LabReview,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.review"))):
    order=get_order(db,order_id)
    if any(r.flag=="pending" for r in order.results): raise HTTPException(422,detail="Svi rezultati moraju biti uneseni prije pregleda")
    order.status="reviewed"; order.review_conclusion=payload.conclusion; order.reviewed_by=actor.user_id; order.reviewed_at=datetime.now(timezone.utc)
    db.flush(); audit(db,"review","LabOrder",order.id,"Liječnik pregledao laboratorijski nalaz",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(order),request); db.commit(); return get_order(db,order.id)

@router.post("/orders/{order_id}/cancel", response_model=LabOrderOut)
def cancel_order(order_id:int,payload:LabCancel,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.write"))):
    order=get_order(db,order_id)
    if order.status=="reviewed": raise HTTPException(409,detail="Pregledani nalaz ne može se otkazati")
    if order.status=="cancelled": raise HTTPException(409,detail="Narudžba je već otkazana")
    before=snapshot(order);order.status="cancelled";order.cancelled_at=datetime.now(timezone.utc);order.cancelled_by=actor.user_id;order.cancellation_reason=payload.reason
    db.flush();audit(db,"cancel","LabOrder",order.id,f"Otkazana laboratorijska narudžba: {payload.reason}",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(order),request);db.commit();return get_order(db,order.id)
