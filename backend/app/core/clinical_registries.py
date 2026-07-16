SPECIALTY_KEYS = {"gastroenterology", "gynecology", "aesthetic_medicine", "aesthetic", "general"}
ACTIVITY_KINDS = {
    "specialist_consultation", "gastroscopy", "colonoscopy", "diagnostic_procedure",
    "therapeutic_procedure", "aesthetic_consultation", "aesthetic_treatment",
    "harmonyca_treatment", "pathology_follow_up", "nursing_activity", "other",
}
INTERVENTION_TYPES = {"biopsy", "polypectomy", "clip_placement", "injection", "hemostasis", "dilation", "foreign_body_removal", "other"}
SPECIMEN_TYPES = {"biopsy", "polyp", "mucosal_resection", "cytology", "other"}
RETRIEVAL_STATUSES = {"not_applicable", "not_retrieved", "retrieved", "collected"}
PATHOLOGY_STATUSES = {
    "draft", "specimens_ready", "sent_to_lab", "received_by_lab", "awaiting_result",
    "result_received", "clinician_review_required", "clinician_reviewed",
    "patient_notification_ready", "patient_notified", "closed", "cancelled",
}
REPORT_DOCUMENT_TYPES = {
    "clinical_report", "specialist_report", "gastroscopy_report", "colonoscopy_report",
    "aesthetic_consultation_report", "aesthetic_treatment_report", "pathology_report",
    "other_procedure_report",
}
CLINICAL_FORM_FIELD_TYPES = {
    "short_text", "long_text", "rich_text_limited", "integer", "decimal", "date", "time",
    "checkbox", "select", "multi_select", "diagnosis_list", "medication_list",
    "procedure_intervention_list", "specimen_list", "product_lot", "anatomical_site",
    "clinician_signature", "read_only_source_link", "repeatable_group",
    "structured_diagnosis_list", "structured_medication_list", "structured_anatomical_sites",
    "structured_polyp_list", "structured_biopsy_list", "structured_intervention_list",
    "structured_specimen_list", "structured_segment_findings",
}
PREPARATION_REQUIREMENT_KEYS = {
    "fasting", "bowel_preparation", "medication_review", "anticoagulant_review",
    "antiplatelet_review", "diabetes_review", "escort", "laboratory", "consent", "other",
}
PATHOLOGY_COMMUNICATION_DISPOSITIONS = {
    "delivered_approved_report", "direct_contact", "reviewed_at_follow_up_visit",
    "no_notification_required", "patient_declined", "unable_to_contact",
    "transferred_to_external_care", "cancelled_as_duplicate",
}


def require_registry(value: str, allowed: set[str], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"Nepoznata vrijednost za {label}: {value}")
    return value
