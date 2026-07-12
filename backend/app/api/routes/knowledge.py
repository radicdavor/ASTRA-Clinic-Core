from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import KnowledgeProtocol, KnowledgeRule
from app.schemas.common import ErrorResponse, KnowledgeProtocolCreate, KnowledgeProtocolOut

router = APIRouter(prefix="/api", tags=["knowledge"], responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}})

def query(): return select(KnowledgeProtocol).options(joinedload(KnowledgeProtocol.rules))
def get_protocol(db, protocol_id):
    item = db.scalar(query().where(KnowledgeProtocol.id == protocol_id))
    if not item: raise HTTPException(404, detail="Protokol nije pronađen")
    return item

@router.get("/knowledge-protocols", response_model=list[KnowledgeProtocolOut])
def list_protocols(status: str | None = None, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("knowledge_protocols.read"))):
    stmt = query().order_by(KnowledgeProtocol.specialty, KnowledgeProtocol.title)
    if status: stmt = stmt.where(KnowledgeProtocol.status == status)
    return db.scalars(stmt).unique().all()

@router.post("/knowledge-protocols", response_model=KnowledgeProtocolOut)
def create_protocol(payload: KnowledgeProtocolCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("knowledge_protocols.write"))):
    data = payload.model_dump(exclude={"rules"}); item = KnowledgeProtocol(**data, created_by=actor.user_id)
    item.rules = [KnowledgeRule(**rule.model_dump(), position=i) for i, rule in enumerate(payload.rules)]
    db.add(item)
    try: db.flush()
    except IntegrityError as exc: db.rollback(); raise HTTPException(409, detail="Ključ protokola već postoji") from exc
    audit(db, "create", "KnowledgeProtocol", item.id, f"Kreiran draft protokola: {item.title}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(item), request)
    db.commit(); return get_protocol(db, item.id)

@router.get("/knowledge-protocols/{protocol_id}", response_model=KnowledgeProtocolOut)
def protocol_detail(protocol_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("knowledge_protocols.read"))): return get_protocol(db, protocol_id)

@router.post("/knowledge-protocols/{protocol_id}/review", response_model=KnowledgeProtocolOut)
def review_protocol(protocol_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("knowledge_protocols.review"))):
    item = get_protocol(db, protocol_id)
    if not item.source_url.startswith("https://") or not item.rules: raise HTTPException(422, detail="Pregled zahtijeva HTTPS izvor i najmanje jedno pravilo")
    before = snapshot(item); item.status = "reviewed"; item.reviewed_by = actor.user_id; item.reviewed_at = datetime.now(timezone.utc); db.flush()
    audit(db, "review", "KnowledgeProtocol", item.id, f"Liječnik je pregledao protokol: {item.title}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request)
    db.commit(); return get_protocol(db, item.id)

@router.post("/knowledge-protocols/{protocol_id}/archive", response_model=KnowledgeProtocolOut)
def archive_protocol(protocol_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("knowledge_protocols.review"))):
    item = get_protocol(db, protocol_id); before = snapshot(item); item.status = "archived"; db.flush()
    audit(db, "archive", "KnowledgeProtocol", item.id, f"Arhiviran protokol: {item.title}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request); db.commit(); return get_protocol(db, item.id)
