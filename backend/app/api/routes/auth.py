from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.auth.dependencies import Actor, hash_api_key, require_permission
from app.models.domain import ApiKey, User
from app.schemas.common import ApiKeyCreate, ApiKeyCreated, ApiKeyOut, ErrorResponse, LoginRequest, TokenResponse

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/auth", tags=["auth"], responses=ERROR_RESPONSES)

API_KEY_SCOPES = [
    {"name": "ai.patients.create", "category": "AI safe scopes", "description": "AI agent can create patients through the AI endpoint."},
    {"name": "ai.appointments.create", "category": "AI safe scopes", "description": "AI agent can create appointments through the AI endpoint."},
    {"name": "ai.free_slots.read", "category": "AI safe scopes", "description": "AI agent can read today's schedule and free slots."},
    {"name": "patients.read", "category": "Read-only scopes", "description": "Read patient records."},
    {"name": "appointments.read", "category": "Read-only scopes", "description": "Read appointments and schedules."},
    {"name": "inventory.read", "category": "Read-only scopes", "description": "Read inventory state."},
    {"name": "patients.write", "category": "Operational write scopes", "description": "Create and update patients."},
    {"name": "appointments.write", "category": "Operational write scopes", "description": "Create and update appointments."},
    {"name": "inventory.adjust", "category": "Dangerous scopes", "description": "Adjust stock quantities."},
    {"name": "inventory.write_off", "category": "Dangerous scopes", "description": "Write off stock."},
    {"name": "billing.mark_paid", "category": "Dangerous scopes", "description": "Mark invoices paid or create payments."},
    {"name": "audit.read", "category": "Dangerous scopes", "description": "Read audit log."},
]


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


@router.get("/api-key-scopes")
def api_key_scopes(actor: Actor = Depends(require_permission("admin.manage_users"))):
    return API_KEY_SCOPES


@router.get("/api-keys", response_model=list[ApiKeyOut])
def list_api_keys(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("admin.manage_users"))):
    return db.scalars(select(ApiKey).order_by(ApiKey.created_at.desc())).all()


@router.patch("/api-keys/{api_key_id}/deactivate", response_model=ApiKeyOut)
def deactivate_api_key(api_key_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("admin.manage_users"))):
    api_key = db.get(ApiKey, api_key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API kljuc nije pronaden")
    api_key.active = False
    db.commit()
    db.refresh(api_key)
    return api_key
