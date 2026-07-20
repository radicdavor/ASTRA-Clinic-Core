export type JourneyStage = "requested" | "booked" | "awaiting_forms" | "awaiting_documents" | "preparation_in_progress" | "ready_for_arrival" | "arrived" | "check_in_review" | "ready_for_clinician" | "in_encounter" | "procedure_completed" | "awaiting_billing" | "awaiting_payment" | "completed" | "cancelled" | "no_show" | "blocked";
export type JourneyStageKey = "documents" | "arrival" | "encounter" | "consumables" | "billing" | "completed";

export type JourneyBlocker = {
  id: number; blocker_key: string; category: string; title: string; details: string | null;
  is_clinical: boolean; status: string; resolution_note: string | null;
};

export type PatientJourneyDetail = {
  id: number; patient_id: number; appointment_id: number; intake_channel: string; current_stage: JourneyStage;
  document_status: string; preparation_status: string; check_in_status: string; encounter_status: string;
  consumables_status: string; billing_status: string; payment_status: string; closed_at: string | null;
  patient: { id: number; first_name: string; last_name: string; date_of_birth: string | null; oib: string | null; email: string | null; phone?: string | null; notes?: string | null; email_verified_at: string | null };
  appointment: {
    id: number; service_id: number; provider_id: number; room_id: number; date: string; start_time: string; end_time: string; status: string; source: string;
    service: { id: number; name: string }; provider: { id: number; full_name: string }; room: { id: number; name: string };
  };
  blockers: JourneyBlocker[];
  activities: JourneyActivity[];
};

export type JourneyActivity = {
  id: number; journey_id: number; appointment_id: number | null; service_id: number; activity_key: string;
  activity_kind: string; specialty_key: string; clinic_id: number | null; primary_provider_id: number | null;
  room_id: number | null; sequence: number; depends_on_activity_id: number | null; required: boolean;
  planned_start: string; planned_end: string; actual_start: string | null; actual_end: string | null; status: string;
  not_performed_reason: string | null; form_resolution_status: string; billing_status: string; consumables_status: string;
};

export type ClinicalFormField = { field_key: string; label: string; type: string; required?: boolean; help_text?: string | null; options?: Array<string | { value: string; label: string }>; item_fields?: ClinicalFormField[]; max_items?: number };
export type ClinicalFormSection = { section_key: string; title?: string; fields: ClinicalFormField[] };
export type ClinicalFormInstance = {
  id: number; activity_id: number; form_version_id: number; purpose: string; status: string; data_json: Record<string, unknown>;
  rendered_summary: string | null; completed_by: number | null; signed_by: number | null; completed_at: string | null;
  signed_at: string | null; amended_from_instance_id: number | null; binding_source: string; resolved_at: string;
  revision_number: number; updated_at: string;
  form_version: { id: number; definition_id: number; version: number; status: string; sections_json: ClinicalFormSection[]; output_document_type: string };
};

export type SignedClinicalReport = {
  id: number; form_instance_id: number; form_version_id: number; clinical_document_id: number;
  activity_id: number; journey_id: number; patient_id: number; document_type: string; title: string;
  structured_data_json: Record<string, unknown>; rendered_content: string; version_number: number;
  signer_user_id: number; signer_name: string; signed_at: string; supersedes_report_id: number | null; superseded_at: string | null; content_hash: string; hash_algorithm: string;
};
export type ReportDelivery = { id: number; report_id: number; channel: string; recipient: string; status: string; provider_mode: string; queued_at: string; sent_at: string | null; delivered_at: string | null; failure_reason: string | null; correlation_id: string; recipient_source: string; alternate_recipient_reason: string | null };
export type VisitDocument = { report: SignedClinicalReport; print_count: number; latest_delivery: ReportDelivery | null };
export type PathologySpecimen = { id: number; specimen_label: string; anatomical_site: string; specimen_type: string; container: string | null; fixation: string | null };
export type PathologyCase = { id: number; source_activity_id: number; status: string; external_lab: string | null; external_case_number: string | null; sent_at: string | null; lab_received_at: string | null; result_received_at: string | null; reviewed_at: string | null; patient_notified_at: string | null; communication_disposition: string | null; communication_note: string | null; communication_attempts: number; specimens: PathologySpecimen[] };
export type ProcedureIntervention = { id: number; activity_id: number; intervention_type: string; anatomical_site: string | null; description: string | null; technique: string | null; size: string | null; count: number; retrieval_status: string | null; complication: string | null };

export type PatientJourneyTimelineItem = {
  date: string; event_type: string; title: string; summary: string | null; source_url: string | null;
  provenance: Record<string, unknown>; review_state: string | null; journey_id: number;
};

export type SummaryFact = {
  id: number; statement: string; fact_type: string; source_document_id: number | null;
  confidence: string | null; limitation: string | null; review_status: string;
};

export type PatientJourneySummary = {
  id: number; journey_id: number; provider: string; model_name: string; status: string;
  content_json: Record<string, unknown>; source_refs_json: unknown[]; limitations_json: string[];
  generated_at: string; facts: SummaryFact[];
};

export type CheckInState = {
  id: number; journey_id: number; status: string; arrived_at: string | null; completed_at: string | null;
  items: Array<{
    id: number; item_key: string; category: string; label: string; state: string; requires_clinician: boolean; note: string | null; position: number;
    details_json?: Record<string, unknown>; activity_ids_json?: number[];
    medical_disposition?: string | null; medical_disposition_note?: string | null; medical_reviewed_at?: string | null;
  }>;
};

export type PreparationState = {
  id: number; journey_id: number; template_id: number; status: string; requirement_states_json: Record<string, string>;
  template: { id: number; name: string; version: string; requirements_json: Array<{ key: string; label: string }> };
};

export type ActivityPreparationState = {
  journey_id: number;
  contradictions: string[];
  requirements: Array<{
    requirement_key: string; label: string; patient_instruction: string; category: string; required: boolean;
    state: string; contradictory: boolean;
    activities: Array<{ activity_id: number; sequence: number; activity_key: string; service_name: string; requirement_id: number; state: string }>;
  }>;
};

export type EncounterDraft = {
  id?: number; status?: string; anamnesis?: string | null; examination?: string | null; patient_findings?: string | null;
  opinion?: string | null; diagnosis?: string | null; recommendations?: string | null; completed_at?: string | null;
};

export type AIDiagnosisSuggestion = {
  code: string; title: string; provider: "openai"; model: string; request_id: string;
};

export type PublicPilotConfig = {
  ai_diagnosis_suggestions?: { enabled: boolean; configured: boolean; catalog_available: boolean; reason: string | null };
};

export type JourneyClosure = {
  journey_id: number; stage: string; consumables_status: string; billing_status: string; payment_status: string;
  invoice: { id?: number; number?: string; total?: string; status?: string } | null; consumables: Array<Record<string, unknown>>;
};

export type AllowedJourneyAction = "open_documents" | "open_arrival" | "open_encounter" | "open_consumables" | "open_billing" | "open_completed";
