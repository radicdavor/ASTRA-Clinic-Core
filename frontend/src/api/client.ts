function defaultApiBaseUrl() {
  if (typeof window === "undefined") return "http://localhost:8000";
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl();
const MUTATION_METHODS = new Set(["POST", "PATCH", "PUT", "DELETE"]);

function notifyMutation(method: string, message: string, tone: "success" | "error" = "success") {
  if (typeof window === "undefined") return;
  if (!MUTATION_METHODS.has(method.toUpperCase())) return;
  window.dispatchEvent(new CustomEvent("astra:toast", { detail: { message, tone } }));
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

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Greška u komunikaciji s API-jem" }));
    const message = error.detail ?? "Greška u komunikaciji s API-jem";
    notifyMutation(options.method ?? "GET", Array.isArray(message) ? "Radnja nije spremljena. Provjerite unesene podatke." : message, "error");
    throw new Error(message);
  }
  notifyMutation(options.method ?? "GET", "Radnja je uspjesno spremljena.");
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
