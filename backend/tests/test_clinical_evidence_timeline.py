from app.services.clinical_evidence_timeline import classify_clinical_evidence_event


def test_clinical_document_audit_events_are_classified_for_evidence_timeline():
    cases = [
        ("create", "source_created", "Izvor kreiran", "no_official_knowledge_impact"),
        ("upload", "source_created", "Izvor ucitan", "no_official_knowledge_impact"),
        ("update", "source_updated", "Izvor azuriran", "no_official_knowledge_impact"),
        ("ai_document_extracted", "ai_extraction", "AI prijedlog generiran", "no_official_knowledge_impact"),
        ("ai_document_extraction_edited", "ai_extraction", "AI prijedlog uredjen", "no_official_knowledge_impact"),
        ("ai_document_summary_rejected", "ai_rejection", "AI prijedlog odbijen", "removed_from_official_knowledge"),
        ("clinical_document_reviewed", "physician_review", "Lijecnicki pregledano", "may_enable_official_knowledge"),
    ]

    for action, category, label, impact in cases:
        result = classify_clinical_evidence_event(action, "ClinicalDocument")
        assert result.is_clinical_evidence_event is True
        assert result.clinical_event_category == category
        assert result.clinical_event_label == label
        assert result.knowledge_impact == impact


def test_patient_summary_audit_events_are_summary_view_only():
    for action in ["patient_summary_draft_generated", "patient_summary_edited", "patient_summary_reviewed"]:
        result = classify_clinical_evidence_event(action, "PatientClinicalSummary")
        assert result.is_clinical_evidence_event is True
        assert result.knowledge_impact == "summary_view_only"


def test_unknown_or_non_clinical_events_are_not_clinical_evidence():
    unknown = classify_clinical_evidence_event("update", "Appointment")
    assert unknown.is_clinical_evidence_event is False
    assert unknown.clinical_event_category == "other"
    assert unknown.clinical_event_label == "Drugi audit dogadjaj"
    assert unknown.knowledge_impact == "no_official_knowledge_impact"
