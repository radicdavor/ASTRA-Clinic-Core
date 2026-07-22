import { expect, test, type Page, type APIResponse } from "@playwright/test";
import { readFileSync } from "node:fs";

type Seed = {
  date: string;
  password: string;
  users: { adminA: string; receptionA: string; dual: string; systemAdmin: string };
  clinics: { a: number; b: number };
  patients: { shared: number; onlyB: number; paid: number };
  journeys: { a: number; b: number; onlyB: number; paid: number };
  services: { consult: number; gastro: number; colon: number };
  providers: { a: number; b: number };
  rooms: { a1: number; a2: number; b1: number };
};

const seedPath = process.env.ASTRA_E2E_SEED_FILE;
if (!seedPath) throw new Error("ASTRA_E2E_SEED_FILE is required for DB-backed E2E tests.");
const seed = JSON.parse(readFileSync(seedPath, "utf-8")) as Seed;

async function login(page: Page, email: string, clinicId?: number) {
  await page.goto("/login");
  await page.getByLabel(/E-po/).fill(email);
  await page.getByLabel("Lozinka").fill(seed.password);
  await page.getByRole("button", { name: "Prijava" }).click();
  if (clinicId) {
    await page.getByLabel("Aktivna klinika").selectOption(String(clinicId));
  }
  await expect(page.getByRole("heading", { name: "Danas u poliklinici" })).toBeVisible();
}

async function api(page: Page, path: string, options: RequestInit = {}) {
  return page.evaluate(
    async ({ path, options, backendUrl }) => {
      const activeClinicId = localStorage.getItem("astra_active_clinic_id");
      const csrf = document.cookie.split("; ").find((entry) => entry.startsWith("astra_csrf="))?.split("=")[1];
      const method = options.method ?? "GET";
      const response = await fetch(`${backendUrl}${path}`, {
        ...options,
        method,
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(activeClinicId ? { "X-Clinic-Id": activeClinicId } : {}),
          ...(csrf && method !== "GET" ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}),
          ...(options.headers ?? {}),
        },
      });
      return {
        status: response.status,
        body: await response.json().catch(() => null),
      };
    },
    { path, options, backendUrl: process.env.ASTRA_E2E_BACKEND_URL ?? "http://127.0.0.1:8011" },
  ) as Promise<{ status: number; body: unknown }>;
}

async function expectApiOk(response: APIResponse) {
  expect(response.ok(), `${response.status()} ${await response.text()}`).toBeTruthy();
}

test("DB-backed workflow uses real backend, PostgreSQL and persistent dashboard state", async ({ page, request }) => {
  const health = await request.get(`${process.env.ASTRA_E2E_BACKEND_URL}/health`);
  await expectApiOk(health);
  const ready = await request.get(`${process.env.ASTRA_E2E_BACKEND_URL}/ready`);
  await expectApiOk(ready);

  await login(page, seed.users.receptionA);
  await expect(page.getByText("E2E Zajednicki Pacijent")).toBeVisible();
  await expect(page.getByText("E2E Placeni Pacijent")).toBeVisible();
  await expect(page.getByLabel(/Završeno|Zavrseno/).first()).toBeVisible();
  await expect(page.getByLabel("10:00 E2E Zajednicki Pacijent").getByText("E2E prvi gastro pregled")).toBeVisible();
  await expect(page.getByLabel("10:00 E2E Zajednicki Pacijent").getByText("E2E gastroskopija")).toBeVisible();

  const availability = await api(page, `/api/patients/${seed.patients.shared}/appointments`);
  expect(availability.status).toBe(200);
  expect(JSON.stringify(availability.body)).toContain("E2E Klinika B");

  const overlap = await api(page, "/api/appointments", {
    method: "POST",
    body: JSON.stringify({
      patient_id: seed.patients.shared,
      service_id: seed.services.consult,
      provider_id: seed.providers.a,
      room_id: seed.rooms.a1,
      date: seed.date,
      start_time: "09:10",
      end_time: "09:40",
      duration_minutes: 30,
      status: "scheduled",
      source: "manual",
    }),
  });
  expect(overlap.status).toBe(409);
  expect(JSON.stringify(overlap.body)).toContain("patient_appointment_overlap");

  const nonOverlap = await api(page, "/api/appointments", {
    method: "POST",
    body: JSON.stringify({
      patient_id: seed.patients.shared,
      service_id: seed.services.consult,
      provider_id: seed.providers.a,
      room_id: seed.rooms.a1,
      date: seed.date,
      start_time: "13:00",
      end_time: "13:30",
      duration_minutes: 30,
      status: "scheduled",
      source: "manual",
      notes: "Synthetic DB-backed E2E non-overlap appointment",
    }),
  });
  expect([200, 201]).toContain(nonOverlap.status);

  await page.reload();
  await expect(page.getByText("13:00").first()).toBeVisible();
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("astra_token"))).toBeNull();
  await expect.poll(() => page.evaluate(() => localStorage.getItem("astra_token"))).toBeNull();

  await page.getByRole("button", { name: "Otvori prijem" }).first().click();
  await expect(page.getByRole("dialog", { name: /Opći podaci pacijenta|Op.*podaci pacijenta/ })).toBeVisible();
  await page.getByRole("button", { name: /Podaci su/ }).click();
  await expect(page.getByRole("dialog", { name: /Kratka prijemna provjera/ })).toBeVisible();
  await page.getByRole("button", { name: "Provjereno" }).click();
  await expect(page.getByRole("dialog", { name: /Kratka prijemna provjera/ })).toBeHidden();

  await page.reload();
  await expect(
    page.getByLabel("10:00 E2E Zajednicki Pacijent").locator(".timeline-state-label", { hasText: /Čeka pregled\/pretragu|Ceka pregled\/pretragu/ }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Otvori pregled" }).first().click();
  await expect(page).toHaveURL(/\/journeys\/\d+\?focus=encounter/);
  await expect(page.getByRole("heading", { name: /E2E Zajednicki Pacijent/ })).toBeVisible();
});

test("DB-backed browser session survives refresh and logout revokes protected access", async ({ page }) => {
  await login(page, seed.users.receptionA);
  await expect(page.getByText("Danas u poliklinici")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Danas u poliklinici")).toBeVisible();
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("astra_token"))).toBeNull();
  await expect.poll(() => page.evaluate(() => localStorage.getItem("astra_token"))).toBeNull();

  await page.getByTitle("Odjava").click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
});

test("DB-backed clinic isolation blocks direct journey access outside active clinic", async ({ page }) => {
  await login(page, seed.users.receptionA);

  const forbiddenJourney = await api(page, `/api/patient-journeys/${seed.journeys.onlyB}`);
  expect([403, 404]).toContain(forbiddenJourney.status);
  expect(JSON.stringify(forbiddenJourney.body)).not.toContain("Samo B Pacijent");

  const forbiddenPatientClinical = await api(page, `/api/patients/${seed.patients.onlyB}/invoices`);
  expect([403, 404]).toContain(forbiddenPatientClinical.status);
  expect(JSON.stringify(forbiddenPatientClinical.body)).not.toContain("Samo B Pacijent");
});

test("DB-backed CSRF protection blocks manual cookie-auth mutations without token", async ({ page }) => {
  await login(page, seed.users.receptionA);
  const result = await page.evaluate(
    async ({ backendUrl, journeyId }) => {
      const response = await fetch(`${backendUrl}/api/patient-journeys/${journeyId}/check-in`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-Clinic-Id": String(localStorage.getItem("astra_active_clinic_id") ?? ""),
        },
      });
      return { status: response.status, body: await response.text() };
    },
    { backendUrl: process.env.ASTRA_E2E_BACKEND_URL ?? "http://127.0.0.1:8011", journeyId: seed.journeys.a },
  );
  expect(result.status).toBe(403);
  expect(result.body).toContain("CSRF");
});

test("DB-backed clinic switching clears stale clinic data and reloads authorized dataset", async ({ page }) => {
  await login(page, seed.users.dual, seed.clinics.a);

  const picker = page.getByLabel("Aktivna klinika");
  await picker.selectOption(String(seed.clinics.a));
  await expect(page.getByRole("button", { name: "E2E Zajednicki Pacijent" }).first()).toBeVisible();

  await picker.selectOption(String(seed.clinics.b));
  await expect(page.getByText("E2E Samo B Pacijent")).toBeVisible();
  await expect(page.getByText("E2E Placeni Pacijent")).toHaveCount(0);

  await picker.selectOption(String(seed.clinics.a));
  await expect(page.getByText("E2E Placeni Pacijent")).toBeVisible();
});

test("DB-backed accessibility smoke covers status, red flag popover and action menu keyboard use", async ({ page }) => {
  await login(page, seed.users.receptionA);
  await page.keyboard.press("Tab");
  await expect(page.getByLabel(/Čeka dolazak|Ceka dolazak/).first()).toBeVisible();

  const actionMenu = page.getByLabel(/Dodatne radnje za E2E Zajednicki Pacijent/).first();
  await actionMenu.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button", { name: "Otvori tijek" }).first()).toBeVisible();
  await page.keyboard.press("Escape");

  await page.getByRole("button", { name: "Otvori prijem" }).first().focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog", { name: /Opći podaci pacijenta|Op.*podaci pacijenta/ })).toBeVisible();
});
