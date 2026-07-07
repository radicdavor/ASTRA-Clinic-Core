from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.schemas.common import ErrorResponse, ReadinessOut
from app.services.readiness import build_operational_readiness

ERROR_RESPONSES = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

router = APIRouter(prefix="/api", tags=["readiness"], responses=ERROR_RESPONSES)


@router.get("/readiness", response_model=ReadinessOut)
def readiness(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("audit.read"))):
    return build_operational_readiness(db)
