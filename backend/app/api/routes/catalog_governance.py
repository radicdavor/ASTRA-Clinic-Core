from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import ClinicalFormDefinition, ClinicalFormVersion, PatientJourney, ServiceFormBinding, ServicePackage, ServicePackageVersion
from app.schemas.catalog_governance import FormBindingCreate, FormDefinitionCreate, FormVersionDraftCreate, PackageBookRequest, PackageCreate, PackageMaterializeRequest, PackageSchedulePreviewRequest, PackageVersionCreate
from app.schemas.clinical_forms import ClinicalFormDefinitionOut, ClinicalFormVersionOut
from app.schemas.patient_journeys import JourneyActivityOut
from app.services.catalog_governance import book_package, clone_form_version, create_binding, create_form_definition, create_package_version, materialize_package, preview_package_schedule, publish_form_version, publish_package_version

router = APIRouter(prefix="/api", tags=["catalog-governance"])


@router.get("/service-packages")
def list_packages(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("service_packages.read"))):
    packages = db.scalars(select(ServicePackage).options(selectinload(ServicePackage.versions).selectinload(ServicePackageVersion.items)).where(ServicePackage.active.is_(True)).order_by(ServicePackage.name)).all()
    return [{"id": item.id, "package_key": item.package_key, "name": item.name, "description": item.description, "specialty_key": item.specialty_key, "versions": [{"id": version.id, "version": version.version, "status": version.status, "items": [{"id": row.id, "service_id": row.service_id, "activity_key": row.activity_key, "activity_kind": row.activity_kind, "sequence": row.sequence, "duration_minutes": row.default_duration_minutes, "required": row.required, "preparation_requirements": row.preparation_requirements_json} for row in version.items]} for version in item.versions]} for item in packages]


@router.post("/service-package-versions/{version_id}/schedule-preview")
def schedule_preview(version_id: int, payload: PackageSchedulePreviewRequest, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("service_packages.schedule"))):
    version = db.scalar(select(ServicePackageVersion).options(selectinload(ServicePackageVersion.items)).where(ServicePackageVersion.id == version_id))
    if not version:
        raise HTTPException(404, detail="Verzija paketa nije pronađena")
    result = preview_package_schedule(db, version, payload.patient_id, [item.model_dump() for item in payload.assignments])
    audit(db, "package_preview_requested", "ServicePackageVersion", version.id, "Provjeren je raspored paketa bez stvaranja termina", actor.user_id, actor.actor_type, actor.api_key_id, None, {"valid": result["valid"], "patient_id": payload.patient_id}, request)
    db.commit()
    return result


@router.post("/service-package-versions/{version_id}/book", status_code=201)
def book_published_package(version_id: int, payload: PackageBookRequest, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("service_packages.schedule"))):
    version = db.scalar(select(ServicePackageVersion).options(selectinload(ServicePackageVersion.items), selectinload(ServicePackageVersion.package)).where(ServicePackageVersion.id == version_id))
    if not version:
        raise HTTPException(404, detail="Verzija paketa nije pronađena")
    journey = book_package(db, version, payload.patient_id, payload.episode_id, [item.model_dump() for item in payload.assignments], payload.idempotency_key, actor, request)
    audit(db, "package_booked", "PatientJourney", journey.id, "Transakcijski je rezerviran koordinirani paket", actor.user_id, actor.actor_type, actor.api_key_id, None, {"package_version_id": version.id, "activity_ids": [item.id for item in journey.activities]}, request)
    db.commit()
    return {"journey_id": journey.id, "appointment_id": journey.appointment_id, "activity_ids": [item.id for item in journey.activities]}


@router.post("/service-packages", status_code=201)
def add_package(payload: PackageCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("service_packages.manage"))):
    package = ServicePackage(**payload.model_dump(), active=True, created_by=actor.user_id)
    db.add(package); db.flush(); audit(db, "service_package_created", "ServicePackage", package.id, "Stvoren je radni paket usluga", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(package), request); db.commit(); db.refresh(package); return {"id": package.id, **payload.model_dump()}


@router.post("/service-packages/{package_id}/versions", status_code=201)
def add_package_version(package_id: int, payload: PackageVersionCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("service_packages.manage"))):
    package = db.get(ServicePackage, package_id)
    if not package: raise HTTPException(404, detail="Paket nije pronađen")
    version = create_package_version(db, package, [item.model_dump() for item in payload.items]); audit(db, "service_package_version_created", "ServicePackageVersion", version.id, "Stvorena je radna verzija paketa", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(version), request); db.commit(); return {"id": version.id, "version": version.version, "status": version.status}


@router.post("/service-package-versions/{version_id}/publish")
def publish_package(version_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("service_packages.manage"))):
    version = db.scalar(select(ServicePackageVersion).options(selectinload(ServicePackageVersion.items), selectinload(ServicePackageVersion.package).selectinload(ServicePackage.versions)).where(ServicePackageVersion.id == version_id))
    if not version: raise HTTPException(404, detail="Verzija paketa nije pronađena")
    publish_package_version(db, version, actor.user_id); audit(db, "service_package_published", "ServicePackageVersion", version.id, "Paket usluga je objavljen", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(version), request); db.commit(); return {"id": version.id, "status": version.status}


@router.post("/patient-journeys/{journey_id}/packages/{version_id}/materialize", response_model=list[JourneyActivityOut])
def materialize(journey_id: int, version_id: int, payload: PackageMaterializeRequest, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("service_packages.schedule"))):
    journey = db.scalar(select(PatientJourney).options(selectinload(PatientJourney.activities)).where(PatientJourney.id == journey_id))
    version = db.scalar(select(ServicePackageVersion).options(selectinload(ServicePackageVersion.items), selectinload(ServicePackageVersion.package)).where(ServicePackageVersion.id == version_id))
    if not journey or not version: raise HTTPException(404, detail="Dolazak ili paket nije pronađen")
    created = materialize_package(db, journey, version, [item.model_dump() for item in payload.assignments], actor, request); audit(db, "service_package_materialized", "PatientJourney", journey.id, "Paket je stvorio aktivnosti jednog dolaska", actor.user_id, actor.actor_type, actor.api_key_id, None, {"package_version_id": version.id, "activity_ids": [item.id for item in created]}, request); db.commit(); return created


@router.post("/clinical-forms/definitions", response_model=ClinicalFormDefinitionOut, status_code=201)
def add_form_definition(payload: FormDefinitionCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_forms.manage"))):
    definition, version = create_form_definition(db, payload.model_dump(), actor.user_id); audit(db, "clinical_form_definition_created", "ClinicalFormDefinition", definition.id, "Stvorena je definicija i radna verzija obrasca", actor.user_id, actor.actor_type, actor.api_key_id, None, {"version_id": version.id}, request); db.commit(); db.refresh(definition); return definition


@router.post("/clinical-forms/definitions/{definition_id}/versions/{source_version_id}/clone", response_model=ClinicalFormVersionOut, status_code=201)
def clone_form(definition_id: int, source_version_id: int, payload: FormVersionDraftCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_forms.manage"))):
    definition = db.get(ClinicalFormDefinition, definition_id); source = db.get(ClinicalFormVersion, source_version_id)
    if not definition or not source: raise HTTPException(404, detail="Obrazac ili izvorna verzija nisu pronađeni")
    version = clone_form_version(db, definition, source, payload.model_dump(exclude_none=True)); audit(db, "clinical_form_version_created", "ClinicalFormVersion", version.id, "Stvorena je nova radna verzija obrasca", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(version), request); db.commit(); db.refresh(version); return version


@router.post("/clinical-form-versions/{version_id}/publish", response_model=ClinicalFormVersionOut)
def publish_form(version_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_forms.manage"))):
    version = db.get(ClinicalFormVersion, version_id)
    if not version: raise HTTPException(404, detail="Verzija obrasca nije pronađena")
    publish_form_version(db, version, actor.user_id); audit(db, "clinical_form_version_published", "ClinicalFormVersion", version.id, "Verzija obrasca je ljudski odobrena i objavljena", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(version), request); db.commit(); db.refresh(version); return version


@router.post("/clinical-form-versions/{version_id}/retire", response_model=ClinicalFormVersionOut)
def retire_form(version_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_forms.manage"))):
    version = db.get(ClinicalFormVersion, version_id)
    if not version or version.status != "published": raise HTTPException(409, detail="Umiroviti se može samo objavljena verzija obrasca")
    version.status = "retired"
    for binding in db.scalars(select(ServiceFormBinding).where(ServiceFormBinding.form_version_id == version.id, ServiceFormBinding.active.is_(True))).all(): binding.active = False
    audit(db, "clinical_form_version_retired", "ClinicalFormVersion", version.id, "Verzija obrasca je umirovljena; postojeći potpisani nalazi ostaju očuvani", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(version), request); db.commit(); db.refresh(version); return version


@router.post("/clinical-form-bindings", status_code=201)
def add_form_binding(payload: FormBindingCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("clinical_forms.manage"))):
    binding = create_binding(db, payload.model_dump(), actor.user_id); audit(db, "clinical_form_binding_created", "ServiceFormBinding", binding.id, "Objavljeni obrazac izričito je povezan s kliničkom aktivnošću", actor.user_id, actor.actor_type, actor.api_key_id, None, snapshot(binding), request); db.commit(); return {"id": binding.id, "form_version_id": binding.form_version_id, "active": binding.active}
