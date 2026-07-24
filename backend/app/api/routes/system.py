from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import ErrorResponse
from app.services.encounter_diagnosis import diagnosis_suggestions_capability

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api", tags=["system"], responses=ERROR_RESPONSES)


@router.get("/public-config")
def public_config():
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "demo_mode": settings.demo_mode,
        "real_data_allowed": settings.real_data_allowed,
        "demo_persona_switcher_enabled": settings.demo_persona_switcher_available,
        "fiscalization_mode": settings.fiscalization_mode,
        "ai_diagnosis_suggestions": diagnosis_suggestions_capability(settings),
        "warnings": settings.public_warnings,
    }
