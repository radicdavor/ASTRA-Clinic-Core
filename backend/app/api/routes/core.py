from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.domain import Appointment, AuditLog, Module, Patient, Provider, Room, Service, User
from app.schemas.common import AppointmentCreate, AppointmentUpdate, PatientCreate, PatientUpdate, ServiceCreate

router = APIRouter(prefix="/api", tags=["clinic"])


def patch_model(obj, data: dict) -> None:
    for key, value in data.items():
        setattr(obj, key, value)


@router.post("/patients")
def create_patient(payload: PatientCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.flush()
    audit(db, "create", "Patient", patient.id, f"{patient.first_name} {patient.last_name}", user.id)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/patients")
def list_patients(q: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Patient).order_by(Patient.last_name, Patient.first_name)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Patient.phone.ilike(like), Patient.email.ilike(like)))
    return db.scalars(stmt).all()


@router.get("/patients/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, detail="Pacijent nije pronađen")
    return patient


@router.patch("/patients/{patient_id}")
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, detail="Pacijent nije pronađen")
    patch_model(patient, payload.model_dump(exclude_unset=True))
    audit(db, "update", "Patient", patient.id, "Ažuriran pacijent", user.id)
    db.commit()
    db.refresh(patient)
    return patient


@router.post("/appointments")
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointment = Appointment(**payload.model_dump(), created_by=user.id)
    db.add(appointment)
    db.flush()
    audit(db, "create", "Appointment", appointment.id, f"Termin {appointment.date}", user.id)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/appointments")
def list_appointments(
    date_from: date | None = None,
    date_to: date | None = None,
    patient: str | None = None,
    service: str | None = None,
    provider_id: int | None = None,
    room_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
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


@router.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointment = db.scalar(select(Appointment).options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room)).where(Appointment.id == appointment_id))
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    return appointment


@router.patch("/appointments/{appointment_id}")
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    patch_model(appointment, payload.model_dump(exclude_unset=True))
    audit(db, "update", "Appointment", appointment.id, "Ažuriran termin", user.id)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    db.delete(appointment)
    audit(db, "delete", "Appointment", appointment_id, "Obrisan termin", user.id)
    db.commit()
    return {"ok": True}


@router.get("/schedule/day")
def day_schedule(date: date = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(
        select(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.service), joinedload(Appointment.provider), joinedload(Appointment.room))
        .where(Appointment.date == date)
        .order_by(Appointment.start_time)
    ).all()


@router.get("/search")
def search(q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    like = f"%{q}%"
    return {
        "patients": db.scalars(select(Patient).where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like))).limit(10)).all(),
        "services": db.scalars(select(Service).where(Service.name.ilike(like)).limit(10)).all(),
        "appointments": db.scalars(select(Appointment).join(Appointment.patient).join(Appointment.service).where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Service.name.ilike(like), Appointment.status.ilike(like))).limit(10)).all(),
    }


@router.get("/services")
def list_services(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Service).order_by(Service.name)).all()


@router.post("/services")
def create_service(payload: ServiceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = Service(**payload.model_dump())
    db.add(service)
    db.flush()
    audit(db, "create", "Service", service.id, service.name, user.id)
    db.commit()
    db.refresh(service)
    return service


@router.get("/modules")
def list_modules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Module).order_by(Module.name)).all()


@router.get("/providers")
def list_providers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Provider).order_by(Provider.full_name)).all()


@router.get("/rooms")
def list_rooms(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Room).order_by(Room.name)).all()


@router.get("/audit-log")
def audit_log(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)).all()
