from datetime import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Clinic, Module, Provider, Room, Service, room_services
from app.modules.manifest import load_catalog_manifests, validate_module_directory
from pathlib import Path
from app.schemas.common import ClinicCreate, ClinicOut, ErrorResponse, ProviderCreate, ProviderOut, ProviderScheduleUpdate, RoomCreate, RoomOut, ServiceCreate, ServiceOut, ServiceUpdate

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

router = APIRouter(prefix="/api", tags=["catalog"], responses=ERROR_RESPONSES)
MODULE_CATALOG = Path(__file__).resolve().parents[2] / "modules" / "catalog"


def service_out(db: Session, service: Service) -> ServiceOut:
    result = ServiceOut.model_validate(service)
    rows = db.execute(select(Room.id, Room.clinic_id).join(room_services, room_services.c.room_id == Room.id).where(room_services.c.service_id == service.id)).all()
    result.room_ids = [row.id for row in rows]
    result.clinic_ids = list(dict.fromkeys(row.clinic_id for row in rows if row.clinic_id is not None))
    return result


@router.get("/services", response_model=list[ServiceOut])
def list_services(clinic_id: int | None = None, include_hidden: bool = False, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.read"))):
    stmt = select(Service).where(Service.active.is_(True)).order_by(Service.name)
    if not include_hidden:
        stmt = stmt.where(Service.visible_in_catalog.is_(True))
    if clinic_id:
        stmt = stmt.join(room_services, room_services.c.service_id == Service.id).join(Room, Room.id == room_services.c.room_id).where(Room.clinic_id == clinic_id).distinct()
    return [service_out(db, service) for service in db.scalars(stmt).all()]


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
    return service_out(db, service)


@router.post("/services/{service_id}/visibility", response_model=ServiceOut)
def toggle_service_visibility(service_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.write"))):
    service = db.get(Service, service_id)
    if not service or not service.active:
        raise HTTPException(404, detail="Usluga nije pronađena")
    before = snapshot(service)
    service.visible_in_catalog = not service.visible_in_catalog
    db.flush()
    action = "show" if service.visible_in_catalog else "hide"
    audit(db, action, "Service", service.id, f"{'Prikazana' if service.visible_in_catalog else 'Skrivena'} usluga: {service.name}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(service), request)
    db.commit(); db.refresh(service)
    return service_out(db, service)


@router.patch("/services/{service_id}", response_model=ServiceOut)
def update_service(service_id: int, payload: ServiceUpdate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.write"))):
    service = db.get(Service, service_id)
    if not service or not service.active:
        raise HTTPException(404, detail="Usluga nije pronađena")
    before = snapshot(service)
    update_data = payload.model_dump(exclude_unset=True)
    room_ids = update_data.pop("room_ids", None)
    if room_ids is not None:
        rooms = list(db.scalars(select(Room).where(Room.id.in_(room_ids), Room.active.is_(True))).all()) if room_ids else []
        if len(rooms) != len(set(room_ids)):
            raise HTTPException(422, detail="Jedna ili više prostorija nisu pronađene")
        service.allowed_rooms = rooms
    for field, value in update_data.items():
        setattr(service, field, value)
    db.flush()
    audit(db, "update", "Service", service.id, f"Ažurirana usluga: {service.name}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(service), request)
    db.commit(); db.refresh(service)
    return service_out(db, service)


@router.delete("/services/{service_id}", response_model=ServiceOut)
def deactivate_service(service_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.write"))):
    service = db.get(Service, service_id)
    if not service:
        raise HTTPException(404, detail="Usluga nije pronađena")
    if not service.active:
        raise HTTPException(409, detail="Usluga je već deaktivirana")
    before = snapshot(service)
    service.active = False
    db.flush()
    audit(db, "deactivate", "Service", service.id, f"Deaktivirana usluga: {service.name}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(service), request)
    db.commit()
    db.refresh(service)
    return service_out(db, service)


@router.get("/clinics", response_model=list[ClinicOut])
def list_clinics(include_hidden: bool = False, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    stmt = select(Clinic).where(Clinic.active.is_(True)).order_by(Clinic.name)
    if not include_hidden:
        stmt = stmt.where(Clinic.visible_in_catalog.is_(True))
    return db.scalars(stmt).all()


@router.post("/clinics", response_model=ClinicOut)
def create_clinic(payload: ClinicCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    clinic = Clinic(name=payload.name.strip(), timezone=payload.timezone)
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


@router.post("/clinics/{clinic_id}/visibility", response_model=ClinicOut)
def toggle_clinic_visibility(clinic_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    clinic = db.get(Clinic, clinic_id)
    if not clinic or not clinic.active: raise HTTPException(404, detail="Klinika nije pronađena")
    before = snapshot(clinic); clinic.visible_in_catalog = not clinic.visible_in_catalog; db.flush()
    audit(db, "show" if clinic.visible_in_catalog else "hide", "Clinic", clinic.id, f"{'Prikazana' if clinic.visible_in_catalog else 'Skrivena'} klinika: {clinic.name}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(clinic), request)
    db.commit(); db.refresh(clinic); return clinic


@router.delete("/clinics/{clinic_id}", response_model=ClinicOut)
def deactivate_clinic(clinic_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    clinic = db.get(Clinic, clinic_id)
    if not clinic or not clinic.active: raise HTTPException(404, detail="Klinika nije pronađena")
    before = snapshot(clinic); clinic.active = False
    for room in db.scalars(select(Room).where(Room.clinic_id == clinic.id)).all(): room.active = False
    db.flush(); audit(db, "deactivate", "Clinic", clinic.id, f"Deaktivirana klinika: {clinic.name}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(clinic), request)
    db.commit(); db.refresh(clinic); return clinic


@router.get("/modules")
def list_modules(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("modules.read"))):
    return db.scalars(select(Module).order_by(Module.name)).all()


@router.get("/modules/registry")
def module_registry(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("modules.read"))):
    installed = {item.key: item for item in db.scalars(select(Module)).all()}
    result = []
    for directory in sorted(path for path in MODULE_CATALOG.iterdir() if path.is_dir()):
        report = validate_module_directory(directory)
        manifest = report.get("manifest", {"name": directory.name, "display_name": directory.name, "version": "-", "capabilities": []})
        module = installed.get(manifest["name"])
        result.append({**manifest, **report, "installed": module is not None, "enabled": bool(module and module.enabled)})
    return result


@router.post("/modules/{module_key}/validate")
def validate_module(module_key: str, actor: Actor = Depends(require_permission("modules.read"))):
    directory = MODULE_CATALOG / module_key
    if not directory.is_dir() or directory.parent != MODULE_CATALOG:
        raise HTTPException(404, detail="Modul nije pronađen")
    return validate_module_directory(directory)


@router.post("/modules/{module_key}/{action}")
def change_module_status(module_key: str, action: str, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("admin.manage_users"))):
    if action not in {"enable", "disable"}:
        raise HTTPException(404, detail="Nepoznata radnja")
    report = validate_module_directory(MODULE_CATALOG / module_key)
    if action == "enable" and not report["valid"]:
        raise HTTPException(422, detail="Neispravan ili nekompatibilan manifest")
    module = db.scalar(select(Module).where(Module.key == module_key))
    if not module:
        raise HTTPException(404, detail="Modul nije instaliran")
    before = snapshot(module); module.enabled = action == "enable"; db.flush()
    audit(db, action, "Module", module.id, f"Modul {module.name}: {action}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(module), request)
    db.commit(); db.refresh(module); return module


@router.get("/providers", response_model=list[ProviderOut])
def list_providers(include_hidden: bool = False, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    stmt = select(Provider).where(Provider.active.is_(True)).order_by(Provider.full_name)
    if not include_hidden: stmt = stmt.where(Provider.available_for_work.is_(True))
    return db.scalars(stmt).all()


@router.post("/providers", response_model=ProviderOut)
def create_provider(payload: ProviderCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    if not db.get(Clinic, payload.clinic_id):
        raise HTTPException(404, detail="Klinika nije pronađena")
    data = payload.model_dump()
    if data.get("weekly_working_hours") is None:
        start, end = payload.work_start.strftime("%H:%M"), payload.work_end.strftime("%H:%M")
        data["weekly_working_hours"] = {str(day): {"enabled": day < 5, "start": start, "end": end} for day in range(7)}
    provider = Provider(**data, active=True)
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


@router.post("/providers/{provider_id}/availability", response_model=ProviderOut)
def toggle_provider_availability(provider_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    provider = db.get(Provider, provider_id)
    if not provider or not provider.active: raise HTTPException(404, detail="Osoba nije pronađena")
    before = snapshot(provider); provider.available_for_work = not provider.available_for_work; db.flush()
    audit(db, "available" if provider.available_for_work else "unavailable", "Provider", provider.id, f"{provider.full_name}: {'radi' if provider.available_for_work else 'ne radi'}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(provider), request)
    db.commit(); db.refresh(provider); return provider


@router.patch("/providers/{provider_id}/schedule", response_model=ProviderOut)
def update_provider_schedule(provider_id: int, payload: ProviderScheduleUpdate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    provider = db.get(Provider, provider_id)
    if not provider or not provider.active: raise HTTPException(404, detail="Osoba nije pronađena")
    before = snapshot(provider)
    provider.weekly_working_hours = payload.weekly_working_hours
    first_working_day = next((day for day in payload.weekly_working_hours.values() if day["enabled"]), None)
    if first_working_day:
        provider.work_start = time.fromisoformat(first_working_day["start"])
        provider.work_end = time.fromisoformat(first_working_day["end"])
    db.flush(); audit(db, "schedule_update", "Provider", provider.id, f"Ažurirano tjedno radno vrijeme: {provider.full_name}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(provider), request)
    db.commit(); db.refresh(provider); return provider


@router.delete("/providers/{provider_id}", response_model=ProviderOut)
def deactivate_provider(provider_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    provider = db.get(Provider, provider_id)
    if not provider or not provider.active: raise HTTPException(404, detail="Osoba nije pronađena")
    before = snapshot(provider); provider.active = False; provider.available_for_work = False; db.flush()
    audit(db, "deactivate", "Provider", provider.id, f"Deaktivirana osoba: {provider.full_name}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(provider), request)
    db.commit(); db.refresh(provider); return provider


@router.get("/rooms", response_model=list[RoomOut])
def list_rooms(include_hidden: bool = False, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    stmt = select(Room).join(Clinic, Clinic.id == Room.clinic_id, isouter=True).where(Room.active.is_(True)).order_by(Room.name)
    if not include_hidden:
        stmt = stmt.where(Room.visible_in_catalog.is_(True), (Room.clinic_id.is_(None)) | (Clinic.visible_in_catalog.is_(True) & Clinic.active.is_(True)))
    return db.scalars(stmt).all()


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


@router.post("/rooms/{room_id}/visibility", response_model=RoomOut)
def toggle_room_visibility(room_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    room = db.get(Room, room_id)
    if not room or not room.active: raise HTTPException(404, detail="Prostorija nije pronađena")
    before = snapshot(room); room.visible_in_catalog = not room.visible_in_catalog; db.flush()
    audit(db, "show" if room.visible_in_catalog else "hide", "Room", room.id, f"{'Prikazana' if room.visible_in_catalog else 'Skrivena'} prostorija: {room.name}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(room), request)
    db.commit(); db.refresh(room); return room


@router.delete("/rooms/{room_id}", response_model=RoomOut)
def deactivate_room(room_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    room = db.get(Room, room_id)
    if not room or not room.active: raise HTTPException(404, detail="Prostorija nije pronađena")
    before = snapshot(room); room.active = False; db.flush()
    audit(db, "deactivate", "Room", room.id, f"Deaktivirana prostorija: {room.name}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(room), request)
    db.commit(); db.refresh(room); return room
