from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import ClinicalFormInstance, JourneyActivity, PathologyCase, PathologySpecimen, PatientJourney, ProcedureIntervention, SignedClinicalReport
from app.services.reports import verify_report_integrity


TERMINAL_ACTIVITY_STATUSES = {"completed", "not_performed", "cancelled"}
NO_REPORT_RESOLUTION_STATUSES = {"not_required", "legacy"}
RESOLVED_CONSUMABLE_STATUSES = {"confirmed", "not_applicable"}
SPECIMEN_REQUIRED_INTERVENTIONS = {"biopsy", "polypectomy"}
SPECIMEN_RETRIEVED_STATUSES = {"retrieved", "collected"}


def activity_report_policy(activity: JourneyActivity) -> dict:
    report_required = activity.form_resolution_status not in NO_REPORT_RESOLUTION_STATUSES
    return {
        "report_required": report_required,
        "signature_required_before_activity_completion": False,
        "signature_required_before_billing": report_required,
        "allow_post_visit_signing": False,
        "policy_source": "activity_form_resolution_status",
        "policy_version": "1",
    }


def validate_clinical_visit_readiness(db: Session, journey: PatientJourney, *, require_consumables: bool) -> None:
    """Fail closed on the shared clinical gates used by billing, payment and closure."""
    activities = db.scalars(
        select(JourneyActivity)
        .where(JourneyActivity.journey_id == journey.id, JourneyActivity.required.is_(True))
        .order_by(JourneyActivity.sequence, JourneyActivity.id)
    ).all()
    unresolved = [item.id for item in activities if item.status not in TERMINAL_ACTIVITY_STATUSES]
    if unresolved:
        raise HTTPException(409, detail="Sve obvezne aktivnosti moraju biti završene ili razriješene s razlogom")

    if any(item.status == "completed" and require_consumables and item.consumables_status not in RESOLVED_CONSUMABLE_STATUSES for item in activities):
        raise HTTPException(409, detail="Potrošni materijal svih dovršenih aktivnosti mora biti razriješen")

    reports = db.scalars(
        select(SignedClinicalReport)
        .where(SignedClinicalReport.journey_id == journey.id, SignedClinicalReport.superseded_at.is_(None))
    ).all()
    reports_by_activity = {item.activity_id: item for item in reports}
    for activity in activities:
        if activity.status != "completed":
            continue
        policy = activity_report_policy(activity)
        form = db.scalar(
            select(ClinicalFormInstance)
            .where(
                ClinicalFormInstance.activity_id == activity.id,
                ClinicalFormInstance.status.notin_({"amended", "void"}),
            )
            .order_by(ClinicalFormInstance.id.desc())
            .limit(1)
        )
        if policy["report_required"] and (not form or form.status not in {"completed", "signed"}):
            raise HTTPException(409, detail="Klinički obrazac aktivnosti mora biti dovršen prije naplate ili završetka dolaska")
        interventions = db.scalars(select(ProcedureIntervention).where(ProcedureIntervention.activity_id == activity.id)).all()
        if any(item.complication is None for item in interventions):
            raise HTTPException(409, detail="Za svaku intervenciju izričito razriješite komplikacije, uključujući odgovor 'nema'")
        specimen_intervention_ids = set(
            db.scalars(
                select(PathologySpecimen.source_intervention_id)
                .join(PathologyCase, PathologyCase.id == PathologySpecimen.case_id)
                .where(PathologyCase.source_activity_id == activity.id)
            ).all()
        )
        missing_specimens = [
            item.id
            for item in interventions
            if item.intervention_type in SPECIMEN_REQUIRED_INTERVENTIONS
            and (item.intervention_type == "biopsy" or item.retrieval_status in SPECIMEN_RETRIEVED_STATUSES)
            and item.id not in specimen_intervention_ids
        ]
        if missing_specimens:
            raise HTTPException(409, detail="Svaka biopsija ili dohvaćena polipektomija mora imati označen patološki uzorak")
        if not policy["signature_required_before_billing"]:
            continue
        report = reports_by_activity.get(activity.id)
        if not report:
            raise HTTPException(409, detail="Potrebni nalazi aktivnosti moraju biti potpisani prije naplate ili završetka dolaska")
        verify_report_integrity(report)

    if any(item.status == "open" for item in journey.blockers):
        raise HTTPException(409, detail="Otvoreni blokatori moraju biti riješeni prije naplate ili završetka dolaska")
