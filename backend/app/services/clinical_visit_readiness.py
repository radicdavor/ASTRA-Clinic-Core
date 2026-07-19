from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import JourneyActivity, PatientJourney, SignedClinicalReport
from app.services.reports import verify_report_integrity


TERMINAL_ACTIVITY_STATUSES = {"completed", "not_performed", "cancelled"}
NO_REPORT_RESOLUTION_STATUSES = {"not_required", "legacy"}
RESOLVED_CONSUMABLE_STATUSES = {"confirmed", "not_applicable"}


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
        if activity.status != "completed" or activity.form_resolution_status in NO_REPORT_RESOLUTION_STATUSES:
            continue
        report = reports_by_activity.get(activity.id)
        if not report:
            raise HTTPException(409, detail="Potrebni nalazi aktivnosti moraju biti potpisani prije naplate ili završetka dolaska")
        verify_report_integrity(report)

    if any(item.status == "open" for item in journey.blockers):
        raise HTTPException(409, detail="Otvoreni blokatori moraju biti riješeni prije naplate ili završetka dolaska")
