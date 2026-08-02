from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUserContext, patient_ids_in_active_clinic_statement, require_active_clinic
from app.core.database import get_db
from app.models.domain import Appointment, Patient, Provider, Room, Service
from app.schemas.common import ErrorResponse, SearchResponse

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

router = APIRouter(prefix="/api", tags=["search"], responses=ERROR_RESPONSES)


@router.get("/search", response_model=SearchResponse)
def search(q: str, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("patients.read"))):
    like = f"%{q}%"
    patients = db.execute(
        select(
            Patient.id,
            Patient.first_name,
            Patient.last_name,
            Patient.date_of_birth,
            Patient.oib,
            Patient.email,
            Patient.phone,
            Patient.created_at,
            Patient.updated_at,
        )
            .where(
                Patient.id.in_(patient_ids_in_active_clinic_statement(context.active_clinic_id)),
                or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like), Patient.oib.ilike(like)),
            )
            .limit(10)
    ).mappings().all()
    services = db.execute(
        select(
            Service.id,
            Service.name,
            Service.code,
            Service.duration_minutes,
        )
        .where(Service.name.ilike(like))
        .limit(10)
    ).mappings().all()
    appointments = db.execute(
        select(
            Appointment.id,
            Appointment.patient_id,
            Appointment.service_id,
            Appointment.provider_id,
            Appointment.room_id,
            Appointment.clinic_id,
            Appointment.date,
            Appointment.start_time,
            Appointment.end_time,
            Appointment.status,
            (Patient.first_name + " " + Patient.last_name).label("patient_name"),
            Service.name.label("service_name"),
            Provider.full_name.label("provider_name"),
            Room.name.label("room_name"),
        )
        .join(Appointment.patient)
        .join(Appointment.service)
        .join(Appointment.provider)
        .join(Appointment.room)
        .where(
            Appointment.clinic_id == context.active_clinic_id,
            or_(
                Patient.first_name.ilike(like),
                Patient.last_name.ilike(like),
                Service.name.ilike(like),
                Appointment.status.ilike(like),
            ),
        )
        .limit(10)
    ).mappings().all()
    return SearchResponse(
        patients=list(patients),
        services=list(services),
        appointments=list(appointments),
    )
