from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.auth.dependencies import Actor, hash_api_key, require_permission
from app.models.domain import ApiKey, User
from app.schemas.common import ApiKeyCreate, ApiKeyCreated, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Neispravna e-pošta ili lozinka")
    token = create_access_token(str(user.id), {"role": user.role.name})
    return TokenResponse(access_token=token, user={"id": user.id, "name": user.full_name, "email": user.email, "role": user.role.name})


@router.post("/api-keys", response_model=ApiKeyCreated)
def create_api_key(payload: ApiKeyCreate, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("admin.manage_users"))):
    raw_key = "astra_" + token_urlsafe(32)
    api_key = ApiKey(name=payload.name, key_hash=hash_api_key(raw_key), scopes=payload.scopes, expires_at=payload.expires_at, active=True)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return ApiKeyCreated(id=api_key.id, name=api_key.name, scopes=api_key.scopes, active=api_key.active, expires_at=api_key.expires_at, key=raw_key)
