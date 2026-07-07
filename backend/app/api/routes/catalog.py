from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Clinic, Module, Provider, Room, Service
from app.schemas.common import ClinicOut, ErrorResponse, ServiceCreate, ServiceOut

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


@router.get("/modules")
def list_modules(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("modules.read"))):
    return db.scalars(select(Module).order_by(Module.name)).all()


@router.get("/providers")
def list_providers(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Provider).order_by(Provider.full_name)).all()


@router.get("/rooms")
def list_rooms(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Room).order_by(Room.name)).all()
