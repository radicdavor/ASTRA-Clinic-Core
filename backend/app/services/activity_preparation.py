from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clinical_registries import PREPARATION_REQUIREMENT_KEYS
from app.models.domain import ActivityPreparationRequirement, JourneyActivity, JourneyBlocker, PatientJourney, Service


def materialize_activity_requirements(db: Session, journey: PatientJourney) -> list[ActivityPreparationRequirement]:
    created = []
    for activity in journey.activities:
        package_item = activity.package_item_id and activity.package_item_id
        if not package_item:
            continue
        from app.models.domain import ServicePackageItem
        item = db.get(ServicePackageItem, package_item)
        for requirement in item.preparation_requirements_json or []:
            key = requirement.get("requirement_key")
            if key not in PREPARATION_REQUIREMENT_KEYS:
                raise HTTPException(422, detail=f"Nepoznata stavka pripreme: {key}")
            existing = db.scalar(select(ActivityPreparationRequirement).where(
                ActivityPreparationRequirement.activity_id == activity.id,
                ActivityPreparationRequirement.requirement_key == key,
            ))
            if existing:
                created.append(existing)
                continue
            row = ActivityPreparationRequirement(
                activity_id=activity.id, requirement_key=key, label=requirement["label"],
                patient_instruction=requirement["patient_instruction"], category=requirement.get("category", key),
                required=requirement.get("required", True), state="assigned",
                source_template_key=requirement.get("source_template_key", "service-package"),
                source_template_version=str(requirement.get("source_template_version", "1")),
            )
            db.add(row); created.append(row)
    db.flush()
    return created


def aggregate_requirements(db: Session, journey: PatientJourney) -> dict:
    rows = db.execute(
        select(ActivityPreparationRequirement, JourneyActivity, Service)
        .join(JourneyActivity, JourneyActivity.id == ActivityPreparationRequirement.activity_id)
        .join(Service, Service.id == JourneyActivity.service_id)
        .where(JourneyActivity.journey_id == journey.id)
        .order_by(ActivityPreparationRequirement.requirement_key, JourneyActivity.sequence)
    ).all()
    groups: dict[str, dict] = {}
    contradictions = []
    for requirement, activity, service in rows:
        group = groups.setdefault(requirement.requirement_key, {
            "requirement_key": requirement.requirement_key, "label": requirement.label,
            "patient_instruction": requirement.patient_instruction, "category": requirement.category,
            "required": requirement.required, "states": [], "activities": [], "contradictory": False,
        })
        if group["patient_instruction"] != requirement.patient_instruction:
            group["contradictory"] = True
            contradictions.append(requirement.requirement_key)
        group["states"].append(requirement.state)
        group["activities"].append({"activity_id": activity.id, "sequence": activity.sequence, "activity_key": activity.activity_key, "service_name": service.name, "requirement_id": requirement.id, "state": requirement.state})
    for group in groups.values():
        group["state"] = "blocked" if group["contradictory"] else (
            "confirmed" if group["states"] and all(state in {"confirmed", "not_applicable"} for state in group["states"])
            else "requires_clinician_review" if any(state in {"requires_clinician_review", "blocked"} for state in group["states"])
            else "in_progress"
        )
    return {"journey_id": journey.id, "requirements": list(groups.values()), "contradictions": sorted(set(contradictions))}


def ensure_preparation_conflict_blocker(db: Session, journey: PatientJourney, actor_user_id: int | None) -> list[str]:
    contradictions = aggregate_requirements(db, journey)["contradictions"]
    if not contradictions:
        return []
    existing = db.scalar(select(JourneyBlocker).where(
        JourneyBlocker.journey_id == journey.id,
        JourneyBlocker.blocker_key == "activity_preparation_conflict",
        JourneyBlocker.status == "open",
    ))
    if not existing:
        db.add(JourneyBlocker(
            journey_id=journey.id,
            blocker_key="activity_preparation_conflict",
            category="preparation",
            title="Protuslovne upute pripreme",
            details=f"Potrebna je klinička provjera stavki: {', '.join(contradictions)}",
            is_clinical=True,
            created_by=actor_user_id,
        ))
    journey.preparation_status = "review_required"
    db.flush()
    return contradictions


def update_requirement(db: Session, requirement: ActivityPreparationRequirement, state: str, note: str | None, actor_user_id: int, clinical_review: bool) -> None:
    if requirement.category in {"medication_review", "anticoagulant_review", "antiplatelet_review", "diabetes_review"} and state == "confirmed" and not clinical_review:
        raise HTTPException(403, detail="Kliničku stavku pripreme može potvrditi samo ovlaštena klinička uloga")
    requirement.state = state
    requirement.note = note
    requirement.reviewed_by = actor_user_id
    requirement.reviewed_at = datetime.now(timezone.utc)
