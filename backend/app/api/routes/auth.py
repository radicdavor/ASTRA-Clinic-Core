from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.auth.dependencies import Actor, active_clinic_memberships, get_current_actor, hash_api_key, require_permission
from app.models.domain import ApiKey, User
from app.schemas.common import ApiKeyCreate, ApiKeyCreated, ApiKeyOut, BrowserSessionResponse, ErrorResponse, LoginRequest, TokenResponse
from app.services.sessions import create_user_session, get_valid_session, revoke_all_user_sessions, revoke_session

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/auth", tags=["auth"], responses=ERROR_RESPONSES)

API_KEY_SCOPES = [
    {"name": "ai.patients.create", "category": "AI safe scopes", "description": "AI agent can create patients through the AI endpoint."},
    {"name": "ai.appointments.create", "category": "AI safe scopes", "description": "AI agent can create appointments through the AI endpoint."},
    {"name": "ai.free_slots.read", "category": "AI safe scopes", "description": "AI agent can read today's schedule and free slots."},
    {"name": "patients.read", "category": "Read-only scopes", "description": "Read patient records."},
    {"name": "appointments.read", "category": "Read-only scopes", "description": "Read appointments and schedules."},
    {"name": "clinical_documents.read", "category": "Read-only scopes", "description": "Read reviewed and pending clinical documents."},
    {"name": "inventory.read", "category": "Read-only scopes", "description": "Read inventory state."},
    {"name": "patients.write", "category": "Operational write scopes", "description": "Create and update patients."},
    {"name": "appointments.write", "category": "Operational write scopes", "description": "Create and update appointments."},
    {"name": "clinical_documents.write", "category": "Operational write scopes", "description": "Upload, extract and review clinical documents."},
    {"name": "clinical_documents.review", "category": "Clinical review scopes", "description": "Confirm reviewed clinical documents and patient summaries."},
    {"name": "inventory.adjust", "category": "Dangerous scopes", "description": "Adjust stock quantities."},
    {"name": "inventory.write_off", "category": "Dangerous scopes", "description": "Write off stock."},
    {"name": "billing.mark_paid", "category": "Dangerous scopes", "description": "Mark invoices paid or create payments."},
    {"name": "audit.read", "category": "Dangerous scopes", "description": "Read audit log."},
]


def _cookie_options() -> dict:
    settings = get_settings()
    return {
        "httponly": True,
        "secure": settings.effective_session_cookie_secure,
        "samesite": settings.session_cookie_samesite,
        "path": "/",
        "max_age": settings.browser_session_minutes * 60,
    }


def _csrf_cookie_options() -> dict:
    settings = get_settings()
    return {
        "httponly": False,
        "secure": settings.effective_csrf_cookie_secure,
        "samesite": settings.session_cookie_samesite,
        "path": "/",
        "max_age": settings.browser_session_minutes * 60,
    }


def _delete_cookie_options(httponly: bool) -> dict:
    settings = get_settings()
    return {
        "httponly": httponly,
        "secure": settings.effective_session_cookie_secure if httponly else settings.effective_csrf_cookie_secure,
        "samesite": settings.session_cookie_samesite,
        "path": "/",
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Neispravna e-pošta ili lozinka")
    token = create_access_token(str(user.id), {"role": user.role.name})
    return TokenResponse(access_token=token, user={"id": user.id, "name": user.full_name, "email": user.email, "role": user.role.name})


@router.post("/browser/login", response_model=BrowserSessionResponse)
def browser_login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> BrowserSessionResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Prijava nije uspjela")
    session, raw_session_token, raw_csrf_token = create_user_session(db, user)
    settings = get_settings()
    response.set_cookie(settings.session_cookie_name, raw_session_token, **_cookie_options())
    response.set_cookie(settings.csrf_cookie_name, raw_csrf_token, **_csrf_cookie_options())
    db.commit()
    return BrowserSessionResponse(
        user={"id": user.id, "name": user.full_name, "email": user.email, "role": user.role.name},
        csrf_token=raw_csrf_token,
        expires_at=session.expires_at,
    )


@router.get("/session", response_model=BrowserSessionResponse)
def current_browser_session(
    request: Request,
    db: Session = Depends(get_db),
) -> BrowserSessionResponse:
    settings = get_settings()
    astra_session = request.cookies.get(settings.session_cookie_name)
    astra_csrf = request.cookies.get(settings.csrf_cookie_name)
    session = get_valid_session(db, astra_session)
    if not session:
        raise HTTPException(status_code=401, detail="Prijava je istekla")
    csrf_token = astra_csrf or ""
    return BrowserSessionResponse(
        user={"id": session.user.id, "name": session.user.full_name, "email": session.user.email, "role": session.user.role.name},
        csrf_token=csrf_token,
        expires_at=session.expires_at,
    )


@router.post("/browser/logout")
def browser_logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    settings = get_settings()
    astra_session = request.cookies.get(settings.session_cookie_name)
    session = get_valid_session(db, astra_session, touch=False)
    revoked = revoke_session(db, session)
    response.delete_cookie(settings.session_cookie_name, **_delete_cookie_options(httponly=True))
    response.delete_cookie(settings.csrf_cookie_name, **_delete_cookie_options(httponly=False))
    db.commit()
    return {"logged_out": True, "revoked": revoked}


@router.post("/browser/revoke-all")
def revoke_all_browser_sessions(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("admin.manage_users"))) -> dict[str, int]:
    if actor.actor_type != "user" or actor.user is None:
        raise HTTPException(status_code=403, detail="Opoziv korisniÄŤkih sesija zahtijeva prijavljenog korisnika")
    count = revoke_all_user_sessions(db, actor.user.id)
    db.commit()
    return {"revoked": count}


@router.get("/me/clinics")
def my_clinics(db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    if actor.actor_type != "user" or actor.user is None:
        raise HTTPException(status_code=403, detail="Odabir klinike zahtijeva prijavljenog korisnika")
    memberships = active_clinic_memberships(db, actor.user.id)
    clinics = [{"id": membership.clinic.id, "name": membership.clinic.name, "timezone": membership.clinic.timezone} for membership in memberships]
    return {
        "clinics": clinics,
        "default_clinic_id": clinics[0]["id"] if len(clinics) == 1 else None,
        "requires_selection": len(clinics) > 1,
    }


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
