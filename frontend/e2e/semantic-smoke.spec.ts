import { expect, test, type Page } from "@playwright/test";

type Persona = {
  key: "admin" | "receptionist" | "nurse" | "physician_1" | "physician_2";
  role: "admin" | "receptionist" | "nurse" | "physician";
  clinicId: number;
  clinicName: string;
  visibleNavigation: string;
  hiddenNavigation: string;
};

const personas: Persona[] = [
  { key: "admin", role: "admin", clinicId: 1, clinicName: "Sintetička klinika A", visibleNavigation: "Administracija", hiddenNavigation: "Klinički rad" },
  { key: "receptionist", role: "receptionist", clinicId: 1, clinicName: "Sintetička klinika A", visibleNavigation: "Prijem", hiddenNavigation: "Klinički rad" },
  { key: "nurse", role: "nurse", clinicId: 1, clinicName: "Sintetička klinika A", visibleNavigation: "Klinička podrška", hiddenNavigation: "Sigurnost" },
  { key: "physician_1", role: "physician", clinicId: 1, clinicName: "Sintetička klinika A", visibleNavigation: "Klinički rad", hiddenNavigation: "Sigurnost" },
  { key: "physician_2", role: "physician", clinicId: 2, clinicName: "Sintetička klinika B", visibleNavigation: "Klinički rad", hiddenNavigation: "Sigurnost" },
];

async function installSemanticMocks(page: Page, persona: Persona) {
  await page.addInitScript(({ role, key, clinicId }) => {
    localStorage.setItem("astra_user", JSON.stringify({
      id: clinicId,
      name: `Sintetička ${key}`,
      email: `${key}@example.invalid`,
      role,
    }));
    localStorage.setItem("astra_demo_persona", key);
    localStorage.setItem("astra_active_clinic_id", String(clinicId));
    localStorage.setItem("astra_active_clinic_timezone", "Europe/Zagreb");
  }, persona);

  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (!url.pathname.startsWith("/api") && !url.pathname.startsWith("/auth")) {
      return route.fallback();
    }
    const json = (body: unknown, status = 200) => route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
    if (url.pathname === "/auth/session") {
      return json({
        user: {
          id: persona.clinicId,
          name: `Sintetička ${persona.key}`,
          email: `${persona.key}@example.invalid`,
          role: persona.role,
        },
        csrf_token: "synthetic-csrf",
        expires_at: "2026-07-23T20:00:00Z",
      });
    }
    if (url.pathname === "/auth/me/clinics") {
      return json({
        clinics: [{ id: persona.clinicId, name: persona.clinicName, timezone: "Europe/Zagreb" }],
        default_clinic_id: persona.clinicId,
        requires_selection: false,
      });
    }
    if (url.pathname === "/api/public-config") {
      return json({
        app_name: "ASTRA Clinic Core",
        demo_mode: true,
        real_data_allowed: false,
        demo_persona_switcher_enabled: true,
        warnings: ["Sintetičko evaluacijsko okruženje."],
      });
    }
    if (url.pathname === "/api/dashboard/day") {
      const receptionAction = persona.role === "receptionist" ? ["open_check_in"] : [];
      return json({
        date: "2026-07-23",
        refreshed_at: "2026-07-23T08:00:00Z",
        visible_sections: [],
        viewer_role: persona.role,
        scope: "clinic",
        scope_label: persona.clinicName,
        scoped_clinician_id: null,
        can_filter_clinician: persona.role === "admin",
        available_clinics: [{ id: persona.clinicId, name: persona.clinicName }],
        rows: [{
          journey_id: persona.clinicId,
          appointment_id: persona.clinicId,
          time: "09:00:00",
          patient_id: persona.clinicId,
          patient_name: `Sintetički pacijent ${persona.clinicId}`,
          patient_date_of_birth: "1990-01-01",
          service_id: 1,
          service_name: "Sintetički pregled",
          clinician_id: persona.role === "physician" ? persona.clinicId : null,
          clinician_name: persona.role === "physician" ? `Liječnik ${persona.clinicId}` : null,
          room_id: persona.clinicId,
          room_name: `Ordinacija ${persona.clinicId}`,
          clinic_id: persona.clinicId,
          clinic_name: persona.clinicName,
          intake_channel: "manual",
          workflow_stage: "ready_for_arrival",
          document_status: "complete",
          preparation_status: "complete",
          arrival_status: "not_arrived",
          check_in_status: "not_arrived",
          encounter_status: "not_started",
          consumables_status: "not_ready",
          billing_status: "not_ready",
          payment_status: "not_due",
          blocker_status: "clear",
          operational_status: "waiting_arrival",
          operational_status_label: "Čeka dolazak",
          operational_status_severity: "neutral",
          operational_status_reasons: [{ code: "not_arrived", label: "Pacijent još nije stigao." }],
          blocker_labels: [],
          blockers: [],
          allowed_actions: receptionAction,
          reception_warning: false,
          reception_warning_details: [],
          activity_count: 1,
          current_activity_id: 1,
          next_activity_id: null,
          activities: [{
            id: 1,
            sequence: 1,
            time: "09:00:00",
            end_time: "09:30:00",
            service_name: "Sintetički pregled",
            clinician_name: persona.role === "physician" ? `Liječnik ${persona.clinicId}` : null,
            room_name: `Ordinacija ${persona.clinicId}`,
            status: "ready",
          }],
        }],
      });
    }
    if (["/api/providers", "/api/rooms", "/api/services"].includes(url.pathname)) return json([]);
    return json([]);
  });
}

for (const persona of personas) {
  test(`${persona.key} uses a semantic role and clinic contract`, async ({ page }) => {
    await installSemanticMocks(page, persona);
    const sessionResponse = page.waitForResponse((response) => response.url().includes("/auth/session"));
    await page.goto("/");
    expect((await sessionResponse).status()).toBe(200);

    await expect(page.getByRole("heading", { name: "Danas u poliklinici" })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Glavna navigacija" })).toBeVisible();
    await expect(page.getByLabel("Demo prikaz uloge")).toHaveValue(persona.key);
    await expect(page.getByLabel("Aktivna klinika")).toHaveValue(String(persona.clinicId));
    await expect(page.getByText(persona.visibleNavigation, { exact: true })).toBeVisible();
    await expect(page.getByText(persona.hiddenNavigation, { exact: true })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: /Klinički kontekst/i })).toHaveCount(0);

    if (persona.role === "receptionist") {
      await expect(page.getByRole("button", { name: "Otvori prijem" })).toBeVisible();
    } else {
      await expect(page.getByRole("button", { name: "Otvori prijem" })).toHaveCount(0);
    }
  });
}
