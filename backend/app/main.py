from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ai, auth, core, inventory
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models import domain  # noqa: F401
from app.services.seed import seed

settings = get_settings()

app = FastAPI(
    title="ASTRA Clinic Core API",
    description="Modularna API-first platforma za naručivanje, tijek pacijenata, inventar, nabavu i pripremu naplate.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(core.router)
app.include_router(inventory.router)
app.include_router(ai.router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
