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

export type Provider = { id: number; full_name: string; specialty?: string };
export type Room = { id: number; name: string; type?: string };
export type Module = { id: number; key: string; name: string; description?: string; enabled: boolean };

export type Appointment = {
  id: number;
  patient_id: number;
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
  patient?: Patient;
  service?: Service;
  provider?: Provider;
  room?: Room;
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
export type ReadinessCheck = { key: string; label: string; status: "ok" | "warning" | "critical"; message: string; count?: number | null; action?: string | null; target_path?: string | null; target_label?: string | null };
export type Readiness = {
  status: "ready_for_demo" | "attention_needed" | "blocked";
  demo_mode: boolean;
  real_data_allowed: boolean;
  fiscalization_mode: string;
  summary: { ok: number; warning: number; critical: number };
  checks: ReadinessCheck[];
};
