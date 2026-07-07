export type Patient = {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  oib?: string;
  email?: string;
  phone?: string;
  notes?: string;
};

export type Service = {
  id: number;
  name: string;
  code?: string;
  duration_minutes: number;
  price: string;
  module_id?: number;
  active: boolean;
};

export type Clinic = { id: number; name: string; active: boolean };
export type Provider = { id: number; full_name: string; specialty?: string; staff_role?: string; clinic_id?: number | null; clinic?: Clinic | null };
export type Room = { id: number; name: string; type?: string; clinic_id?: number | null; clinic?: Clinic | null };
export type Module = { id: number; key: string; name: string; description?: string; enabled: boolean };

export type ClinicalEpisode = {
  id: number;
  patient_id: number;
  title: string;
  episode_type: string;
  status: string;
  priority?: string;
  start_date: string;
  end_date?: string;
  summary?: string;
  clinical_notes?: string;
  owner_provider_id?: number;
  created_by?: number;
  created_at: string;
  updated_at?: string;
  patient?: Patient;
  owner_provider?: Provider;
  appointment_count?: number;
};

export type ClinicalPlan = {
  id: number;
  episode_id: number;
  source: string;
  status: string;
  proposed_episode_status?: string | null;
  next_action: string;
  due_date?: string | null;
  priority: string;
  rationale?: string | null;
  suggested_follow_up?: string | null;
  physician_conclusion?: string | null;
  ai_confidence?: string | null;
  physician_confirmed: boolean;
  confirmed_by?: number | null;
  confirmed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type ClinicalDecisionTimelineItem = {
  id: number;
  action: string;
  label: string;
  summary?: string | null;
  source?: string | null;
  created_at: string;
};

export type ClinicalDocument = {
  id: number;
  patient_id: number;
  source_type: string;
  document_type: string;
  origin?: string | null;
  document_date?: string | null;
  title: string;
  author?: string | null;
  institution?: string | null;
  raw_text?: string | null;
  ai_summary?: string | null;
  key_findings?: string[] | null;
  recommendations?: string[] | null;
  ai_extraction_status: "not_run" | "generated" | "edited" | "accepted" | "rejected" | "superseded";
  ai_extraction_generated_at?: string | null;
  ai_extraction_updated_at?: string | null;
  physician_reviewed: boolean;
  review_status: "draft" | "extracted" | "needs_physician_review" | "reviewed" | "rejected" | "superseded";
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  attachment_path?: string | null;
  appointment_id?: number | null;
  patient?: Patient;
  created_at: string;
  updated_at: string;
};

export type PatientKnowledgeSource = {
  document_id: number;
  title: string;
  document_type: string;
  source_type: string;
  origin?: string | null;
  document_date?: string | null;
};

export type PatientKnowledgeItem = {
  text: string;
  sources: PatientKnowledgeSource[];
  display_kind?: string | null;
  severity?: string | null;
  requires_attention: boolean;
};

export type PatientClinicalSummaryRecord = {
  id: number;
  patient_id: number;
  summary_text?: string | null;
  known_conditions?: string[] | null;
  key_findings?: string[] | null;
  open_items?: string[] | null;
  risks?: string[] | null;
  last_recommendations?: string[] | null;
  source_document_ids?: number[] | null;
  status: "draft_ai" | "needs_review" | "reviewed" | "stale" | "rejected" | "superseded";
  generated_by?: string | null;
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type PatientClinicalSummary = {
  patient_id: number;
  generated_from_reviewed_documents: number;
  awaiting_review_count: number;
  reviewed_summary?: PatientClinicalSummaryRecord | null;
  draft_summary?: PatientClinicalSummaryRecord | null;
  reviewed_summary_is_stale: boolean;
  draft_summary_is_stale: boolean;
  latest_reviewed_document_updated_at?: string | null;
  reviewed_summary_updated_at?: string | null;
  summary_warning?: string | null;
  known_problems: PatientKnowledgeItem[];
  completed_procedures: PatientKnowledgeItem[];
  pathology: PatientKnowledgeItem[];
  laboratory: PatientKnowledgeItem[];
  imaging: PatientKnowledgeItem[];
  current_therapy: PatientKnowledgeItem[];
  open_questions: PatientKnowledgeItem[];
  latest_recommendations: PatientKnowledgeItem[];
};

export type Appointment = {
  id: number;
  patient_id: number;
  episode_id?: number | null;
  service_id: number;
  provider_id: number;
  room_id: number;
  date: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  status: string;
  source: string;
  notes?: string;
  arrived_at?: string | null;
  identity_verified_at?: string | null;
  identity_verified_by?: number | null;
  patient?: Patient;
  service?: Service;
  provider?: Provider;
  room?: Room;
  episode?: ClinicalEpisode | null;
};

export type ReceptionSlot = {
  time: string;
  appointment?: Appointment | null;
  span: number;
  empty: boolean;
};

export type InventoryItem = {
  id: number;
  sku: string;
  name: string;
  category?: string;
  unit_of_measure: string;
  current_stock: string;
  minimum_stock: string;
  reorder_point: string;
  purchase_price: string;
  selling_price: string;
  lot_tracking_enabled?: boolean;
  expiration_tracking_enabled?: boolean;
};

export type Supplier = { id: number; name: string; contact_person?: string; email?: string; phone?: string };
export type AuditLog = {
  id: number;
  action: string;
  entity_type: string;
  entity_id?: number;
  summary?: string;
  actor_type?: string;
  actor_user_id?: number;
  actor_api_key_id?: number;
  request_id?: string;
  before_json?: Record<string, unknown> | null;
  after_json?: Record<string, unknown> | null;
  created_at: string;
};
export type StockMovement = { id: number; inventory_item_id: number; related_appointment_id?: number; movement_type: string; quantity: string; reason?: string; created_at: string; item?: InventoryItem };
export type StockLocation = { id: number; name: string; type: string };
export type PurchaseOrderLine = { id: number; purchase_order_id: number; inventory_item_id: number; quantity_ordered: string; quantity_received: string; unit_price: string; vat_rate: string };
export type PurchaseOrder = { id: number; status: string; order_date: string; expected_delivery_date?: string; total_amount: string; supplier?: Supplier; lines: PurchaseOrderLine[] };
export type InvoiceLine = { id: number; invoice_id: number; description: string; quantity: string; unit_price: string; vat_rate: string; total: string };
export type PaymentTransaction = { id: number; invoice_id: number; amount: string; method: string; reference?: string; paid_at?: string };
export type Invoice = { id: number; patient_id?: number; appointment_id?: number; invoice_number: string; invoice_date: string; status: string; payment_status: string; total_amount: string; fiscalization_status?: string; fiscalization_provider?: string; fiscalization_message?: string; lines: InvoiceLine[]; payments: PaymentTransaction[] };
export type ApiKey = { id: number; name: string; scopes: string[]; active: boolean; expires_at?: string; last_used_at?: string; created_at: string };
export type DecisionImpact = "none" | "review" | "blocks_demo" | "blocks_release";
export type ReadinessCheck = { key: string; label: string; status: "ok" | "warning" | "critical"; message: string; count?: number | null; action?: string | null; target_path?: string | null; target_label?: string | null; decision_impact: DecisionImpact; severity_reason?: string | null };
export type Readiness = {
  status: "ready_for_demo" | "attention_needed" | "blocked";
  demo_mode: boolean;
  real_data_allowed: boolean;
  fiscalization_mode: string;
  summary: { ok: number; warning: number; critical: number };
  checks: ReadinessCheck[];
};
