from __future__ import annotations

from dataclasses import dataclass

from app.models.domain import AuditLog


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
