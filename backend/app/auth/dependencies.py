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
from app.models.domain import ApiKey, User

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


def require_roles(*role_names: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in role_names:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nemate ovlasti za ovu radnju")
        return user

    return dependency
