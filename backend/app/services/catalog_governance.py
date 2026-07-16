from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import Actor
from app.models.domain import ClinicalFormDefinition, ClinicalFormVersion, PatientJourney, Service, ServiceFormBinding, ServicePackage, ServicePackageItem, ServicePackageVersion
from app.services.clinical_forms import validate_sections
from app.services.journey_activities import create_activity


def create_package_version(db: Session, package: ServicePackage, items: list[dict]) -> ServicePackageVersion:
    if len({item["sequence"] for item in items}) != len(items) or len({item["activity_key"] for item in items}) != len(items):
        raise HTTPException(422, detail="Redni brojevi i oznake aktivnosti paketa moraju biti jedinstveni")
    for item in items:
        if not db.get(Service, item["service_id"]):
            raise HTTPException(404, detail=f"Usluga {item['service_id']} nije pronađena")
    version_number = (db.scalar(select(func.max(ServicePackageVersion.version)).where(ServicePackageVersion.package_id == package.id)) or 0) + 1
    version = ServicePackageVersion(package_id=package.id, version=version_number, status="draft")
    db.add(version); db.flush()
    for item in sorted(items, key=lambda value: value["sequence"]):
        db.add(ServicePackageItem(package_version_id=version.id, **item))
    db.flush()
    return version


def publish_package_version(db: Session, version: ServicePackageVersion, actor_user_id: int) -> None:
    if version.status != "draft" or not version.items:
        raise HTTPException(409, detail="Objaviti se može samo potpuna radna verzija paketa")
    for other in version.package.versions:
        if other.status == "published":
            other.status = "retired"
    version.status = "published"; version.approved_by = actor_user_id; version.approved_at = datetime.now(timezone.utc); version.published_at = version.approved_at


def materialize_package(db: Session, journey: PatientJourney, version: ServicePackageVersion, assignments: list[dict], actor: Actor, request: Request):
    if version.status != "published":
        raise HTTPException(409, detail="Samo objavljeni paket može stvoriti aktivnosti")
    assignment_by_item = {item["package_item_id"]: item for item in assignments}
    if set(assignment_by_item) != {item.id for item in version.items}:
        raise HTTPException(422, detail="Raspored mora sadržavati svaku aktivnost paketa točno jednom")
    created = []
    for package_item in sorted(version.items, key=lambda value: value.sequence):
        assignment = assignment_by_item[package_item.id]
        activity = create_activity(db, journey, {
            "service_id": package_item.service_id, "activity_key": package_item.activity_key,
            "activity_kind": package_item.activity_kind, "specialty_key": package_item.specialty_key,
            "date": assignment["date"], "start_time": assignment["start_time"], "end_time": assignment["end_time"],
            "provider_id": assignment["provider_id"], "room_id": assignment["room_id"], "depends_on_activity_id": None,
            "required": package_item.required, "notes": f"Paket {version.package.name} v{version.version}",
        }, actor, request)
        activity.package_item_id = package_item.id
        created.append(activity)
    return created


def create_form_definition(db: Session, data: dict, actor_user_id: int) -> tuple[ClinicalFormDefinition, ClinicalFormVersion]:
    validate_sections(data["sections_json"])
    definition = ClinicalFormDefinition(form_key=data["form_key"], name=data["name"], specialty_key=data["specialty_key"], activity_kind=data["activity_kind"], description=data.get("description"), active=True)
    db.add(definition); db.flush()
    version = ClinicalFormVersion(definition_id=definition.id, version=1, status="draft", sections_json=data["sections_json"], validation_schema_json=data["validation_schema_json"], print_layout_json=data["print_layout_json"], output_document_type=data["output_document_type"])
    db.add(version); db.flush()
    return definition, version


def clone_form_version(db: Session, definition: ClinicalFormDefinition, source: ClinicalFormVersion, overrides: dict) -> ClinicalFormVersion:
    if source.definition_id != definition.id:
        raise HTTPException(404, detail="Verzija ne pripada definiciji obrasca")
    sections = overrides.get("sections_json") or source.sections_json
    validate_sections(sections)
    number = (db.scalar(select(func.max(ClinicalFormVersion.version)).where(ClinicalFormVersion.definition_id == definition.id)) or 0) + 1
    version = ClinicalFormVersion(definition_id=definition.id, version=number, status="draft", sections_json=sections, validation_schema_json=overrides.get("validation_schema_json") or source.validation_schema_json, print_layout_json=overrides.get("print_layout_json") or source.print_layout_json, output_document_type=overrides.get("output_document_type") or source.output_document_type, supersedes_version_id=source.id)
    db.add(version); db.flush(); return version


def publish_form_version(db: Session, version: ClinicalFormVersion, actor_user_id: int) -> None:
    if version.status != "draft":
        raise HTTPException(409, detail="Objaviti se može samo radna verzija obrasca")
    validate_sections(version.sections_json)
    version.status = "published"; version.approved_by = actor_user_id; version.approved_at = datetime.now(timezone.utc); version.published_at = version.approved_at


def create_binding(db: Session, data: dict, actor_user_id: int) -> ServiceFormBinding:
    version = db.get(ClinicalFormVersion, data["form_version_id"])
    if not version or version.status != "published":
        raise HTTPException(409, detail="Povezati se može samo objavljena verzija obrasca")
    if not data.get("service_id") and not (data.get("specialty_key") and data.get("activity_kind")):
        raise HTTPException(422, detail="Povezivanje zahtijeva uslugu ili specijalnost i vrstu aktivnosti")
    binding = ServiceFormBinding(**data, active=True, created_by=actor_user_id)
    db.add(binding); db.flush(); return binding
