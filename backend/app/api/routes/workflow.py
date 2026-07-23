from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, CurrentUserContext, get_scoped_patient, require_active_clinic, require_medical_staff, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, Clinic, Provider, WorkflowChecklistItem, WorkflowTask, WorkflowTemplate
from app.schemas.common import ErrorResponse, WorkflowTaskCreate, WorkflowTaskOut, WorkflowTaskUpdate, WorkflowTemplateCreate, WorkflowTemplateOut
from app.services.clinical_scope import authorized_institution_id, get_institution_episode, provider_belongs_to_institution

router = APIRouter(
    prefix="/api",
    tags=["workflow"],
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    dependencies=[Depends(require_medical_staff)],
)


def task_query(institution_id: int):
    return (
        select(WorkflowTask)
        .options(
            joinedload(WorkflowTask.patient),
            joinedload(WorkflowTask.episode),
            joinedload(WorkflowTask.assignee_provider),
            joinedload(WorkflowTask.checklist),
        )
        .where(WorkflowTask.institution_id == institution_id)
    )


def get_task(db: Session, task_id: int, institution_id: int) -> WorkflowTask:
    task = db.scalar(task_query(institution_id).where(WorkflowTask.id == task_id))
    if not task:
        raise HTTPException(404, detail="Zadatak nije pronaden")
    return task


def validate_links(db: Session, payload: WorkflowTaskCreate, context: CurrentUserContext) -> int:
    get_scoped_patient(db, payload.patient_id, context)
    institution_id = authorized_institution_id(context)
    if payload.episode_id:
        episode = get_institution_episode(db, payload.episode_id, context)
        if episode.patient_id != payload.patient_id:
            raise HTTPException(422, detail="Epizoda mora pripadati odabranom pacijentu")
    if payload.appointment_id:
        appointment = db.scalar(
            select(Appointment)
            .join(Clinic, Clinic.id == Appointment.clinic_id)
            .where(Appointment.id == payload.appointment_id, Clinic.institution_id == institution_id)
        )
        if not appointment or appointment.patient_id != payload.patient_id:
            raise HTTPException(422, detail="Termin mora pripadati pacijentu i ustanovi")
        if payload.episode_id and appointment.episode_id not in {None, payload.episode_id}:
            raise HTTPException(422, detail="Termin pripada drugoj epizodi")
    if payload.assignee_provider_id:
        provider = db.get(Provider, payload.assignee_provider_id)
        if not provider or not provider_belongs_to_institution(db, provider.clinic_id, context):
            raise HTTPException(404, detail="Odgovorna osoba nije pronadena")
    return institution_id


def audit_scope(context: CurrentUserContext, institution_id: int) -> dict:
    return {"scope_type": "clinic", "clinic_id": context.active_clinic_id, "institution_id": institution_id}


@router.get("/workflow-templates", response_model=list[WorkflowTemplateOut])
def list_templates(active: bool | None = True, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("workflow_tasks.read"))):
    stmt = select(WorkflowTemplate).order_by(WorkflowTemplate.name)
    if active is not None:
        stmt = stmt.where(WorkflowTemplate.active.is_(active))
    return db.scalars(stmt).all()


@router.post("/workflow-templates", response_model=WorkflowTemplateOut)
def create_template(payload: WorkflowTemplateCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("workflow_templates.manage"))):
    template = WorkflowTemplate(**payload.model_dump())
    db.add(template)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail="Predlozak s tim kljucem vec postoji") from exc
    audit(db, "create", "WorkflowTemplate", template.id, "Kreiran predlozak radnog toka", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(template), request)
    db.commit()
    db.refresh(template)
    return template


@router.get("/workflow-tasks", response_model=list[WorkflowTaskOut])
def list_tasks(patient_id: int | None = None, episode_id: int | None = None, status: str | None = None, assignee_provider_id: int | None = None, due: str | None = None, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("workflow_tasks.read"))):
    stmt = task_query(authorized_institution_id(context)).order_by(WorkflowTask.due_date.asc().nulls_last(), WorkflowTask.id.desc())
    if patient_id:
        stmt = stmt.where(WorkflowTask.patient_id == patient_id)
    if episode_id:
        stmt = stmt.where(WorkflowTask.episode_id == episode_id)
    if status:
        stmt = stmt.where(WorkflowTask.status == status)
    if assignee_provider_id:
        stmt = stmt.where(WorkflowTask.assignee_provider_id == assignee_provider_id)
    if due == "open":
        stmt = stmt.where(WorkflowTask.status.in_(["open", "in_progress", "waiting"]))
    return db.scalars(stmt).unique().all()


@router.post("/workflow-tasks", response_model=WorkflowTaskOut)
def create_task(payload: WorkflowTaskCreate, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("workflow_tasks.write"))):
    institution_id = validate_links(db, payload, context)
    data = payload.model_dump(exclude={"checklist_items"})
    labels = list(payload.checklist_items)
    if payload.template_id:
        template = db.get(WorkflowTemplate, payload.template_id)
        if not template or not template.active:
            raise HTTPException(422, detail="Predlozak nije aktivan")
        if not labels:
            labels = list(template.checklist_items or [])
        if payload.priority == "routine":
            data["priority"] = template.default_priority
    actor = context.actor
    task = WorkflowTask(**data, institution_id=institution_id, status="open", created_by=actor.user_id)
    task.checklist = [WorkflowChecklistItem(label=label.strip(), position=index) for index, label in enumerate(labels) if label.strip()]
    db.add(task)
    db.flush()
    audit(db, "create", "WorkflowTask", task.id, "Kreiran zadatak", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(task), request, **audit_scope(context, institution_id))
    db.commit()
    return get_task(db, task.id, institution_id)


@router.get("/workflow-tasks/{task_id}", response_model=WorkflowTaskOut)
def task_detail(task_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("workflow_tasks.read"))):
    return get_task(db, task_id, authorized_institution_id(context))


@router.patch("/workflow-tasks/{task_id}", response_model=WorkflowTaskOut)
def update_task(task_id: int, payload: WorkflowTaskUpdate, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("workflow_tasks.write"))):
    institution_id = authorized_institution_id(context)
    task = get_task(db, task_id, institution_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("assignee_provider_id"):
        provider = db.get(Provider, data["assignee_provider_id"])
        if not provider or not provider_belongs_to_institution(db, provider.clinic_id, context):
            raise HTTPException(404, detail="Odgovorna osoba nije pronadena")
    if data.get("status") == "completed" and any(not item.completed for item in task.checklist):
        raise HTTPException(422, detail="Dovrsite checklistu prije zatvaranja zadatka")
    before = snapshot(task)
    for key, value in data.items():
        setattr(task, key, value)
    task.completed_at = datetime.now(timezone.utc) if task.status == "completed" else None
    db.flush()
    actor = context.actor
    audit(db, "complete" if task.status == "completed" else "update", "WorkflowTask", task.id, "Azuriran zadatak", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(task), request, **audit_scope(context, institution_id))
    db.commit()
    return get_task(db, task.id, institution_id)


@router.post("/workflow-tasks/{task_id}/checklist/{item_id}/toggle", response_model=WorkflowTaskOut)
def toggle_checklist(task_id: int, item_id: int, request: Request, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("workflow_tasks.write"))):
    institution_id = authorized_institution_id(context)
    task = get_task(db, task_id, institution_id)
    item = next((entry for entry in task.checklist if entry.id == item_id), None)
    if not item:
        raise HTTPException(404, detail="Stavka checkliste nije pronadena")
    before = snapshot(item)
    item.completed = not item.completed
    item.completed_by = context.actor.user_id if item.completed else None
    item.completed_at = datetime.now(timezone.utc) if item.completed else None
    db.flush()
    actor = context.actor
    audit(db, "checklist_completed" if item.completed else "checklist_reopened", "WorkflowTask", task.id, "Promijenjena checklist stavka", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request, **audit_scope(context, institution_id))
    db.commit()
    return get_task(db, task.id, institution_id)


@router.get("/patients/{patient_id}/workflow-tasks", response_model=list[WorkflowTaskOut])
def patient_tasks(patient_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("workflow_tasks.read"))):
    get_scoped_patient(db, patient_id, context)
    return db.scalars(task_query(authorized_institution_id(context)).where(WorkflowTask.patient_id == patient_id).order_by(WorkflowTask.due_date.asc().nulls_last())).unique().all()


@router.get("/episodes/{episode_id}/workflow-tasks", response_model=list[WorkflowTaskOut])
def episode_tasks(episode_id: int, db: Session = Depends(get_db), context: CurrentUserContext = Depends(require_active_clinic("workflow_tasks.read"))):
    episode = get_institution_episode(db, episode_id, context)
    return db.scalars(task_query(authorized_institution_id(context)).where(WorkflowTask.episode_id == episode.id).order_by(WorkflowTask.due_date.asc().nulls_last())).unique().all()
