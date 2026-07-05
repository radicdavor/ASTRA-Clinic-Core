export type Patient = {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
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
};

export type Supplier = { id: number; name: string; contact_person?: string; email?: string; phone?: string };
export type AuditLog = { id: number; action: string; entity_type: string; entity_id?: number; summary?: string; created_at: string };
