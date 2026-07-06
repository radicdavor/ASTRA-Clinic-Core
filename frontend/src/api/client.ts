function defaultApiBaseUrl() {
  if (typeof window === "undefined") return "http://localhost:8000";
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl();
const MUTATION_METHODS = new Set(["POST", "PATCH", "PUT", "DELETE"]);

export type ToastTone = "success" | "error";

export function notifyUser(message: string, tone: ToastTone = "success", title?: string) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent("astra:toast", { detail: { message, tone, title } }));
}

function mutationSuccessMessage(path: string, method: string) {
  const normalizedMethod = method.toUpperCase();
  if (normalizedMethod === "POST" && path === "/api/patients") return "Pacijent je spremljen.";
  if (normalizedMethod === "POST" && path === "/api/appointments") return "Termin je spremljen.";
  if (normalizedMethod === "PATCH" && path.startsWith("/api/appointments/")) return "Status termina je azuriran.";
  if (normalizedMethod === "POST" && path.includes("/complete-with-consumption")) return "Termin je zavrsen i materijal je skinut sa zalihe.";
  if (normalizedMethod === "POST" && path.includes("/draft-invoice")) return "Nacrt racuna je kreiran.";
  if (normalizedMethod === "POST" && path.includes("/issue")) return "Racun je izdan.";
  if (normalizedMethod === "POST" && path.includes("/payments")) return "Uplata je evidentirana.";
  if (normalizedMethod === "POST" && path.includes("/lines")) return "Stavka racuna je dodana.";
  if (normalizedMethod === "POST" && path.includes("/receive")) return "Roba je zaprimljena na zalihu.";
  if (normalizedMethod === "POST" && path === "/api/services") return "Usluga je dodana.";
  if (normalizedMethod === "POST" && path === "/auth/api-keys") return "API kljuc je kreiran.";
  if (normalizedMethod === "PATCH" && path.includes("/deactivate")) return "API kljuc je deaktiviran.";
  if (normalizedMethod === "DELETE") return "Zapis je obrisan.";
  return "Radnja je uspjesno spremljena.";
}

function notifyMutation(path: string, method: string, message: string, tone: ToastTone = "success") {
  if (!MUTATION_METHODS.has(method.toUpperCase())) return;
  notifyUser(message, tone);
}

export function getToken() {
  return localStorage.getItem("astra_token");
}

export function setToken(token: string) {
  localStorage.setItem("astra_token", token);
}

export function clearToken() {
  localStorage.removeItem("astra_token");
}

function handleUnauthorized() {
  clearToken();
  notifyUser("Prijava je istekla ili vise nije valjana. Prijavite se ponovno.", "error", "Potrebna prijava");
  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const method = options.method ?? "GET";
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (response.status === 401) {
    handleUnauthorized();
    throw new Error("Potrebna je ponovna prijava.");
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Greska u komunikaciji s API-jem" }));
    const message = error.detail ?? "Greska u komunikaciji s API-jem";
    notifyMutation(path, method, Array.isArray(message) ? "Radnja nije spremljena. Provjerite unesene podatke." : message, "error");
    throw new Error(message);
  }
  notifyMutation(path, method, mutationSuccessMessage(path, method));
  return response.json();
}

export async function login(email: string, password: string) {
  const result = await api<{ access_token: string; user: unknown }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  setToken(result.access_token);
  return result;
}
