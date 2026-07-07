from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ai, auth, clinical_documents, core, inventory, patient_clinical_summary, patients, readiness, system
from app.core.config import get_settings

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
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(system.router)
app.include_router(clinical_documents.router)
app.include_router(patient_clinical_summary.router)
app.include_router(patients.router)
app.include_router(core.router)
app.include_router(inventory.router)
app.include_router(readiness.router)
app.include_router(ai.router)


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
