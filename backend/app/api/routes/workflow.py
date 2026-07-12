from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import Appointment, ClinicalEpisode, Patient, Provider, WorkflowChecklistItem, WorkflowTask, WorkflowTemplate
from app.schemas.common import ErrorResponse, WorkflowTaskCreate, WorkflowTaskOut, WorkflowTaskUpdate, WorkflowTemplateCreate, WorkflowTemplateOut

router = APIRouter(prefix="/api", tags=["workflow"], responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}})


def task_query():
    return select(WorkflowTask).options(
        joinedload(WorkflowTask.patient),
        joinedload(WorkflowTask.episode),
        joinedload(WorkflowTask.assignee_provider),
        joinedload(WorkflowTask.checklist),
    )


def get_task(db: Session, task_id: int) -> WorkflowTask:
    task = db.scalar(task_query().where(WorkflowTask.id == task_id))
    if not task:
        raise HTTPException(404, detail="Zadatak nije pronaden")
    return task


def validate_links(db: Session, payload: WorkflowTaskCreate) -> None:
    if not db.get(Patient, payload.patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    if payload.episode_id:
        episode = db.get(ClinicalEpisode, payload.episode_id)
        if not episode or episode.patient_id != payload.patient_id:
            raise HTTPException(422, detail="Epizoda mora pripadati odabranom pacijentu")
    if payload.appointment_id:
        appointment = db.get(Appointment, payload.appointment_id)
        if not appointment or appointment.patient_id != payload.patient_id:
            raise HTTPException(422, detail="Termin mora pripadati odabranom pacijentu")
        if payload.episode_id and appointment.episode_id not in {None, payload.episode_id}:
            raise HTTPException(422, detail="Termin pripada drugoj epizodi")
    if payload.assignee_provider_id and not db.get(Provider, payload.assignee_provider_id):
        raise HTTPException(404, detail="Odgovorna osoba nije pronadena")


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
    audit(db, "create", "WorkflowTemplate", template.id, f"Kreiran predlozak radnog toka: {template.name}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(template), request)
    db.commit()
    db.refresh(template)
    return template


@router.get("/workflow-tasks", response_model=list[WorkflowTaskOut])
def list_tasks(patient_id: int | None = None, episode_id: int | None = None, status: str | None = None, assignee_provider_id: int | None = None, due: str | None = None, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("workflow_tasks.read"))):
    stmt = task_query().order_by(WorkflowTask.due_date.asc().nulls_last(), WorkflowTask.id.desc())
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
def create_task(payload: WorkflowTaskCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("workflow_tasks.write"))):
    validate_links(db, payload)
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
    task = WorkflowTask(**data, status="open", created_by=actor.user_id)
    task.checklist = [WorkflowChecklistItem(label=label.strip(), position=index) for index, label in enumerate(labels) if label.strip()]
    db.add(task)
    db.flush()
    audit(db, "create", "WorkflowTask", task.id, f"Kreiran zadatak: {task.title}", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(task), request)
    db.commit()
    return get_task(db, task.id)


@router.get("/workflow-tasks/{task_id}", response_model=WorkflowTaskOut)
def task_detail(task_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("workflow_tasks.read"))):
    return get_task(db, task_id)


@router.patch("/workflow-tasks/{task_id}", response_model=WorkflowTaskOut)
def update_task(task_id: int, payload: WorkflowTaskUpdate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("workflow_tasks.write"))):
    task = get_task(db, task_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("assignee_provider_id") and not db.get(Provider, data["assignee_provider_id"]):
        raise HTTPException(404, detail="Odgovorna osoba nije pronadena")
    if data.get("status") == "completed" and any(not item.completed for item in task.checklist):
        raise HTTPException(422, detail="Dovrsite checklistu prije zatvaranja zadatka")
    before = snapshot(task)
    for key, value in data.items():
        setattr(task, key, value)
    task.completed_at = datetime.now(timezone.utc) if task.status == "completed" else None
    db.flush()
    audit(db, "complete" if task.status == "completed" else "update", "WorkflowTask", task.id, f"Azuriran zadatak: {task.title} ({task.status})", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(task), request)
    db.commit()
    return get_task(db, task.id)


@router.post("/workflow-tasks/{task_id}/checklist/{item_id}/toggle", response_model=WorkflowTaskOut)
def toggle_checklist(task_id: int, item_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("workflow_tasks.write"))):
    task = get_task(db, task_id)
    item = next((entry for entry in task.checklist if entry.id == item_id), None)
    if not item:
        raise HTTPException(404, detail="Stavka checkliste nije pronadena")
    before = snapshot(item)
    item.completed = not item.completed
    item.completed_by = actor.user_id if item.completed else None
    item.completed_at = datetime.now(timezone.utc) if item.completed else None
    db.flush()
    audit(db, "checklist_completed" if item.completed else "checklist_reopened", "WorkflowTask", task.id, f"Checklist stavka: {item.label}", actor.user_id, actor.actor_type, actor.api_key_id, before, snapshot(item), request)
    db.commit()
    return get_task(db, task.id)


@router.get("/patients/{patient_id}/workflow-tasks", response_model=list[WorkflowTaskOut])
def patient_tasks(patient_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("workflow_tasks.read"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail="Pacijent nije pronaden")
    return db.scalars(task_query().where(WorkflowTask.patient_id == patient_id).order_by(WorkflowTask.due_date.asc().nulls_last())).unique().all()


@router.get("/episodes/{episode_id}/workflow-tasks", response_model=list[WorkflowTaskOut])
def episode_tasks(episode_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("workflow_tasks.read"))):
    if not db.get(ClinicalEpisode, episode_id):
        raise HTTPException(404, detail="Epizoda nije pronadena")
    return db.scalars(task_query().where(WorkflowTask.episode_id == episode_id).order_by(WorkflowTask.due_date.asc().nulls_last())).unique().all()
