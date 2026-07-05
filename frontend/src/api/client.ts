const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
    throw new Error(error.detail ?? "Greška u komunikaciji s API-jem");
  }
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
