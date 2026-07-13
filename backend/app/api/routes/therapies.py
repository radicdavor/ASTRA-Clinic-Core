from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import ClinicalEpisode, Patient, Therapy
from app.schemas.therapies import TherapyComplete, TherapyCreate, TherapyOut, TherapyRenew, TherapyStop, TherapyUpdate

router = APIRouter(prefix="/api/therapies", tags=["therapies"])

def query(): return select(Therapy).options(joinedload(Therapy.patient))
def get_therapy(db: Session, therapy_id: int):
    item = db.scalar(query().where(Therapy.id == therapy_id))
    if not item: raise HTTPException(404, detail="Terapija nije pronađena")
    return item

@router.get("", response_model=list[TherapyOut])
def list_therapies(patient_id:int|None=None,episode_id:int|None=None,status:str|None=None,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.read"))):
    stmt=query().order_by(Therapy.start_date.desc(),Therapy.id.desc())
    if patient_id: stmt=stmt.where(Therapy.patient_id==patient_id)
    if episode_id: stmt=stmt.where(Therapy.episode_id==episode_id)
    if status: stmt=stmt.where(Therapy.status==status)
    return db.scalars(stmt).unique().all()

@router.post("",response_model=TherapyOut)
def create_therapy(payload:TherapyCreate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.write"))):
    if not db.get(Patient,payload.patient_id): raise HTTPException(404,detail="Pacijent nije pronađen")
    if payload.episode_id:
        episode=db.get(ClinicalEpisode,payload.episode_id)
        if not episode or episode.patient_id!=payload.patient_id: raise HTTPException(422,detail="Epizoda ne pripada pacijentu")
    item=Therapy(**payload.model_dump(),status="active",created_by=actor.user_id);db.add(item);db.flush()
    audit(db,"create","Therapy",item.id,f"Evidentirana terapija {item.name}",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();return get_therapy(db,item.id)

@router.put("/{therapy_id}",response_model=TherapyOut)
def update_therapy(therapy_id:int,payload:TherapyUpdate,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.write"))):
    item=get_therapy(db,therapy_id)
    if item.status!="active": raise HTTPException(409,detail="Samo aktivna terapija može se mijenjati")
    if payload.episode_id:
        episode=db.get(ClinicalEpisode,payload.episode_id)
        if not episode or episode.patient_id!=item.patient_id: raise HTTPException(422,detail="Epizoda ne pripada pacijentu")
    if payload.end_date and payload.end_date<payload.start_date: raise HTTPException(422,detail="Datum završetka ne može biti prije početka")
    before=snapshot(item)
    for key,value in payload.model_dump().items(): setattr(item,key,value)
    item.status="completed" if item.end_date and item.end_date < datetime.now(timezone.utc).date() else "active"
    db.flush();audit(db,"update","Therapy",item.id,f"Ažurirana terapija {item.name}",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(item),request);db.commit();return get_therapy(db,item.id)

@router.post("/{therapy_id}/stop",response_model=TherapyOut)
def stop_therapy(therapy_id:int,payload:TherapyStop,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.write"))):
    item=get_therapy(db,therapy_id)
    if item.status=="stopped": raise HTTPException(409,detail="Terapija je već prekinuta")
    before=snapshot(item);item.status="stopped";item.end_date=datetime.now(timezone.utc).date();item.stopped_at=datetime.now(timezone.utc);item.stopped_by=actor.user_id;item.stop_reason=payload.reason
    db.flush();audit(db,"stop","Therapy",item.id,f"Prekinuta terapija {item.name}: {payload.reason}",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(item),request);db.commit();return get_therapy(db,item.id)

@router.post("/{therapy_id}/complete",response_model=TherapyOut)
def complete_therapy(therapy_id:int,payload:TherapyComplete,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.write"))):
    item=get_therapy(db,therapy_id)
    if item.status!="active": raise HTTPException(409,detail="Samo aktivna terapija može se završiti")
    before=snapshot(item);now=datetime.now(timezone.utc);item.status="completed";item.end_date=now.date();item.completed_at=now;item.completed_by=actor.user_id;item.completion_note=payload.note
    db.flush();audit(db,"complete","Therapy",item.id,f"Završena terapija {item.name}",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(item),request);db.commit();return get_therapy(db,item.id)

@router.post("/{therapy_id}/renew",response_model=TherapyOut)
def renew_therapy(therapy_id:int,payload:TherapyRenew,request:Request,db:Session=Depends(get_db),actor:Actor=Depends(require_permission("clinical_documents.write"))):
    source=get_therapy(db,therapy_id)
    if source.status=="active": raise HTTPException(409,detail="Aktivnu terapiju nije potrebno obnoviti")
    if payload.end_date and payload.end_date<payload.start_date: raise HTTPException(422,detail="Datum završetka ne može biti prije početka")
    item=Therapy(patient_id=source.patient_id,episode_id=source.episode_id,parent_therapy_id=source.id,name=source.name,instructions=payload.instructions or source.instructions,start_date=payload.start_date,end_date=payload.end_date,status="active",prescriber=source.prescriber,notes=source.notes,created_by=actor.user_id)
    db.add(item);db.flush();audit(db,"renew","Therapy",item.id,f"Obnovljena terapija {item.name} iz zapisa {source.id}",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();return get_therapy(db,item.id)
