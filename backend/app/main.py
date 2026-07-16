from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ai, appointments, audit, auth, catalog, clinical_documents, clinical_forms, daily_dashboard, document_ingestion, episodes, intake, inventory, journey_activities, journey_check_in, journey_closure, journey_encounter, journey_preparation, journey_timeline, knowledge, laboratory, pathology, patient_clinical_summary, patient_journeys, patients, readiness, reception, reports, search, system, therapies, workflow
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
app.include_router(audit.router)
app.include_router(search.router)
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
