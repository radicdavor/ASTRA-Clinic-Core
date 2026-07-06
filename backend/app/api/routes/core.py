from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.config import get_settings
from app.core.database import get_db
from app.models.domain import ApiKey, Appointment, AuditLog, InventoryBatch, InventoryItem, Invoice, Module, Patient, Provider, Room, Service
from app.schemas.common import AppointmentCreate, AppointmentOut, AppointmentUpdate, ErrorResponse, InvoiceOut, PatientCreate, PatientOut, PatientUpdate, ReadinessCheck, ReadinessOut, ServiceCreate, ServiceOut
from app.services.appointments import validate_appointment_payload

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api", tags=["clinic"], responses=ERROR_RESPONSES)


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


@router.get("/public-config")
def public_config():
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "demo_mode": settings.demo_mode,
        "real_data_allowed": settings.real_data_allowed,
        "fiscalization_mode": settings.fiscalization_mode,
        "warnings": settings.public_warnings,
    }


def scalar_count(db: Session, stmt) -> int:
    return int(db.scalar(stmt) or 0)


@router.get("/readiness", response_model=ReadinessOut)
def readiness(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("audit.read"))):
    settings = get_settings()
    today = date.today()
    critical = "critical"
    warning = "warning"
    ok = "ok"

    patient_count = scalar_count(db, select(func.count(Patient.id)))
    provider_count = scalar_count(db, select(func.count(Provider.id)).where(Provider.active.is_(True)))
    room_count = scalar_count(db, select(func.count(Room.id)).where(Room.active.is_(True)))
    service_count = scalar_count(db, select(func.count(Service.id)).where(Service.active.is_(True)))
    module_count = scalar_count(db, select(func.count(Module.id)).where(Module.enabled.is_(True)))
    audit_count = scalar_count(db, select(func.count(AuditLog.id)))
    active_api_keys = scalar_count(db, select(func.count(ApiKey.id)).where(ApiKey.active.is_(True)))
    low_stock_count = scalar_count(db, select(func.count(InventoryItem.id)).where(InventoryItem.active.is_(True), InventoryItem.current_stock <= InventoryItem.reorder_point))
    expiring_count = scalar_count(db, select(func.count(InventoryBatch.id)).where(InventoryBatch.quantity > 0, InventoryBatch.expiration_date.is_not(None), InventoryBatch.expiration_date <= today + timedelta(days=30)))
    draft_invoice_count = scalar_count(db, select(func.count(Invoice.id)).where(Invoice.status == "draft"))
    unpaid_invoice_count = scalar_count(db, select(func.count(Invoice.id)).where(Invoice.status != "draft", Invoice.payment_status != "paid"))

    checks = [
        ReadinessCheck(
            key="demo_guardrail",
            label="Demo sigurnost",
            status=ok if settings.demo_mode and not settings.real_data_allowed else critical,
            message="Demo nacin je ukljucen i stvarni podaci nisu dopusteni." if settings.demo_mode and not settings.real_data_allowed else "Provjerite postavke demo/real-data zastite prije nastavka.",
            action="Ne unositi stvarne podatke pacijenata dok real-data readiness nije odobren.",
            target_path="/readiness",
            target_label="Otvori spremnost",
        ),
        ReadinessCheck(
            key="fiscalization",
            label="Fiskalizacija",
            status=warning if settings.fiscalization_mode == "noop" else ok,
            message="Aktivna je demo/noop fiskalizacija." if settings.fiscalization_mode == "noop" else "Fiskalizacijski provider nije noop.",
            action="Ne koristiti za stvarnu hrvatsku fiskalizaciju dok provider nije odobren." if settings.fiscalization_mode == "noop" else None,
            target_path="/invoices",
            target_label="Otvori racune",
        ),
        ReadinessCheck(key="patients", label="Pacijenti", status=ok if patient_count > 0 else warning, message="Demo pacijenti su dostupni." if patient_count > 0 else "Nema pacijenata za pilot prolaz.", count=patient_count, target_path="/patients", target_label="Otvori pacijente"),
        ReadinessCheck(key="providers", label="Lijecnici", status=ok if provider_count > 0 else critical, message="Aktivan lijecnik je dostupan." if provider_count > 0 else "Nema aktivnog lijecnika za termine.", count=provider_count, target_path="/appointments/new", target_label="Otvori termin"),
        ReadinessCheck(key="rooms", label="Sobe", status=ok if room_count > 0 else critical, message="Aktivna soba je dostupna." if room_count > 0 else "Nema aktivne sobe za termine.", count=room_count, target_path="/appointments/new", target_label="Otvori termin"),
        ReadinessCheck(key="services", label="Usluge", status=ok if service_count > 0 else critical, message="Aktivne usluge su dostupne." if service_count > 0 else "Nema aktivnih usluga.", count=service_count, target_path="/services", target_label="Otvori usluge"),
        ReadinessCheck(key="modules", label="Moduli", status=ok if module_count > 0 else warning, message="Modularni katalog je inicijaliziran." if module_count > 0 else "Nema aktivnih modula.", count=module_count, target_path="/modules", target_label="Otvori module"),
        ReadinessCheck(key="audit", label="Audit", status=ok if audit_count > 0 else warning, message="Audit log sadrzi zapise." if audit_count > 0 else "Audit log jos nema zapisa.", count=audit_count, target_path="/audit-log", target_label="Otvori audit"),
        ReadinessCheck(key="inventory_low_stock", label="Niska zaliha", status=warning if low_stock_count > 0 else ok, message="Postoje artikli na ili ispod reorder razine." if low_stock_count > 0 else "Nema artikala ispod reorder razine.", count=low_stock_count, action="Provjeriti inventar i nabavu." if low_stock_count > 0 else None, target_path="/inventory", target_label="Otvori inventar"),
        ReadinessCheck(key="inventory_expiring", label="Rokovi zalihe", status=warning if expiring_count > 0 else ok, message="Postoje serije kojima uskoro istjece rok." if expiring_count > 0 else "Nema serija s rokom unutar 30 dana.", count=expiring_count, action="Provjeriti artikle s rokom trajanja." if expiring_count > 0 else None, target_path="/inventory", target_label="Otvori inventar"),
        ReadinessCheck(key="draft_invoices", label="Draft racuni", status=warning if draft_invoice_count > 0 else ok, message="Postoje neizdani draft racuni." if draft_invoice_count > 0 else "Nema neizdanih draft racuna.", count=draft_invoice_count, target_path="/invoices", target_label="Otvori racune"),
        ReadinessCheck(key="unpaid_invoices", label="Neplaceni racuni", status=warning if unpaid_invoice_count > 0 else ok, message="Postoje izdani racuni koji nisu placeni." if unpaid_invoice_count > 0 else "Nema otvorenih uplata.", count=unpaid_invoice_count, target_path="/invoices", target_label="Otvori racune"),
        ReadinessCheck(key="api_keys", label="API kljucevi", status=warning if active_api_keys > 0 else ok, message="Postoje aktivni API kljucevi." if active_api_keys > 0 else "Nema aktivnih API kljuceva.", count=active_api_keys, action="Provjeriti scopeove i deaktivirati nepotrebne kljuceve." if active_api_keys > 0 else None, target_path="/api-keys", target_label="Otvori API kljuceve"),
        ReadinessCheck(
            key="human_pilot_evidence",
            label="Human pilot evidence",
            status=warning,
            message="Provjerite docs/pilot_sessions prije v0.1-pilot taga.",
            action="Azurirati human pilot report, triage, ADR i Go/No-Go matrix.",
            target_path="/readiness",
            target_label="Otvori spremnost",
        ),
    ]

    summary = {
        "ok": sum(1 for check in checks if check.status == ok),
        "warning": sum(1 for check in checks if check.status == warning),
        "critical": sum(1 for check in checks if check.status == critical),
    }
    status = "blocked" if summary["critical"] else "attention_needed" if summary["warning"] else "ready_for_demo"
    return {
        "status": status,
        "demo_mode": settings.demo_mode,
        "real_data_allowed": settings.real_data_allowed,
        "fiscalization_mode": settings.fiscalization_mode,
        "summary": summary,
        "checks": checks,
    }


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
        raise HTTPException(404, detail="Pacijent nije pronađen")
    return patient


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
        raise HTTPException(404, detail="Pacijent nije pronađen")
    before = snapshot(patient)
    patch_model(patient, payload.model_dump(exclude_unset=True))
    flush_or_conflict(db)
    audit(db, "update", "Patient", patient.id, "Ažuriran pacijent", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(patient), request)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient


@router.post("/appointments", response_model=AppointmentOut)
def create_appointment(
    payload: AppointmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    data = payload.model_dump()
    data["duration_minutes"] = validate_appointment_payload(db, payload.date, payload.start_time, payload.end_time, payload.provider_id, payload.room_id, payload.status, payload.source)
    appointment = Appointment(**data, created_by=actor.user_id)
    db.add(appointment)
    db.flush()
    audit(db, "create", "Appointment", appointment.id, f"Termin {appointment.date}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(appointment), request)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(
    date_from: date | None = None,
    date_to: date | None = None,
    patient: str | None = None,
    service: str | None = None,
    provider_id: int | None = None,
    room_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.read")),
):
    stmt = select(Appointment).options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room)).order_by(Appointment.date, Appointment.start_time)
    if date_from:
        stmt = stmt.where(Appointment.date >= date_from)
    if date_to:
        stmt = stmt.where(Appointment.date <= date_to)
    if provider_id:
        stmt = stmt.where(Appointment.provider_id == provider_id)
    if room_id:
        stmt = stmt.where(Appointment.room_id == room_id)
    if status:
        stmt = stmt.where(Appointment.status == status)
    if patient:
        stmt = stmt.join(Appointment.patient).where(or_(Patient.first_name.ilike(f"%{patient}%"), Patient.last_name.ilike(f"%{patient}%")))
    if service:
        stmt = stmt.join(Appointment.service).where(Service.name.ilike(f"%{service}%"))
    return db.scalars(stmt).all()


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    appointment = db.scalar(select(Appointment).options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room)).where(Appointment.id == appointment_id))
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    return appointment


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    before = snapshot(appointment)
    patch_model(appointment, payload.model_dump(exclude_unset=True))
    appointment.duration_minutes = validate_appointment_payload(db, appointment.date, appointment.start_time, appointment.end_time, appointment.provider_id, appointment.room_id, appointment.status, appointment.source, appointment_id=appointment.id)
    db.flush()
    audit(db, "update", "Appointment", appointment.id, "Ažuriran termin", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(appointment), request)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.delete("/appointments/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("appointments.write")),
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    before = snapshot(appointment)
    db.delete(appointment)
    audit(db, "delete", "Appointment", appointment_id, "Obrisan termin", actor.user_id, actor.actor_type, actor.api_key_id, before, None, request)
    db.commit()
    return {"ok": True}


@router.get("/schedule/day", response_model=list[AppointmentOut])
def day_schedule(date: date = Query(...), db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(
        select(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room))
        .where(Appointment.date == date)
        .order_by(Appointment.start_time)
    ).all()


@router.get("/search")
def search(q: str, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("patients.read"))):
    like = f"%{q}%"
    return {
        "patients": db.scalars(select(Patient).where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Patient.oib.ilike(like))).limit(10)).all(),
        "services": db.scalars(select(Service).where(Service.name.ilike(like)).limit(10)).all(),
        "appointments": db.scalars(select(Appointment).join(Appointment.patient).join(Appointment.service).where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Service.name.ilike(like), Appointment.status.ilike(like))).limit(10)).all(),
    }


@router.get("/services", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.read"))):
    return db.scalars(select(Service).order_by(Service.name)).all()


@router.post("/services", response_model=ServiceOut)
def create_service(payload: ServiceCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.write"))):
    service = Service(**payload.model_dump())
    db.add(service)
    db.flush()
    audit(db, "create", "Service", service.id, service.name, actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(service), request)
    db.commit()
    db.refresh(service)
    return service


@router.get("/modules")
def list_modules(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("modules.read"))):
    return db.scalars(select(Module).order_by(Module.name)).all()


@router.get("/providers")
def list_providers(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Provider).order_by(Provider.full_name)).all()


@router.get("/rooms")
def list_rooms(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    return db.scalars(select(Room).order_by(Room.name)).all()


@router.get("/audit-log")
def audit_log(
    entity_type: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    actor_type: str | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_permission("audit.read")),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor_type:
        stmt = stmt.where(AuditLog.actor_type == actor_type)
    return db.scalars(stmt).all()
