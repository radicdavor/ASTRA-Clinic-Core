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

export type ClinicalReadinessPreviewItem = {
  key: string;
  label: string;
  category: string;
  status: string;
  severity: string;
  responsible_role?: string | null;
  source_type: string;
  source_ref?: string | null;
  source_label?: string | null;
  suggested_action?: string | null;
  blocking: boolean;
  override_allowed: boolean;
  override_role?: string | null;
  override_reason_required: boolean;
  audit_required: boolean;
};

export type ClinicalReadinessPreview = {
  appointment_id: number;
  patient_id?: number | null;
  service_id?: number | null;
  template_key?: string | null;
  template_label?: string | null;
  template_version?: string | null;
  template_version_warning?: string | null;
  template_binding_status: string;
  template_binding_warning?: string | null;
  snapshot_supported: boolean;
  snapshot_status: string;
  snapshot_warning: string;
  status: string;
  is_preview: boolean;
  generated_at: string;
  summary: string;
  items: ClinicalReadinessPreviewItem[];
  source_warnings: string[];
  limitations: string[];
};

export type ClinicalReadinessSnapshotHistoryItem = {
  id: number;
  appointment_id: number;
  patient_id: number;
  service_id: number;
  created_at: string;
  created_by_user_id: number;
  schema_version: string;
  preview_generated_at: string;
  preview_status: string;
  template_key?: string | null;
  template_label?: string | null;
  template_version?: string | null;
  template_binding_status?: string | null;
  snapshot_reason: string;
  is_preview_snapshot: boolean;
  disclaimer: string;
  item_count: number;
  limitation_count: number;
  source_warning_count: number;
  superseded_by_snapshot_id?: number | null;
  superseded_at?: string | null;
  superseded_reason?: string | null;
};

export type ClinicalReadinessSnapshotHistoryResponse = {
  appointment_id: number;
  snapshots: ClinicalReadinessSnapshotHistoryItem[];
  count: number;
  is_preview_history: boolean;
  warning: string;
};

export type ClinicalReadinessSnapshotCaptureRequest = {
  reason: string;
  client_preview_generated_at?: string | null;
  idempotency_key?: string | null;
};

export type ClinicalReadinessSnapshotResponse = {
  id: number;
  appointment_id: number;
  patient_id: number;
  service_id: number;
  created_at: string;
  created_by_user_id: number;
  schema_version: string;
  preview_generated_at: string;
  preview_status: string;
  template_key?: string | null;
  template_label?: string | null;
  template_version?: string | null;
  template_binding_status?: string | null;
  snapshot_reason: string;
  is_preview_snapshot: boolean;
  disclaimer: string;
  items: ClinicalReadinessPreviewItem[];
  limitations: string[];
  source_warnings: string[];
  source_refs: Record<string, unknown>[];
};

export type ClinicalReadinessSnapshotDetailResponse = ClinicalReadinessSnapshotResponse & {
  preview_summary: string;
  template_binding_warning?: string | null;
  superseded_by_snapshot_id?: number | null;
  superseded_at?: string | null;
  superseded_reason?: string | null;
  warning: string;
};

export type ClinicalReadinessSnapshotSupersedeRequest = {
  reason: string;
};

export type ClinicalReadinessSnapshotSupersedeResponse = {
  old_snapshot_id: number;
  new_snapshot: ClinicalReadinessSnapshotResponse;
  superseded_at: string;
  superseded_reason: string;
  warning: string;
};

export type ClinicalReadinessAcknowledgmentReadItem = {
  id: number;
  acknowledgment_key: string;
  appointment_id: number;
  patient_id: number;
  advisory_signal_key: string;
  snapshot_id?: number | null;
  actor_user_id: number;
  actor_role: string;
  reason: string;
  limitations: string[];
  schema_version: string;
  created_at: string;
  safe_disclaimer: string;
  is_decision: boolean;
  is_clearance: boolean;
  is_override: boolean;
};

export type ClinicalReadinessAcknowledgmentListResponse = {
  appointment_id: number;
  acknowledgments: ClinicalReadinessAcknowledgmentReadItem[];
  count: number;
  is_read_only: boolean;
  warning: string;
};

export type ClinicalReadinessAcknowledgmentDetailResponse = ClinicalReadinessAcknowledgmentReadItem & {
  warning: string;
};

export type ClinicalFindingReadItem = {
  id: number;
  finding_key: string;
  patient_id: number;
  source_type: string;
  source_label: string;
  source_reference: string;
  source_document_id?: number | null;
  label: string;
  category: string;
  lifecycle_status: string;
  requires_review: boolean;
  reviewed_at?: string | null;
  reviewed_by_user_id?: number | null;
  limitations: string[];
  schema_version: string;
  created_at: string;
  updated_at: string;
  safe_disclaimer: string;
};

export type ClinicalFindingListResponse = {
  patient_id: number;
  findings: ClinicalFindingReadItem[];
  count: number;
  is_read_only: boolean;
  warning: string;
};

export type ClinicalFindingDetailResponse = ClinicalFindingReadItem & {
  warning: string;
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
export type ClinicalEvidenceTimelineItem = {
  id: number;
  action: string;
  object_type: string;
  object_id?: number;
  message?: string;
  actor_type?: string;
  actor_user_id?: number;
  actor_api_key_id?: number;
  created_at: string;
  clinical_event_category: string;
  clinical_event_label: string;
  knowledge_impact: "no_official_knowledge_impact" | "may_enable_official_knowledge" | "removed_from_official_knowledge" | "summary_view_only" | string;
  is_clinical_evidence_event: boolean;
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
