import type { ClinicalEvidenceTimelineListResponse, ClinicalFindingDetailResponse, ClinicalFindingListResponse, ClinicalReadinessAcknowledgmentDetailResponse, ClinicalReadinessAcknowledgmentListResponse, ClinicalReadinessSnapshotCaptureRequest, ClinicalReadinessSnapshotDetailResponse, ClinicalReadinessSnapshotHistoryResponse, ClinicalReadinessSnapshotResponse, ClinicalReadinessSnapshotSupersedeRequest, ClinicalReadinessSnapshotSupersedeResponse } from "../types";

function defaultApiBaseUrl() {
  if (typeof window === "undefined") return "http://localhost:8000";
  if (import.meta.env.DEV) return window.location.origin;
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl();
const MUTATION_METHODS = new Set(["POST", "PATCH", "PUT", "DELETE"]);

export type ToastTone = "success" | "error";

export type ApiValidationDetail = {
  code?: string;
  message?: string;
  errors?: Array<{ field_key?: string; label?: string; message?: string }>;
  fields?: Array<{ field_key?: string; label?: string; message?: string }>;
  actual_instance_id?: number;
  actual_revision_number?: number;
  current_updated_at?: string | null;
  server_data?: Record<string, unknown>;
};

export type ApiRequestOptions = RequestInit & { suppressErrorToast?: boolean };

export class ApiError extends Error {
  constructor(message: string, public readonly detail: unknown, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

export function notifyUser(message: string, tone: ToastTone = "success", title?: string) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent("astra:toast", { detail: { message, tone, title } }));
}

function mutationSuccessMessage(path: string, method: string) {
  const normalizedMethod = method.toUpperCase();
  if (normalizedMethod === "PATCH" && path.endsWith("/form")) return "Skica spremljena";
  if (normalizedMethod === "POST" && path.endsWith("/form/complete")) return "Obrazac dovršen";
  if (normalizedMethod === "POST" && path === "/api/patients") return "Pacijent je spremljen.";
  if (normalizedMethod === "POST" && path === "/api/appointments") return "Termin je spremljen.";
  if (normalizedMethod === "POST" && path === "/api/workflow-tasks") return "Zadatak je spremljen.";
  if (normalizedMethod === "PATCH" && path.startsWith("/api/workflow-tasks/")) return "Zadatak je azuriran.";
  if (normalizedMethod === "POST" && path.includes("/checklist/")) return "Checklista je azurirana.";
  if (normalizedMethod === "POST" && path === "/api/episodes") return "Epizoda je spremljena.";
  if (normalizedMethod === "POST" && path === "/api/clinical-documents/upload") return "Klinicki dokument je spremljen.";
  if (normalizedMethod === "POST" && path === "/api/clinical-documents") return "Klinicki dokument je spremljen.";
  if (normalizedMethod === "PATCH" && path.startsWith("/api/clinical-documents/")) return "Klinicki dokument je azuriran.";
  if (normalizedMethod === "POST" && path.includes("/extract")) return "AI prijedlog sazetka je pripremljen.";
  if (normalizedMethod === "POST" && path.includes("/review")) return "Dokument je oznacen kao pregledan.";
  if (normalizedMethod === "POST" && path.includes("/reject-summary")) return "AI prijedlog je odbijen.";
  if (normalizedMethod === "POST" && path.includes("/mark-arrived")) return "Dolazak pacijenta je evidentiran.";
  if (normalizedMethod === "POST" && path.endsWith("/check-in")) return "Prijemna provjera je otvorena.";
  if (normalizedMethod === "PATCH" && path.startsWith("/api/episodes/")) return "Epizoda je azurirana.";
  if (normalizedMethod === "POST" && path.includes("/close")) return "Epizoda je zatvorena.";
  if (normalizedMethod === "POST" && path.includes("/clinical-plans/generate")) return "AI prijedlog plana je pripremljen.";
  if (normalizedMethod === "PATCH" && path.startsWith("/api/clinical-plans/")) return "Prijedlog plana je uredjen.";
  if (normalizedMethod === "POST" && path.includes("/confirm")) return "Klinicki plan je potvrdjen.";
  if (normalizedMethod === "POST" && path.includes("/reject")) return "AI prijedlog plana je odbijen.";
  if (normalizedMethod === "PATCH" && path.startsWith("/api/appointments/")) return "Status termina je azuriran.";
  if (normalizedMethod === "POST" && path.includes("/complete-with-consumption")) return "Termin je zavrsen i materijal je skinut sa zalihe.";
  if (normalizedMethod === "POST" && path.includes("/draft-invoice")) return "Nacrt racuna je kreiran.";
  if (normalizedMethod === "POST" && path.includes("/issue")) return "Racun je izdan.";
  if (normalizedMethod === "POST" && path.includes("/payments")) return "Uplata je evidentirana.";
  if (normalizedMethod === "POST" && path.includes("/lines")) return "Stavka racuna je dodana.";
  if (normalizedMethod === "POST" && path.includes("/receive")) return "Roba je zaprimljena na zalihu.";
  if (normalizedMethod === "POST" && path === "/api/services") return "Usluga je dodana.";
  if (normalizedMethod === "POST" && path === "/api/clinics") return "Klinika je dodana.";
  if (normalizedMethod === "POST" && path === "/api/rooms") return "Prostorija je dodana.";
  if (normalizedMethod === "POST" && path === "/api/providers") return "Liječnik je dodan.";
  if (normalizedMethod === "POST" && path === "/auth/api-keys") return "API kljuc je kreiran.";
  if (normalizedMethod === "PATCH" && path.includes("/deactivate")) return "API kljuc je deaktiviran.";
  if (normalizedMethod === "DELETE") return "Zapis je obrisan.";
  return "Radnja je uspjesno spremljena.";
}

function notifyMutation(path: string, method: string, message: string, tone: ToastTone = "success") {
  if (!MUTATION_METHODS.has(method.toUpperCase())) return;
  notifyUser(message, tone);
}

function apiErrorMessage(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const entry = detail as ApiValidationDetail;
    const fieldMessages = (entry.fields ?? entry.errors ?? [])
      .map(error => error.label && error.message ? `${error.label}: ${error.message}` : error.message ?? null)
      .filter((message): message is string => Boolean(message));
    if (fieldMessages.length) return fieldMessages.join(" ");
    if (entry.message) return entry.message;
  }
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      if (!item || typeof item !== "object") return null;
      const entry = item as { msg?: string; loc?: Array<string | number> };
      const field = entry.loc?.[entry.loc.length - 1];
      return entry.msg ? `${field ? `${field}: ` : ""}${entry.msg}` : null;
    }).filter(Boolean);
    if (messages.length) return messages.join(" ");
  }
  return "Radnja nije spremljena. Provjerite unesene podatke.";
}

export function getToken() {
  return localStorage.getItem("astra_token");
}

export function setToken(token: string) {
  localStorage.setItem("astra_token", token);
}

export type SessionUser = { id: number; name: string; email: string; role: string };

export function setSessionUser(user: SessionUser) {
  localStorage.setItem("astra_user", JSON.stringify(user));
}

export function getSessionUser(): SessionUser | null {
  try {
    const value = localStorage.getItem("astra_user");
    if (value) return JSON.parse(value) as SessionUser;

    // Existing sessions created before role-aware navigation do not have
    // astra_user yet. The decoded role is presentation-only; API RBAC remains
    // authoritative for every protected operation.
    const token = localStorage.getItem("astra_token");
    if (!token) return null;
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))) as { sub?: string; role?: string };
    if (!payload.role) return null;
    return { id: Number(payload.sub) || 0, name: "", email: "", role: payload.role };
  } catch {
    return null;
  }
}

export function clearToken() {
  localStorage.removeItem("astra_token");
  localStorage.removeItem("astra_user");
}

function handleUnauthorized() {
  clearToken();
  notifyUser("Prijava je istekla ili vise nije valjana. Prijavite se ponovno.", "error", "Potrebna prijava");
  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

export async function api<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { suppressErrorToast = false, ...requestOptions } = options;
  const headers = new Headers(requestOptions.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const method = requestOptions.method ?? "GET";
  const response = await fetch(`${API_BASE_URL}${path}`, { ...requestOptions, headers });
  if (response.status === 401) {
    handleUnauthorized();
    throw new Error("Potrebna je ponovna prijava.");
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Greska u komunikaciji s API-jem" }));
    const message = apiErrorMessage(error.detail);
    if (!suppressErrorToast) notifyMutation(path, method, message, "error");
    throw new ApiError(message, error.detail, response.status);
  }
  notifyMutation(path, method, mutationSuccessMessage(path, method));
  return response.json();
}

export async function login(email: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Prijava nije uspjela" }));
    throw new Error(error.detail ?? "Prijava nije uspjela");
  }
  const result = await response.json() as { access_token: string; user: SessionUser };
  setToken(result.access_token);
  setSessionUser(result.user);
  return result;
}

export async function getClinicalReadinessSnapshotHistory(appointmentId: number) {
  return api<ClinicalReadinessSnapshotHistoryResponse>(`/api/appointments/${appointmentId}/clinical-readiness-snapshots`);
}

export async function captureClinicalReadinessSnapshot(appointmentId: number, request: ClinicalReadinessSnapshotCaptureRequest) {
  return api<ClinicalReadinessSnapshotResponse>(`/api/appointments/${appointmentId}/clinical-readiness-snapshots`, {
    method: "POST",
    body: JSON.stringify(request)
  });
}

export async function getClinicalReadinessSnapshotDetail(appointmentId: number, snapshotId: number) {
  return api<ClinicalReadinessSnapshotDetailResponse>(`/api/appointments/${appointmentId}/clinical-readiness-snapshots/${snapshotId}`);
}

export async function supersedeClinicalReadinessSnapshot(appointmentId: number, snapshotId: number, request: ClinicalReadinessSnapshotSupersedeRequest) {
  return api<ClinicalReadinessSnapshotSupersedeResponse>(`/api/appointments/${appointmentId}/clinical-readiness-snapshots/${snapshotId}/supersede`, {
    method: "POST",
    body: JSON.stringify(request)
  });
}

export async function getClinicalReadinessAcknowledgments(appointmentId: number) {
  return api<ClinicalReadinessAcknowledgmentListResponse>(`/api/appointments/${appointmentId}/clinical-readiness/acknowledgments`);
}

export async function getClinicalReadinessAcknowledgmentDetail(appointmentId: number, acknowledgmentId: number) {
  return api<ClinicalReadinessAcknowledgmentDetailResponse>(`/api/appointments/${appointmentId}/clinical-readiness/acknowledgments/${acknowledgmentId}`);
}

export async function getClinicalFindings(patientId: number) {
  return api<ClinicalFindingListResponse>(`/api/patients/${patientId}/clinical-findings`);
}

export async function getClinicalFindingDetail(patientId: number, findingId: number) {
  return api<ClinicalFindingDetailResponse>(`/api/patients/${patientId}/clinical-findings/${findingId}`);
}

export async function getClinicalEvidenceTimeline(patientId: number) {
  return api<ClinicalEvidenceTimelineListResponse>(`/api/patients/${patientId}/clinical-evidence-timeline`);
}
