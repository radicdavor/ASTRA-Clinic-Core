from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain import (
    ClinicalFormInstance,
    ClinicalFormRevision,
    ClinicalFormVersion,
    JourneyActivity,
    ServiceFormBinding,
    ServicePackageItem,
)
from app.core.clinical_registries import CLINICAL_FORM_FIELD_TYPES


FIELD_TYPES = CLINICAL_FORM_FIELD_TYPES
STRUCTURED_LIST_TYPES = {
    "repeatable_group", "structured_diagnosis_list", "structured_medication_list",
    "structured_anatomical_sites", "structured_polyp_list", "structured_biopsy_list",
    "structured_intervention_list", "structured_specimen_list", "structured_segment_findings",
}


def validate_sections(sections: list) -> None:
    if not isinstance(sections, list) or not sections:
        raise HTTPException(422, detail="Obrazac mora sadržavati barem jednu sekciju")
    keys: set[str] = set()
    for section in sections:
        if not isinstance(section, dict) or not section.get("section_key") or not isinstance(section.get("fields"), list):
            raise HTTPException(422, detail="Svaka sekcija mora imati stabilnu oznaku i popis polja")
        for field in section["fields"]:
            key = field.get("field_key") if isinstance(field, dict) else None
            field_type = field.get("type") if isinstance(field, dict) else None
            if not key or not field.get("label") or field_type not in FIELD_TYPES:
                raise HTTPException(422, detail="Polje mora imati oznaku, naziv i dopuštenu vrstu")
            if key in keys:
                raise HTTPException(422, detail=f"Oznaka polja nije jedinstvena: {key}")
            keys.add(key)
            if field.get("options") is not None and not isinstance(field["options"], list):
                raise HTTPException(422, detail=f"Opcije polja {key} moraju biti popis")
            if field_type in STRUCTURED_LIST_TYPES:
                item_fields = field.get("item_fields")
                if not isinstance(item_fields, list) or not item_fields:
                    raise HTTPException(422, detail=f"Strukturirano polje {key} mora imati kontrolirani item_fields")
                item_keys = [item.get("field_key") for item in item_fields if isinstance(item, dict)]
                if len(item_keys) != len(item_fields) or None in item_keys or len(item_keys) != len(set(item_keys)):
                    raise HTTPException(422, detail=f"Stavke polja {key} moraju imati jedinstvene oznake")
                allowed_item_types = FIELD_TYPES - STRUCTURED_LIST_TYPES
                if any(not item.get("label") or item.get("type") not in allowed_item_types for item in item_fields if isinstance(item, dict)):
                    raise HTTPException(422, detail=f"Stavke polja {key} moraju imati naziv i dopuštenu jednostavnu vrstu")
                if any(item.get("options") is not None and not isinstance(item["options"], list) for item in item_fields):
                    raise HTTPException(422, detail=f"Opcije stavki polja {key} moraju biti popis")
                if not 1 <= field.get("max_items", 50) <= 100:
                    raise HTTPException(422, detail=f"Polje {key} prelazi dopušteni broj stavki")


def required_field_keys(version: ClinicalFormVersion) -> set[str]:
    return {
        field["field_key"]
        for section in version.sections_json
        for field in section.get("fields", [])
        if field.get("required")
    }


def render_summary(version: ClinicalFormVersion, data: dict) -> str:
    labels = {
        field["field_key"]: field["label"]
        for section in version.sections_json
        for field in section.get("fields", [])
    }
    lines = []
    for key, value in data.items():
        if value not in (None, "", [], {}):
            if isinstance(value, list) and value and isinstance(value[0], dict):
                shown = " | ".join(", ".join(f"{k}: {item[k]}" for k in sorted(item) if k != "item_id" and item[k] not in (None, "", [])) for item in value)
            else:
                shown = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value)
            lines.append(f"{labels.get(key, key)}: {shown}")
    return "\n".join(lines)


def validate_data(version: ClinicalFormVersion, data: dict) -> None:
    for section in version.sections_json:
        for field in section.get("fields", []):
            key, field_type, value = field["field_key"], field["type"], data.get(field["field_key"])
            if field_type not in STRUCTURED_LIST_TYPES or value in (None, []):
                continue
            if not isinstance(value, list):
                raise HTTPException(422, detail=f"Polje {key} mora biti strukturirani popis")
            if len(value) > field.get("max_items", 50):
                raise HTTPException(422, detail=f"Polje {key} ima previše stavki")
            item_ids = [item.get("item_id") for item in value if isinstance(item, dict)]
            if len(item_ids) != len(value) or any(not item_id for item_id in item_ids) or len(set(item_ids)) != len(item_ids):
                raise HTTPException(422, detail=f"Svaka stavka polja {key} mora imati jedinstveni item_id")
            allowed = {item["field_key"] for item in field["item_fields"]}
            required = {item["field_key"] for item in field["item_fields"] if item.get("required")}
            for item in value:
                if set(item) - allowed - {"item_id"}:
                    raise HTTPException(422, detail=f"Stavka polja {key} sadrži nepoznata polja")
                missing = [item_key for item_key in required if item.get(item_key) in (None, "", [])]
                if missing:
                    raise HTTPException(422, detail=f"Stavka polja {key} nema obvezna polja: {', '.join(missing)}")
            if field_type == "structured_specimen_list":
                labels = [item.get("specimen_label") for item in value]
                if len(labels) != len(set(labels)):
                    raise HTTPException(422, detail="Oznake uzoraka moraju biti jedinstvene")


def resolve_form_version(db: Session, activity: JourneyActivity) -> tuple[ClinicalFormVersion, str]:
    if activity.package_item_id:
        item = db.get(ServicePackageItem, activity.package_item_id)
        if item and item.form_binding_override_version_id:
            version = db.get(ClinicalFormVersion, item.form_binding_override_version_id)
            if version and version.status == "published":
                return version, "package_item_override"

    scopes = [
        ("clinic_service", ServiceFormBinding.service_id == activity.service_id, ServiceFormBinding.clinic_id.is_not(None), ServiceFormBinding.clinic_id == activity.clinic_id),
        ("default_service", ServiceFormBinding.service_id == activity.service_id, ServiceFormBinding.clinic_id.is_(None)),
        (
            "specialty_activity_kind",
            ServiceFormBinding.service_id.is_(None),
            ServiceFormBinding.specialty_key == activity.specialty_key,
            ServiceFormBinding.activity_kind == activity.activity_kind,
            ServiceFormBinding.clinic_id.is_(None),
        ),
    ]
    for source, *conditions in scopes:
        binding = db.scalar(
            select(ServiceFormBinding)
            .join(ClinicalFormVersion, ClinicalFormVersion.id == ServiceFormBinding.form_version_id)
            .where(ServiceFormBinding.active.is_(True), ClinicalFormVersion.status == "published", *conditions)
            .order_by(ServiceFormBinding.id.desc())
            .limit(1)
        )
        if binding:
            return binding.form_version, source
    raise HTTPException(409, detail="Za ovu uslugu i vrstu aktivnosti nije konfiguriran objavljeni klinički obrazac")


def resolve_instance(db: Session, activity: JourneyActivity, actor_user_id: int | None) -> ClinicalFormInstance:
    current = db.scalar(
        select(ClinicalFormInstance)
        .where(
            ClinicalFormInstance.activity_id == activity.id,
            ClinicalFormInstance.purpose == "clinical_report",
            ClinicalFormInstance.status.notin_({"amended", "void"}),
        )
        .order_by(ClinicalFormInstance.id.desc())
        .limit(1)
    )
    if current:
        return current
    version, source = resolve_form_version(db, activity)
    now = datetime.now(timezone.utc)
    instance = ClinicalFormInstance(
        activity_id=activity.id,
        form_version_id=version.id,
        purpose="clinical_report",
        status="draft",
        data_json={},
        created_by=actor_user_id,
        last_edited_by=actor_user_id,
        binding_source=source,
        resolved_at=now,
    )
    db.add(instance)
    activity.form_resolution_status = "resolved"
    db.flush()
    return instance


def update_instance(db: Session, instance: ClinicalFormInstance, data: dict, actor_user_id: int | None) -> None:
    if instance.status in {"completed", "signed", "amended", "void"}:
        raise HTTPException(409, detail="Dovršen ili potpisan obrazac nije moguće tiho mijenjati")
    allowed = {
        field["field_key"]
        for section in instance.form_version.sections_json
        for field in section.get("fields", [])
    }
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise HTTPException(422, detail=f"Nepoznata polja obrasca: {', '.join(unknown)}")
    validate_data(instance.form_version, data)
    instance.data_json = data
    instance.rendered_summary = render_summary(instance.form_version, data)
    instance.status = "in_progress"
    instance.last_edited_by = actor_user_id
    revision_number = (db.scalar(select(func.max(ClinicalFormRevision.revision_number)).where(ClinicalFormRevision.instance_id == instance.id)) or 0) + 1
    db.add(ClinicalFormRevision(instance_id=instance.id, revision_number=revision_number, data_json=data, rendered_summary=instance.rendered_summary, edited_by=actor_user_id))
    db.flush()


def complete_instance(db: Session, instance: ClinicalFormInstance, actor_user_id: int | None) -> None:
    if instance.status not in {"draft", "in_progress"}:
        raise HTTPException(409, detail="Samo radni obrazac može biti dovršen")
    missing = sorted(key for key in required_field_keys(instance.form_version) if instance.data_json.get(key) in (None, "", [], {}))
    if missing:
        raise HTTPException(422, detail=f"Nedostaju obvezna polja: {', '.join(missing)}")
    instance.status = "completed"
    instance.completed_by = actor_user_id
    instance.completed_at = datetime.now(timezone.utc)
    db.flush()


def sign_instance(db: Session, instance: ClinicalFormInstance, actor_user_id: int | None) -> None:
    if instance.status != "completed":
        raise HTTPException(409, detail="Prije potpisa obrazac mora biti dovršen")
    if actor_user_id is None:
        raise HTTPException(403, detail="Potpis zahtijeva prijavljenog zdravstvenog radnika")
    instance.status = "signed"
    instance.signed_by = actor_user_id
    instance.signed_at = datetime.now(timezone.utc)
    db.flush()


def amend_instance(db: Session, instance: ClinicalFormInstance, actor_user_id: int | None) -> ClinicalFormInstance:
    if instance.status != "signed":
        raise HTTPException(409, detail="Ispravak se može otvoriti samo iz potpisanog obrasca")
    instance.status = "amended"
    amendment = ClinicalFormInstance(
        activity_id=instance.activity_id,
        form_version_id=instance.form_version_id,
        purpose=instance.purpose,
        status="draft",
        data_json=dict(instance.data_json),
        rendered_summary=instance.rendered_summary,
        created_by=actor_user_id,
        last_edited_by=actor_user_id,
        amended_from_instance_id=instance.id,
        binding_source="amendment",
        resolved_at=datetime.now(timezone.utc),
    )
    db.add(amendment)
    db.flush()
    return amendment
