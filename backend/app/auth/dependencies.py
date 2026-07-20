from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.domain import ApiKey, Clinic, ClinicMembership, Patient, PatientClinicAssociation, PatientJourney, User

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Actor:
    actor_type: str
    user: User | None = None
    api_key: ApiKey | None = None

    @property
    def user_id(self) -> int | None:
        return self.user.id if self.user else None

    @property
    def api_key_id(self) -> int | None:
        return self.api_key.id if self.api_key else None

    @property
    def permissions(self) -> set[str]:
        if self.user:
            return {permission.name for permission in self.user.role.permissions}
        if self.api_key:
            return set(self.api_key.scopes or [])
        return set()


@dataclass(frozen=True)
class CurrentUserContext:
    actor: Actor
    user: User
    permissions: set[str]
    active_clinic: Clinic | None = None

    @property
    def active_clinic_id(self) -> int | None:
        return self.active_clinic.id if self.active_clinic else None

    @property
    def is_system_admin(self) -> bool:
        return "system.admin" in self.permissions


def hash_api_key(raw_key: str) -> str:
    return sha256(raw_key.encode("utf-8")).hexdigest()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nedostaje prijava")
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Neispravan token") from exc
    user = db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Korisnik nije aktivan")
    return user


def get_current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    x_astra_api_key: str | None = Header(default=None, alias="X-ASTRA-API-Key"),
    db: Session = Depends(get_db),
) -> Actor:
    if x_astra_api_key:
        api_key = db.scalar(select(ApiKey).where(ApiKey.key_hash == hash_api_key(x_astra_api_key), ApiKey.active.is_(True)))
        if not api_key or (api_key.expires_at and api_key.expires_at <= datetime.now(UTC)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Neispravan API ključ")
        api_key.last_used_at = datetime.now(UTC)
        db.flush()
        return Actor(actor_type="api_key", api_key=api_key)
    return Actor(actor_type="user", user=get_current_user(credentials, db))


def require_permission(permission_name: str):
    def dependency(actor: Actor = Depends(get_current_actor)) -> Actor:
        if permission_name not in actor.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Nedostaje dozvola: {permission_name}")
        return actor

    return dependency


def active_clinic_memberships(db: Session, user_id: int) -> list[ClinicMembership]:
    return db.scalars(
        select(ClinicMembership)
        .where(ClinicMembership.user_id == user_id, ClinicMembership.active.is_(True))
        .join(Clinic, Clinic.id == ClinicMembership.clinic_id)
        .where(Clinic.active.is_(True))
        .order_by(Clinic.name, Clinic.id)
    ).all()


def require_active_clinic(permission_name: str):
    def dependency(
        actor: Actor = Depends(require_permission(permission_name)),
        x_clinic_id: int | None = Header(default=None, alias="X-Clinic-Id"),
        db: Session = Depends(get_db),
    ) -> CurrentUserContext:
        if actor.actor_type != "user" or actor.user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinic-scoped pristup zahtijeva prijavljenog korisnika")
        memberships = active_clinic_memberships(db, actor.user.id)
        if not memberships:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Korisnik nema aktivno članstvo ni u jednoj klinici")
        if x_clinic_id is None:
            if len(memberships) == 1:
                membership = memberships[0]
            else:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Potreban je odabir aktivne klinike")
        else:
            membership = next((item for item in memberships if item.clinic_id == x_clinic_id), None)
            if membership is None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Korisnik nema pristup odabranoj klinici")
        return CurrentUserContext(
            actor=actor,
            user=actor.user,
            permissions=actor.permissions,
            active_clinic=membership.clinic,
        )

    return dependency


def patient_in_active_clinic_statement(patient_id: int, clinic_id: int):
    return (
        select(Patient)
        .join(PatientClinicAssociation, PatientClinicAssociation.patient_id == Patient.id)
        .where(
            Patient.id == patient_id,
            PatientClinicAssociation.clinic_id == clinic_id,
            PatientClinicAssociation.active.is_(True),
        )
    )


def get_scoped_patient(db: Session, patient_id: int, context: CurrentUserContext) -> Patient:
    if context.active_clinic_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aktivna klinika nije razriješena")
    patient = db.scalar(patient_in_active_clinic_statement(patient_id, context.active_clinic_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pacijent nije pronađen")
    return patient


def get_scoped_journey(db: Session, journey_id: int, context: CurrentUserContext) -> PatientJourney:
    if context.active_clinic_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aktivna klinika nije razriješena")
    journey = db.scalar(select(PatientJourney).where(PatientJourney.id == journey_id, PatientJourney.clinic_id == context.active_clinic_id))
    if journey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tijek pacijenta nije pronađen")
    return journey


def require_roles(*role_names: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in role_names:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nemate ovlasti za ovu radnju")
        return user

    return dependency
