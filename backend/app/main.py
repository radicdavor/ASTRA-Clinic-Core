from uuid import uuid4
import logging
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ai, appointments, audit, auth, catalog, catalog_governance, clinical_documents, clinical_forms, daily_dashboard, document_ingestion, episodes, intake, inventory, journey_activities, journey_check_in, journey_closure, journey_encounter, journey_preparation, journey_timeline, knowledge, laboratory, pathology, patient_clinical_summary, patient_journeys, patients, readiness, reception, reports, search, system, therapies, workflow
from app.core.config import get_settings
from app.services.schema_readiness import check_configured_database_schema_readiness

logger = logging.getLogger(__name__)

settings = get_settings()
settings.validate_production_safety()

app = FastAPI(
    title="ASTRA Clinic Core API",
    description="Modularna API-first platforma za naručivanje, tijek pacijenata, inventar, nabavu i pripremu naplate.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-ASTRA-API-Key", "X-CSRF-Token", "X-Clinic-Id", "X-Request-ID"],
)

app.include_router(auth.router)
app.include_router(system.router)
app.include_router(clinical_documents.router)
app.include_router(clinical_forms.router)
app.include_router(document_ingestion.router)
app.include_router(patient_clinical_summary.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(reception.router)
app.include_router(episodes.router)
app.include_router(workflow.router)
app.include_router(knowledge.router)
app.include_router(laboratory.router)
app.include_router(pathology.router)
app.include_router(reports.router)
app.include_router(therapies.router)
app.include_router(patient_journeys.router)
app.include_router(journey_activities.router)
app.include_router(intake.router)
app.include_router(journey_preparation.router)
app.include_router(journey_timeline.router)
app.include_router(daily_dashboard.router)
app.include_router(journey_check_in.router)
app.include_router(journey_encounter.router)
app.include_router(journey_closure.router)
app.include_router(catalog.router)
app.include_router(catalog_governance.router)
app.include_router(audit.router)
app.include_router(search.router)
app.include_router(inventory.router)
app.include_router(readiness.router)
app.include_router(ai.router)


def log_schema_readiness() -> None:
    if settings.app_env != "production" and not settings.schema_readiness_check_on_startup:
        logger.info("Database schema readiness check is available at /ready.")
        return
    result = check_configured_database_schema_readiness()
    if result.status == "ready":
        logger.info("Database schema readiness: ready at Alembic revision %s.", result.database_revision)
    else:
        logger.warning(
            "Database schema readiness: %s; database=%s schema=%s expected_revision=%s database_revision=%s.",
            result.status,
            result.checks.get("database"),
            result.checks.get("schema"),
            result.expected_revision,
            result.database_revision,
        )


log_schema_readiness()


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_EXEMPT_PATHS = {"/auth/browser/login", "/auth/login"}


def _origin_allowed(origin: str | None) -> bool:
    if not origin:
        return True
    allowed = set(settings.cors_origin_list)
    if origin in allowed:
        return True
    if settings.cors_origin_regex:
        import re

        return re.match(settings.cors_origin_regex, origin) is not None
    return False


def _same_origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _browser_forbidden(request: Request, detail: str) -> JSONResponse:
    response = JSONResponse(status_code=403, content={"detail": detail})
    origin = request.headers.get("Origin")
    if origin and _origin_allowed(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    )
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


@app.middleware("http")
async def protect_browser_session_mutations(request: Request, call_next):
    if (
        request.method.upper() not in SAFE_METHODS
        and request.url.path not in CSRF_EXEMPT_PATHS
        and settings.session_cookie_name in request.cookies
    ):
        origin = request.headers.get("Origin")
        referer_origin = _same_origin_from_referer(request.headers.get("Referer"))
        if not _origin_allowed(origin) or (referer_origin and not _origin_allowed(referer_origin)):
            return _browser_forbidden(request, "Nedopu?ten origin zahtjeva")
        raw_csrf = request.headers.get("X-CSRF-Token")
        cookie_csrf = request.cookies.get(settings.csrf_cookie_name)
        if not raw_csrf or not cookie_csrf or raw_csrf != cookie_csrf:
            return _browser_forbidden(request, "CSRF provjera nije uspjela")
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-ASTRA-REAL-DATA-ALLOWED"] = str(settings.real_data_allowed).lower()
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/ready")
def ready() -> JSONResponse:
    result = check_configured_database_schema_readiness()
    configuration_errors = settings.production_safety_errors()
    payload = result.to_public_dict()
    payload["checks"]["configuration"] = "invalid" if configuration_errors else "valid"
    payload["configuration_errors"] = configuration_errors
    payload["status"] = "ready" if result.status == "ready" and not configuration_errors else "not_ready"
    status_code = 200 if payload["status"] == "ready" else 503
    return JSONResponse(status_code=status_code, content=payload)
