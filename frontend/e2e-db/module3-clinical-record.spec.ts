import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

type Seed = {
  password: string;
  users: { receptionA: string; physicianA: string; physicianB: string; nurseA: string; foreignPhysician: string };
  clinics: { a: number; b: number; foreign: number };
  patients: { shared: number };
  clinical: { signedDocument: number; signedReport: number; ownDraft: number; unclassifiedSource: number; financialSource: number; clinicBInvoice: number };
};

const seedPath = process.env.ASTRA_E2E_SEED_FILE;
if (!seedPath) throw new Error("ASTRA_E2E_SEED_FILE is required for DB-backed E2E tests.");
const seed = JSON.parse(readFileSync(seedPath, "utf-8")) as Seed;

async function login(page: Page, email: string, clinicId: number) {
  await page.goto("/login");
  await page.getByLabel(/E-po/).fill(email);
  await page.getByLabel("Lozinka").fill(seed.password);
  await page.getByRole("button", { name: "Prijava" }).click();
  const picker = page.getByLabel("Aktivna klinika");
  if (await picker.count()) await picker.selectOption(String(clinicId));
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
      return { status: response.status, body: await response.json().catch(() => null) };
    },
    { path, options, backendUrl: process.env.ASTRA_E2E_BACKEND_URL ?? "http://127.0.0.1:8011" },
  ) as Promise<{ status: number; body: unknown }>;
}

test("DB-backed physician reads same-institution report, edits own draft and preserves signed snapshot", async ({ page }) => {
  await login(page, seed.users.physicianA, seed.clinics.a);

  const record = await api(page, `/api/patients/${seed.patients.shared}/clinical-record`);
  expect(record.status).toBe(200);
  expect(JSON.stringify(record.body)).toContain(`"document_id":${seed.clinical.signedDocument}`);
  expect(JSON.stringify(record.body)).toContain(`"document_id":${seed.clinical.ownDraft}`);
  expect(JSON.stringify(record.body)).not.toContain(`"document_id":${seed.clinical.financialSource}`);
  expect(JSON.stringify(record.body)).not.toContain("ORIGINAL_CONTENT");

  await page.goto(`/clinical-documents/${seed.clinical.signedDocument}`);
  await expect(page.getByRole("heading", { name: "E2E potpisani nalaz Clinic B" })).toBeVisible();
  await expect(page.getByLabel("Postojeće dopune dokumenta").getByText("E2E odvojena dopuna")).toBeVisible();
  await expect(page.getByText("Spremi dopunu", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Spremi tekst" })).toHaveCount(0);

  const report = await api(page, `/api/signed-reports/${seed.clinical.signedReport}`);
  expect(report.status).toBe(200);
  expect(JSON.stringify(report.body)).toContain("ORIGINAL_CONTENT");
  expect(JSON.stringify(report.body)).not.toContain("CHANGED_CONTENT");

  const addendum = await api(page, `/api/signed-reports/${seed.clinical.signedReport}/addenda`, {
    method: "POST",
    body: JSON.stringify({ reason: "E2E browser dopuna", content: "Nova odvojena dopuna iz preglednika." }),
  });
  expect(addendum.status).toBe(200);
  expect((addendum.body as { signed_report_id?: number }).signed_report_id).toBe(seed.clinical.signedReport);
  await page.reload();
  await expect(page.getByLabel("Postojeće dopune dokumenta").getByText("Nova odvojena dopuna iz preglednika.")).toBeVisible();

  await page.goto(`/clinical-documents/${seed.clinical.ownDraft}`);
  const rawText = page.getByLabel("Izvorni tekst dokumenta");
  await expect(rawText).toHaveValue("E2E DRAFT ORIGINAL");
  await rawText.fill("E2E DRAFT SAVED BY AUTHOR");
  await page.getByText("Spremi tekst", { exact: true }).click();
  await page.reload();
  await expect(page.getByLabel("Izvorni tekst dokumenta")).toHaveValue("E2E DRAFT SAVED BY AUTHOR");
});

test("DB-backed nurse reads report without edit actions and foreign physician is denied", async ({ page }) => {
  await login(page, seed.users.nurseA, seed.clinics.a);
  await page.goto(`/clinical-documents/${seed.clinical.signedDocument}`);
  await expect(page.getByRole("heading", { name: "E2E potpisani nalaz Clinic B" })).toBeVisible();
  await expect(page.getByLabel("Izvorni tekst dokumenta")).toHaveValue("ORIGINAL_CONTENT");
  await expect(page.getByRole("button", { name: "Spremi tekst" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Spremi dopunu" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Pokreni AI ekstrakciju" })).toHaveCount(0);

  const nursePatch = await api(page, `/api/clinical-documents/${seed.clinical.ownDraft}`, {
    method: "PATCH",
    body: JSON.stringify({ title: "Nedopuštena sestrinska izmjena" }),
  });
  expect(nursePatch.status).toBe(403);

  await page.getByTitle("Odjava").click();
  await login(page, seed.users.foreignPhysician, seed.clinics.foreign);
  const foreignRead = await api(page, `/api/clinical-documents/${seed.clinical.signedDocument}`);
  expect(foreignRead.status).toBe(404);
  expect(JSON.stringify(foreignRead.body)).not.toContain("ORIGINAL_CONTENT");
});

test("DB-backed reception cannot read PHI and another physician cannot edit the author's draft", async ({ page }) => {
  await login(page, seed.users.receptionA, seed.clinics.a);
  const receptionRead = await api(page, `/api/clinical-documents/${seed.clinical.signedDocument}`);
  expect(receptionRead.status).toBe(403);
  expect(JSON.stringify(receptionRead.body)).not.toContain("ORIGINAL_CONTENT");
  await page.goto(`/clinical-documents/${seed.clinical.signedDocument}`);
  await expect(page.getByText("ORIGINAL_CONTENT")).toHaveCount(0);

  await page.getByTitle("Odjava").click();
  await login(page, seed.users.physicianB, seed.clinics.b);
  const otherPhysicianPatch = await api(page, `/api/clinical-documents/${seed.clinical.ownDraft}`, {
    method: "PATCH",
    body: JSON.stringify({ title: "Nedopuštena izmjena drugog liječnika" }),
  });
  expect(otherPhysicianPatch.status).toBe(403);
});

test("DB-backed source classification is one-way and clinical read does not open billing", async ({ page }) => {
  await login(page, seed.users.physicianA, seed.clinics.a);

  const unclassifiedRead = await api(page, `/api/clinical-documents/${seed.clinical.unclassifiedSource}`);
  const financialRead = await api(page, `/api/clinical-documents/${seed.clinical.financialSource}`);
  const billingRead = await api(page, `/api/invoices/${seed.clinical.clinicBInvoice}`);
  expect(unclassifiedRead.status).toBe(403);
  expect(financialRead.status).toBe(403);
  expect(billingRead.status).toBe(403);

  const classified = await api(page, `/api/clinical-documents/${seed.clinical.unclassifiedSource}/classification/review`, {
    method: "POST",
    body: JSON.stringify({ record_classification: "clinical", note: "E2E ljudski pregled" }),
  });
  expect(classified.status).toBe(200);
  expect((await api(page, `/api/clinical-documents/${seed.clinical.unclassifiedSource}`)).status).toBe(200);
  const reclassified = await api(page, `/api/clinical-documents/${seed.clinical.unclassifiedSource}/classification/review`, {
    method: "POST",
    body: JSON.stringify({ record_classification: "financial" }),
  });
  expect(reclassified.status).toBe(409);
});
