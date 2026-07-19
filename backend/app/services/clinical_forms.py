from datetime import datetime, timezone
import hashlib
import json

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


def field_definitions(version: ClinicalFormVersion) -> dict[str, dict]:
    return {
        field["field_key"]: field
        for section in version.sections_json
        for field in section.get("fields", [])
    }


def current_revision_number(db: Session, instance_id: int) -> int:
    return db.scalar(
        select(func.max(ClinicalFormRevision.revision_number)).where(
            ClinicalFormRevision.instance_id == instance_id
        )
    ) or 0


def _validation_error(code: str, message: str, errors: list[dict]) -> HTTPException:
    return HTTPException(422, detail={"code": code, "message": message, "fields": errors})


def _stale_form_error(instance: ClinicalFormInstance, expected_revision_number: int, actual_revision_number: int) -> HTTPException:
    return HTTPException(
        409,
        detail={
            "code": "stale_form",
            "message": "Drugi korisnik je izmijenio ovaj nalaz. Lokalni unos nije prepisan.",
            "expected_revision_number": expected_revision_number,
            "actual_revision_number": actual_revision_number,
            "current_updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
            "server_data": instance.data_json,
        },
    )


def _completion_payload_hash(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_submission(version: ClinicalFormVersion, data: dict, *, require_complete: bool) -> None:
    fields = field_definitions(version)
    unknown = sorted(set(data) - set(fields))
    if unknown:
        raise _validation_error(
            "unknown_fields",
            "Obrazac sadrži polja koja ne pripadaju aktivnoj verziji obrasca.",
            [
                {
                    "field_key": key,
                    "label": "Nepodržano polje",
                    "message": "Polje nije dio aktivne verzije obrasca.",
                }
                for key in unknown
            ],
        )
    validate_data(version, data)
    if not require_complete:
        return
    missing = sorted(
        key for key in required_field_keys(version)
        if data.get(key) in (None, "", [], {})
    )
    if missing:
        raise _validation_error(
            "required_fields",
            "Dopunite obvezna polja prije dovršavanja obrasca.",
            [
                {
                    "field_key": key,
                    "label": fields[key]["label"],
                    "message": "Polje je obvezno.",
                }
                for key in missing
            ],
        )


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
            label = field["label"]
            if field_type not in STRUCTURED_LIST_TYPES or value in (None, []):
                continue
            if not isinstance(value, list):
                raise _validation_error("invalid_type", "Provjerite unesene podatke.", [{"field_key": key, "label": label, "message": "Vrijednost mora biti strukturirani popis."}])
            if len(value) > field.get("max_items", 50):
                raise _validation_error("maximum_items", "Provjerite unesene podatke.", [{"field_key": key, "label": label, "message": "Uneseno je previše stavki."}])
            item_ids = [item.get("item_id") for item in value if isinstance(item, dict)]
            if len(item_ids) != len(value) or any(not item_id for item_id in item_ids) or len(set(item_ids)) != len(item_ids):
                raise _validation_error("invalid_item_id", "Provjerite unesene podatke.", [{"field_key": key, "label": label, "message": "Svaka stavka mora imati jedinstvenu internu oznaku."}])
            allowed = {item["field_key"] for item in field["item_fields"]}
            required = {item["field_key"] for item in field["item_fields"] if item.get("required")}
            item_labels = {item["field_key"]: item["label"] for item in field["item_fields"]}
            for index, item in enumerate(value):
                if set(item) - allowed - {"item_id"}:
                    raise _validation_error("unknown_item_fields", "Provjerite unesene podatke.", [{"field_key": key, "label": label, "message": f"Stavka {index + 1} sadrži nepodržane podatke."}])
                missing = [item_key for item_key in required if item.get(item_key) in (None, "", [])]
                if missing:
                    missing_labels = ", ".join(item_labels[item_key] for item_key in missing)
                    raise _validation_error("required_item_fields", "Dopunite obvezna polja prije dovršavanja obrasca.", [{"field_key": key, "label": label, "message": f"Stavka {index + 1}: nedostaje {missing_labels}."}])
            if field_type == "structured_specimen_list":
                labels = [item.get("specimen_label") for item in value]
                if len(labels) != len(set(labels)):
                    raise _validation_error("duplicate_specimen_labels", "Provjerite unesene podatke.", [{"field_key": key, "label": label, "message": "Oznake uzoraka moraju biti jedinstvene."}])


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


def update_instance(db: Session, instance: ClinicalFormInstance, data: dict, actor_user_id: int | None, expected_revision_number: int) -> None:
    if instance.status in {"completed", "signed", "amended", "void"}:
        raise HTTPException(409, detail="Dovršen ili potpisan obrazac nije moguće tiho mijenjati")
    actual_revision_number = current_revision_number(db, instance.id)
    if expected_revision_number != actual_revision_number:
        raise _stale_form_error(instance, expected_revision_number, actual_revision_number)
    validate_submission(instance.form_version, data, require_complete=False)
    instance.data_json = dict(data)
    instance.rendered_summary = render_summary(instance.form_version, data)
    instance.status = "in_progress"
    instance.last_edited_by = actor_user_id
    revision_number = actual_revision_number + 1
    db.add(ClinicalFormRevision(instance=instance, revision_number=revision_number, data_json=dict(data), rendered_summary=instance.rendered_summary, edited_by=actor_user_id))
    db.flush()


def save_and_complete_instance(
    db: Session,
    instance: ClinicalFormInstance,
    data: dict,
    actor_user_id: int | None,
    expected_revision_number: int,
    idempotency_key: str,
) -> bool:
    payload_hash = _completion_payload_hash(data)
    if instance.completion_idempotency_key == idempotency_key:
        if instance.completion_payload_hash != payload_hash:
            raise HTTPException(409, detail={"code": "idempotency_conflict", "message": "Ova potvrda dovršavanja već je iskorištena za drugi sadržaj."})
        if instance.status in {"completed", "signed", "amended"}:
            return False
    if instance.status not in {"draft", "in_progress"}:
        raise HTTPException(409, detail="Samo radni obrazac može biti dovršen")
    actual_revision_number = current_revision_number(db, instance.id)
    if expected_revision_number != actual_revision_number:
        raise _stale_form_error(instance, expected_revision_number, actual_revision_number)
    validate_submission(instance.form_version, data, require_complete=True)
    instance.data_json = dict(data)
    instance.rendered_summary = render_summary(instance.form_version, data)
    instance.status = "completed"
    instance.last_edited_by = actor_user_id
    instance.completed_by = actor_user_id
    instance.completed_at = datetime.now(timezone.utc)
    instance.completion_idempotency_key = idempotency_key
    instance.completion_payload_hash = payload_hash
    db.add(
        ClinicalFormRevision(
            instance=instance,
            revision_number=actual_revision_number + 1,
            data_json=dict(data),
            rendered_summary=instance.rendered_summary,
            edited_by=actor_user_id,
        )
    )
    db.flush()
    return True


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
