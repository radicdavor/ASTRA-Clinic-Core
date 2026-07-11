from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Clinic, Module, Provider, Room, Service
from app.schemas.common import ClinicCreate, ClinicOut, ErrorResponse, ProviderCreate, ProviderOut, RoomCreate, RoomOut, ServiceCreate, ServiceOut

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

router = APIRouter(prefix="/api", tags=["catalog"], responses=ERROR_RESPONSES)


@router.get("/services", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.read"))):
    return db.scalars(select(Service).order_by(Service.name)).all()


@router.post("/services", response_model=ServiceOut)
def create_service(
    payload: ServiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("services.write")),
):
    service = Service(**payload.model_dump())
    db.add(service)
    db.flush()
    audit(db, "create", "Service", service.id, service.name, actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(service), request)
    db.commit()
    db.refresh(service)
    return service


@router.get("/clinics", response_model=list[ClinicOut])
def list_clinics(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Clinic).where(Clinic.active.is_(True)).order_by(Clinic.name)).all()


@router.post("/clinics", response_model=ClinicOut)
def create_clinic(payload: ClinicCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    clinic = Clinic(name=payload.name.strip())
    db.add(clinic)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail="Klinika s tim nazivom već postoji") from exc
    audit(db, "create", "Clinic", clinic.id, clinic.name, actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(clinic), request)
    db.commit()
    db.refresh(clinic)
    return clinic


@router.get("/modules")
def list_modules(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("modules.read"))):
    return db.scalars(select(Module).order_by(Module.name)).all()


@router.get("/providers", response_model=list[ProviderOut])
def list_providers(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Provider).order_by(Provider.full_name)).all()


@router.post("/providers", response_model=ProviderOut)
def create_provider(payload: ProviderCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    if not db.get(Clinic, payload.clinic_id):
        raise HTTPException(404, detail="Klinika nije pronađena")
    provider = Provider(**payload.model_dump(), staff_role="physician", active=True)
    db.add(provider)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail="Liječnik s tim e-mailom već postoji") from exc
    audit(db, "create", "Provider", provider.id, provider.full_name, actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(provider), request)
    db.commit()
    db.refresh(provider)
    return provider


@router.get("/rooms", response_model=list[RoomOut])
def list_rooms(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Room).order_by(Room.name)).all()


@router.post("/rooms", response_model=RoomOut)
def create_room(payload: RoomCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    if not db.get(Clinic, payload.clinic_id):
        raise HTTPException(404, detail="Klinika nije pronađena")
    room = Room(**payload.model_dump(), active=True)
    db.add(room)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail="Prostorija s tim nazivom već postoji") from exc
    audit(db, "create", "Room", room.id, room.name, actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(room), request)
    db.commit()
    db.refresh(room)
    return room
