import { expect, test, type Page } from "@playwright/test";

const patientOne = {
  id: 501,
  first_name: "Sintetički 01",
  last_name: "Pacijent",
  date_of_birth: "1992-01-06",
  oib: null,
  email: "synthetic01@example.com",
  phone: "0994477445",
  notes: null,
  email_verified_at: null,
  updated_at: "2026-07-19T08:00:00Z",
};

const patientTwo = {
  ...patientOne,
  id: 502,
  first_name: "Sintetički 02",
  email: "synthetic02@example.com",
};

const activity = {
  id: 301,
  journey_id: 1,
  appointment_id: 101,
  service_id: 1,
  activity_key: "Demo gastroskopija",
  activity_kind: "procedure",
  specialty_key: "gastroenterology",
  clinic_id: 1,
  primary_provider_id: 1,
  room_id: 1,
  sequence: 1,
  depends_on_activity_id: null,
  required: true,
  planned_start: "2026-07-19T07:30:00",
  planned_end: "2026-07-19T08:00:00",
  actual_start: null,
  actual_end: null,
  status: "ready",
  not_performed_reason: null,
  form_resolution_status: "not_started",
  billing_status: "not_ready",
  consumables_status: "not_ready",
};

const appointment = {
  id: 101,
  service_id: 1,
  provider_id: 1,
  room_id: 1,
  date: "2026-07-19",
  start_time: "07:30:00",
  end_time: "08:00:00",
  status: "booked",
  source: "manual",
  service: { id: 1, name: "Demo gastroskopija" },
  provider: { id: 1, full_name: "dr. Demo Gastro" },
  room: { id: 1, name: "Demo ordinacija 1" },
};

function dashboardRow(id: number, patientName: string, overrides: Record<string, unknown> = {}) {
  return {
    journey_id: id,
    appointment_id: 100 + id,
    time: id === 1 ? "07:30:00" : "08:30:00",
    patient_id: 500 + id,
    patient_name: patientName,
    patient_date_of_birth: "1992-01-06",
    service_id: 1,
    service_name: "Demo gastroskopija",
    clinician_id: 1,
    clinician_name: "dr. Demo Gastro",
    room_id: 1,
    room_name: "Demo ordinacija 1",
    clinic_id: 1,
    clinic_name: "Demo klinika",
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
    operational_status_reasons: [{ code: "patient_not_arrived", label: "Pacijent još nije stigao." }],
    blocker_labels: [],
    blockers: [],
    allowed_actions: ["open_check_in"],
    reception_warning: false,
    reception_warning_details: [],
    activity_count: 1,
    current_activity_id: id === 1 ? 301 : 302,
    next_activity_id: null,
    activities: [{ id: id === 1 ? 301 : 302, sequence: 1, time: id === 1 ? "07:30:00" : "08:30:00", end_time: id === 1 ? "08:00:00" : "09:00:00", service_name: "Demo gastroskopija", clinician_name: "dr. Demo Gastro", room_name: "Demo ordinacija 1", status: "ready" }],
    ...overrides,
  };
}

function journey(id: number) {
  const patient = id === 1 ? patientOne : patientTwo;
  return {
    id,
    patient_id: patient.id,
    appointment_id: 100 + id,
    intake_channel: "manual",
    current_stage: id === 1 ? "ready_for_arrival" : "ready_for_clinician",
    document_status: "complete",
    preparation_status: "complete",
    check_in_status: id === 1 ? "not_arrived" : "ready",
    encounter_status: "not_started",
    consumables_status: "not_ready",
    billing_status: "not_ready",
    payment_status: "not_due",
    closed_at: null,
    blockers: [],
    activities: [{ ...activity, id: id === 1 ? 301 : 302, journey_id: id, appointment_id: 100 + id }],
    patient,
    appointment: { ...appointment, id: 100 + id, start_time: id === 1 ? "07:30:00" : "08:30:00" },
  };
}

async function installApiMocks(page: Page) {
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (!url.pathname.startsWith("/api") && !url.pathname.startsWith("/auth")) return route.fallback();

    const json = (body: unknown, status = 200) => route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(body),
    });

    if (url.pathname === "/api/public-config") return json({ demo_mode: true, real_data_allowed: false, warnings: ["Demo/development okruženje - ne unositi stvarne podatke pacijenata."] });
    if (url.pathname === "/auth/session") return json({ user: { id: 1, name: "Admin", email: "admin@example.com", role: "admin" }, csrf_token: "mock-csrf", expires_at: "2026-07-19T20:00:00Z" });
    if (url.pathname === "/auth/me/clinics") return json({ clinics: [{ id: 1, name: "Demo klinika", timezone: "Europe/Zagreb" }], default_clinic_id: 1, requires_selection: false });
    if (url.pathname === "/api/dashboard/day") return json({
      date: "2026-07-19",
      refreshed_at: "2026-07-19T07:00:00Z",
      visible_sections: [],
      viewer_role: "admin",
      scope: "all",
      scope_label: "Svi liječnici",
      scoped_clinician_id: null,
      can_filter_clinician: true,
      available_clinics: [{ id: 1, name: "Demo klinika" }],
      rows: [
        dashboardRow(1, "Sintetički 01 Pacijent"),
        dashboardRow(2, "Sintetički 02 Pacijent", {
          workflow_stage: "ready_for_clinician",
          arrival_status: "arrived",
          check_in_status: "ready",
          operational_status: "ready_for_clinician",
          operational_status_label: "Čeka pregled/pretragu",
          operational_status_severity: "active",
          operational_status_reasons: [{ code: "checkin_ready", label: "Prijem je završen." }],
          allowed_actions: ["open_encounter"],
        }),
      ],
    });
    if (url.pathname === "/api/providers") return json([{ id: 1, full_name: "dr. Demo Gastro", staff_role: "physician" }]);
    if (url.pathname === "/api/rooms") return json([{ id: 1, name: "Demo ordinacija 1", clinic_id: 1 }]);
    if (url.pathname === "/api/services") return json([{ id: 1, name: "Demo gastroskopija" }]);
    if (url.pathname === "/api/inventory/items") return json([]);
    if (url.pathname === "/api/patient-journeys/1") return json(journey(1));
    if (url.pathname === "/api/patient-journeys/2") return json(journey(2));
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/timeline$/)) return json([]);
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/summary$/)) return json(null);
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/check-in$/)) {
      if (request.method() === "POST") return json({ id: 1, journey_id: 1, status: "in_review", arrived_at: "2026-07-19T07:30:00Z", completed_at: null, items: [] });
      return json({ id: 1, journey_id: Number(url.pathname.split("/")[3]), status: "not_arrived", arrived_at: null, completed_at: null, items: [] });
    }
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/check-in\/complete-reception$/)) return json({ id: 1, journey_id: 1, status: "ready", arrived_at: "2026-07-19T07:30:00Z", completed_at: "2026-07-19T07:40:00Z", items: [] });
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/preparation$/)) return json({ status: "complete", requirements: [] });
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/activity-preparation$/)) return json({ requirements: [], projection: [] });
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/encounter$/)) return json({ anamnesis: "", examination: "", patient_findings: "", opinion: "", recommendations: "", diagnoses: [] });
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/activities\/\d+\/form$/) && request.method() === "GET") return json({ detail: "Obrazac nije otvoren." }, 404);
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/activities\/\d+\/interventions$/) && request.method() === "GET") return json([]);
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/closure$/)) return json({ can_close: false, blockers: [], invoice: null });
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/visit-documents$/)) return json([]);
    if (url.pathname.match(/^\/api\/patient-journeys\/\d+\/pathology-cases$/)) return json([]);
    if (url.pathname === "/api/clinical-documents") return json([]);
    return json({}, 200);
  });
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("astra_user", JSON.stringify({ id: 1, name: "Admin", email: "admin@example.com", role: "admin" }));
    window.localStorage.setItem("astra_active_clinic_id", "1");
    window.localStorage.setItem("astra_active_clinic_timezone", "Europe/Zagreb");
  });
  await installApiMocks(page);
});

test("daily dashboard supports floating reception and canonical clinical workspace", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Danas u poliklinici" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Sintetički 01 Pacijent" })).toBeVisible();
  await expect(page.getByLabel(/Čeka dolazak/).first()).toBeVisible();

  await page.getByRole("button", { name: "Otvori prijem" }).first().click();
  await expect(page.getByRole("dialog", { name: /Opći podaci pacijenta/ })).toBeVisible();
  await page.getByRole("button", { name: /Podaci su/ }).click();
  const receptionChecklist = page.getByRole("dialog", { name: /Kratka prijemna provjera/ });
  await expect(receptionChecklist).toBeVisible();

  await receptionChecklist.getByRole("checkbox", { name: /Problem s postom/ }).check();
  await expect(page.getByText(/Post od 6 sati nije potvrđen/)).toBeVisible();
  await page.getByRole("button", { name: "Provjereno" }).click();
  await expect(page.getByRole("dialog", { name: /Kratka prijemna provjera/ })).toBeHidden();

  await page.getByRole("button", { name: "Otvori pregled" }).click();
  await expect(page).toHaveURL(/\/journeys\/2\?focus=encounter/);
  await expect(page.getByRole("heading", { name: "Sintetički 02 Pacijent" })).toBeVisible();
});

test("daily dashboard keeps the page within a 1024px viewport and scrolls its timeline internally", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Danas u poliklinici" })).toBeVisible();

  const dimensions = await page.evaluate(() => {
    const timeline = document.querySelector<HTMLElement>(".clinic-timeline");
    return {
      pageWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
      timelineClientWidth: timeline?.clientWidth ?? 0,
      timelineScrollWidth: timeline?.scrollWidth ?? 0,
    };
  });
  expect(dimensions.pageWidth).toBeLessThanOrEqual(dimensions.viewportWidth);
  expect(dimensions.timelineClientWidth).toBeGreaterThan(0);
  expect(dimensions.timelineScrollWidth).toBeGreaterThanOrEqual(dimensions.timelineClientWidth);
  await expect(page.getByRole("button", { name: "Otvori prijem" }).first()).toBeVisible();
});
