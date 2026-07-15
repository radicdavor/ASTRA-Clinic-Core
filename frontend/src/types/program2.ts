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
  patient: { id: number; first_name: string; last_name: string; date_of_birth: string | null; oib: string | null };
  appointment: {
    id: number; service_id: number; provider_id: number; room_id: number; date: string; start_time: string; end_time: string; status: string; source: string;
    service: { id: number; name: string }; provider: { id: number; full_name: string }; room: { id: number; name: string };
  };
  blockers: JourneyBlocker[];
};

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
  items: Array<{ id: number; item_key: string; category: string; label: string; state: string; requires_clinician: boolean; note: string | null; position: number }>;
};

export type PreparationState = {
  id: number; journey_id: number; template_id: number; status: string; requirement_states_json: Record<string, string>;
  template: { id: number; name: string; version: string; requirements_json: Array<{ key: string; label: string }> };
};

export type EncounterDraft = {
  id?: number; status?: string; anamnesis?: string | null; examination?: string | null; patient_findings?: string | null;
  opinion?: string | null; diagnosis?: string | null; recommendations?: string | null; completed_at?: string | null;
};

export type JourneyClosure = {
  journey_id: number; stage: string; consumables_status: string; billing_status: string; payment_status: string;
  invoice: { id?: number; number?: string; total?: string; status?: string } | null; consumables: Array<Record<string, unknown>>;
};

export type AllowedJourneyAction = "open_documents" | "open_arrival" | "open_encounter" | "open_consumables" | "open_billing" | "open_completed";
