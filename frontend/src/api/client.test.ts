import { beforeEach, describe, expect, test, vi } from "vitest";
import { api, clearSessionState, login, switchDemoPersona } from "./client";

describe("browser session client", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    Object.defineProperty(document, "cookie", { writable: true, value: "astra_csrf=test-csrf" });
    vi.restoreAllMocks();
  });

  test("login uses browser session endpoint and does not store a readable token", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({
      user: { id: 1, name: "Admin", email: "admin@example.com", role: "admin" },
      csrf_token: "test-csrf",
      expires_at: "2026-07-21T20:00:00Z",
    }), { status: 200, headers: { "Content-Type": "application/json" } })));

    await login("admin@example.com", "secret");

    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/auth/browser/login"), expect.objectContaining({ credentials: "include" }));
    expect(sessionStorage.getItem("astra_token")).toBeNull();
    expect(localStorage.getItem("astra_token")).toBeNull();
    expect(localStorage.getItem("astra_user")).toContain("Admin");
  });

  test("api sends cookies, clinic context and CSRF for mutations without Bearer", async () => {
    localStorage.setItem("astra_active_clinic_id", "7");
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } })));

    await api("/api/example", { method: "POST", body: JSON.stringify({ ok: true }) });

    const [, init] = vi.mocked(fetch).mock.calls[0];
    const [url] = vi.mocked(fetch).mock.calls[0];
    const headers = init?.headers as Headers;
    expect(url).toBe(`${window.location.origin}/api/example`);
    expect(init).toEqual(expect.objectContaining({ credentials: "include" }));
    expect(headers.get("X-Clinic-Id")).toBe("7");
    expect(headers.get("X-CSRF-Token")).toBe("test-csrf");
    expect(headers.has("Authorization")).toBe(false);
  });

  test("clearSessionState removes only non-sensitive session presentation state", () => {
    localStorage.setItem("astra_user", "{}");
    localStorage.setItem("astra_active_clinic_id", "1");
    localStorage.setItem("astra_active_clinic_timezone", "Europe/Zagreb");
    localStorage.setItem("astra_demo_persona", "nurse");
    clearSessionState();
    expect(localStorage.getItem("astra_user")).toBeNull();
    expect(localStorage.getItem("astra_active_clinic_id")).toBeNull();
    expect(localStorage.getItem("astra_active_clinic_timezone")).toBeNull();
    expect(localStorage.getItem("astra_demo_persona")).toBeNull();
  });

  test("persona switch replaces presentation context without storing credentials", async () => {
    localStorage.setItem("astra_active_clinic_id", "99");
    localStorage.setItem("astra_active_clinic_timezone", "UTC");
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({
      persona_key: "physician_2",
      user: { id: 22, name: "Liječnik 2", email: "synthetic@example.invalid", role: "demo_physician" },
      csrf_token: "new-csrf",
      expires_at: "2026-07-21T20:00:00Z",
    }), { status: 200, headers: { "Content-Type": "application/json" } })));

    await switchDemoPersona("physician_2");

    const [, init] = vi.mocked(fetch).mock.calls[0];
    expect(init).toEqual(expect.objectContaining({ method: "POST", credentials: "include" }));
    expect((init?.headers as Headers).get("X-CSRF-Token")).toBe("test-csrf");
    expect(localStorage.getItem("astra_active_clinic_id")).toBeNull();
    expect(localStorage.getItem("astra_active_clinic_timezone")).toBeNull();
    expect(localStorage.getItem("astra_demo_persona")).toBe("physician_2");
    expect(localStorage.getItem("astra_user")).toContain("Liječnik 2");
    expect(JSON.stringify(localStorage)).not.toContain("new-csrf");
  });
});
