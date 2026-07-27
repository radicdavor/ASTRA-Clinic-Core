from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Appointment, AuditLog, Clinic, ClinicalFinding, ClinicalOpenQuestion, ClinicalReadinessReviewAcknowledgment, ClinicalReadinessSnapshot
from app.schemas.common import ClinicalEvidenceTimelineEventPreview, ClinicalEvidenceTimelineSourceReference


@dataclass(frozen=True)
class ClinicalEvidenceClassification:
    clinical_event_category: str
    clinical_event_label: str
    knowledge_impact: str
    is_clinical_evidence_event: bool


OTHER_CLASSIFICATION = ClinicalEvidenceClassification(
    clinical_event_category="other",
    clinical_event_label="Drugi audit dogadjaj",
    knowledge_impact="no_official_knowledge_impact",
    is_clinical_evidence_event=False,
)


def classify_clinical_evidence_event(action: str, entity_type: str) -> ClinicalEvidenceClassification:
    if entity_type == "ClinicalDocument":
        return classify_clinical_document_event(action)
    if entity_type == "PatientClinicalSummary":
        return classify_patient_summary_event(action)
    return OTHER_CLASSIFICATION


def classify_audit_log(log: AuditLog) -> ClinicalEvidenceClassification:
    return classify_clinical_evidence_event(log.action, log.entity_type)


def classify_clinical_document_event(action: str) -> ClinicalEvidenceClassification:
    mapping = {
        "create": ClinicalEvidenceClassification("source_created", "Izvor kreiran", "no_official_knowledge_impact", True),
        "clinical_document_created": ClinicalEvidenceClassification("source_created", "Izvor kreiran", "no_official_knowledge_impact", True),
        "upload": ClinicalEvidenceClassification("source_created", "Izvor ucitan", "no_official_knowledge_impact", True),
        "clinical_document_uploaded": ClinicalEvidenceClassification("source_created", "Izvor ucitan", "no_official_knowledge_impact", True),
        "update": ClinicalEvidenceClassification("source_updated", "Izvor azuriran", "no_official_knowledge_impact", True),
        "clinical_document_updated": ClinicalEvidenceClassification("source_updated", "Izvor azuriran", "no_official_knowledge_impact", True),
        "ai_document_extracted": ClinicalEvidenceClassification("ai_extraction", "AI prijedlog generiran", "no_official_knowledge_impact", True),
        "clinical_document_ai_extracted": ClinicalEvidenceClassification("ai_extraction", "AI prijedlog generiran", "no_official_knowledge_impact", True),
        "ai_document_extraction_edited": ClinicalEvidenceClassification("ai_extraction", "AI prijedlog uredjen", "no_official_knowledge_impact", True),
        "clinical_document_ai_extraction_edited": ClinicalEvidenceClassification("ai_extraction", "AI prijedlog uredjen", "no_official_knowledge_impact", True),
        "ai_document_summary_rejected": ClinicalEvidenceClassification("ai_rejection", "AI prijedlog odbijen", "removed_from_official_knowledge", True),
        "clinical_document_ai_extraction_rejected": ClinicalEvidenceClassification("ai_rejection", "AI prijedlog odbijen", "removed_from_official_knowledge", True),
        "clinical_document_reviewed": ClinicalEvidenceClassification("physician_review", "Lijecnicki pregledano", "may_enable_official_knowledge", True),
        "clinical_document_review_reset": ClinicalEvidenceClassification("knowledge_visibility", "Pregled resetiran", "removed_from_official_knowledge", True),
    }
    return mapping.get(action, OTHER_CLASSIFICATION)


def classify_patient_summary_event(action: str) -> ClinicalEvidenceClassification:
    mapping = {
        "patient_summary_draft_generated": ClinicalEvidenceClassification("summary_generation", "Draft sazetka generiran", "summary_view_only", True),
        "patient_summary_edited": ClinicalEvidenceClassification("summary_generation", "Sazetak uredjen", "summary_view_only", True),
        "patient_summary_reviewed": ClinicalEvidenceClassification("summary_review", "Sazetak potvrdjen", "summary_view_only", True),
        "patient_summary_review_blocked_stale": ClinicalEvidenceClassification("summary_review", "Potvrda sazetka blokirana", "summary_view_only", True),
    }
    return mapping.get(action, OTHER_CLASSIFICATION)


def _source_reference(
    *,
    source_object_type: str,
    source_object_reference: str,
    patient_id: int,
    source_label: str,
    provenance_label: str,
    source_document_id: int | None = None,
    limitations: list[str] | None = None,
) -> ClinicalEvidenceTimelineSourceReference:
    return ClinicalEvidenceTimelineSourceReference(
        source_object_type=source_object_type,
        source_object_reference=source_object_reference,
        patient_id=patient_id,
        source_label=source_label,
        provenance_label=provenance_label,
        source_document_reference=f"clinical_document:{source_document_id}" if source_document_id else None,
        limitations=limitations or ["Timeline event is source-linked context for human interpretation."],
    )


def _finding_event(finding: ClinicalFinding) -> ClinicalEvidenceTimelineEventPreview:
    event_type = "finding_requires_review" if finding.requires_review else "finding_recorded"
    return ClinicalEvidenceTimelineEventPreview(
        event_key=f"clinical_finding:{finding.id}",
        event_type=event_type,
        label=finding.label,
        source_reference=_source_reference(
            source_object_type="clinical_finding",
            source_object_reference=f"clinical_finding:{finding.id}",
            patient_id=finding.patient_id,
            source_label=finding.source_label,
            provenance_label=f"Finding source: {finding.source_type}",
            source_document_id=finding.source_document_id,
            limitations=finding.limitations_json or None,
        ),
        event_timestamp=finding.created_at,
        display_timestamp=finding.created_at,
        limitations=finding.limitations_json or ["Finding timeline event is not diagnosis or treatment."],
        requires_review=finding.requires_review,
        created_at=finding.created_at,
    )


def _open_question_event(question: ClinicalOpenQuestion) -> ClinicalEvidenceTimelineEventPreview:
    event_type = "open_question_awaiting_review" if question.requires_clinician_review else "open_question_suggested"
    return ClinicalEvidenceTimelineEventPreview(
        event_key=f"clinical_open_question:{question.id}",
        event_type=event_type,
        label=question.label,
        source_reference=_source_reference(
            source_object_type="clinical_open_question",
            source_object_reference=f"clinical_open_question:{question.id}",
            patient_id=question.patient_id,
            source_label=question.source_label,
            provenance_label=f"Open question source: {question.source_type}",
            source_document_id=question.source_document_id,
            limitations=question.limitations_json or None,
        ),
        event_timestamp=question.created_at,
        display_timestamp=question.created_at,
        limitations=question.limitations_json or ["Open question timeline event requires clinician interpretation."],
        requires_review=question.requires_clinician_review,
        created_at=question.created_at,
    )


def _snapshot_events(snapshot: ClinicalReadinessSnapshot) -> list[ClinicalEvidenceTimelineEventPreview]:
    source = _source_reference(
        source_object_type="readiness_snapshot",
        source_object_reference=f"clinical_readiness_snapshot:{snapshot.id}",
        patient_id=snapshot.patient_id,
        source_label=snapshot.template_label or "Clinical readiness snapshot",
        provenance_label="Readiness snapshot",
        limitations=snapshot.limitations_json or None,
    )
    events = [
        ClinicalEvidenceTimelineEventPreview(
            event_key=f"clinical_readiness_snapshot:{snapshot.id}:captured",
            event_type="readiness_snapshot_captured",
            label="Readiness snapshot captured",
            source_reference=source,
            event_timestamp=snapshot.created_at,
            display_timestamp=snapshot.preview_generated_at,
            limitations=snapshot.limitations_json or ["Readiness snapshot is advisory context, not clearance."],
            requires_review=snapshot.preview_status in {"needs_physician_review", "not_ready", "blocked"},
            created_at=snapshot.created_at,
        )
    ]
    if snapshot.superseded_at:
        events.append(
            ClinicalEvidenceTimelineEventPreview(
                event_key=f"clinical_readiness_snapshot:{snapshot.id}:superseded",
                event_type="readiness_snapshot_superseded",
                label="Readiness snapshot superseded",
                source_reference=source,
                event_timestamp=snapshot.superseded_at,
                display_timestamp=snapshot.superseded_at,
                limitations=["Supersession is additive and does not mutate the old snapshot payload."],
                requires_review=False,
                created_at=snapshot.superseded_at,
            )
        )
    return events


def _acknowledgment_event(acknowledgment: ClinicalReadinessReviewAcknowledgment) -> ClinicalEvidenceTimelineEventPreview:
    return ClinicalEvidenceTimelineEventPreview(
        event_key=f"clinical_readiness_acknowledgment:{acknowledgment.id}",
        event_type="acknowledgment_recorded",
        label="Readiness acknowledgment recorded",
        source_reference=_source_reference(
            source_object_type="acknowledgment",
            source_object_reference=f"clinical_readiness_acknowledgment:{acknowledgment.id}",
            patient_id=acknowledgment.patient_id,
            source_label=acknowledgment.advisory_signal_key,
            provenance_label="Human acknowledgment",
            limitations=acknowledgment.limitations_json or None,
        ),
        event_timestamp=acknowledgment.created_at,
        display_timestamp=acknowledgment.created_at,
        limitations=acknowledgment.limitations_json or ["Acknowledgment is human review context, not approval or clearance."],
        requires_review=False,
        created_at=acknowledgment.created_at,
    )


def list_patient_clinical_evidence_timeline(
    db: Session,
    *,
    patient_id: int,
    institution_id: int,
    event_type: str | None = None,
    source_type: str | None = None,
    requires_review: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[ClinicalEvidenceTimelineEventPreview]:
    events: list[ClinicalEvidenceTimelineEventPreview] = []
    events.extend(
        _finding_event(finding)
        for finding in db.scalars(
            select(ClinicalFinding).where(
                ClinicalFinding.patient_id == patient_id,
                ClinicalFinding.institution_id == institution_id,
            )
        ).all()
    )
    events.extend(
        _open_question_event(question)
        for question in db.scalars(
            select(ClinicalOpenQuestion).where(
                ClinicalOpenQuestion.patient_id == patient_id,
                ClinicalOpenQuestion.institution_id == institution_id,
            )
        ).all()
    )
    for snapshot in db.scalars(
        select(ClinicalReadinessSnapshot)
        .join(Appointment, Appointment.id == ClinicalReadinessSnapshot.appointment_id)
        .join(Clinic, Clinic.id == Appointment.clinic_id)
        .where(
            ClinicalReadinessSnapshot.patient_id == patient_id,
            Clinic.institution_id == institution_id,
        )
    ).all():
        events.extend(_snapshot_events(snapshot))
    events.extend(
        _acknowledgment_event(acknowledgment)
        for acknowledgment in db.scalars(
            select(ClinicalReadinessReviewAcknowledgment)
            .join(Appointment, Appointment.id == ClinicalReadinessReviewAcknowledgment.appointment_id)
            .join(Clinic, Clinic.id == Appointment.clinic_id)
            .where(
                ClinicalReadinessReviewAcknowledgment.patient_id == patient_id,
                Clinic.institution_id == institution_id,
            )
        ).all()
    )

    if event_type is not None:
        events = [event for event in events if event.event_type == event_type]
    if source_type is not None:
        events = [event for event in events if event.source_reference.source_object_type == source_type]
    if requires_review is not None:
        events = [event for event in events if event.requires_review is requires_review]
    if date_from is not None:
        events = [event for event in events if event.event_timestamp >= date_from]
    if date_to is not None:
        events = [event for event in events if event.event_timestamp <= date_to]

    return sorted(events, key=lambda event: (event.event_timestamp, event.event_key), reverse=True)
