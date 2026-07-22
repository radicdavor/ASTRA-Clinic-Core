from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import CurrentUserContext
from app.models.domain import Clinic, ClinicalEpisode, ClinicalPlan


def authorized_institution_id(context: CurrentUserContext) -> int:
    institution_id = context.active_clinic.institution_id if context.active_clinic else None
    if institution_id is None:
        raise HTTPException(403, detail="Aktivna klinika nema razriješenu ustanovu")
    return institution_id


def institution_episode_statement(context: CurrentUserContext):
    return (
        select(ClinicalEpisode)
        .options(joinedload(ClinicalEpisode.patient), joinedload(ClinicalEpisode.owner_provider))
        .where(ClinicalEpisode.institution_id == authorized_institution_id(context))
    )


def get_institution_episode(db: Session, episode_id: int, context: CurrentUserContext) -> ClinicalEpisode:
    episode = db.scalar(institution_episode_statement(context).where(ClinicalEpisode.id == episode_id))
    if episode is None:
        raise HTTPException(404, detail="Klinička epizoda nije pronađena")
    return episode


def get_institution_clinical_plan(db: Session, plan_id: int, context: CurrentUserContext) -> ClinicalPlan:
    plan = db.scalar(
        select(ClinicalPlan)
        .join(ClinicalEpisode, ClinicalEpisode.id == ClinicalPlan.episode_id)
        .where(
            ClinicalPlan.id == plan_id,
            ClinicalEpisode.institution_id == authorized_institution_id(context),
        )
    )
    if plan is None:
        raise HTTPException(404, detail="Klinički plan nije pronađen")
    return plan


def provider_belongs_to_institution(db: Session, provider_clinic_id: int | None, context: CurrentUserContext) -> bool:
    if provider_clinic_id is None:
        return True
    return db.scalar(
        select(Clinic.id).where(
            Clinic.id == provider_clinic_id,
            Clinic.institution_id == authorized_institution_id(context),
        )
    ) is not None
