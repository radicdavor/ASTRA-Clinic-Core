import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

type Seed = { password: string; users: { receptionA: string; adminA: string; identityReviewer: string }; clinics: { a: number }; patients: { foreign: number } };
const seedPath = process.env.ASTRA_E2E_SEED_FILE;
if (!seedPath) throw new Error("ASTRA_E2E_SEED_FILE is required");
const seed = JSON.parse(readFileSync(seedPath, "utf-8")) as Seed;

async function login(page: Page, email: string, clinicId?: number) {
  await page.goto("/login");
  await page.getByLabel(/E-po/).fill(email);
  await page.getByLabel("Lozinka").fill(seed.password);
  await page.getByRole("button", { name: "Prijava" }).click();
  await page.waitForURL((url) => url.pathname !== "/login");
  if (clinicId) {
    await page.getByLabel("Aktivna klinika").selectOption(String(clinicId));
    const dialog = page.getByRole("dialog", { name: "Promijeniti aktivnu kliniku?" });
    if (await dialog.isVisible()) await dialog.getByRole("button", { name: "Promijeni kliniku" }).click();
  }
}

async function switchUser(page: Page, email: string, clinicId?: number) {
  await page.context().clearCookies();
  await page.goto("/login");
  await page.evaluate(() => localStorage.clear());
  await login(page, email, clinicId);
}

async function api(page: Page, path: string, method = "GET", body?: unknown) {
  return page.evaluate(async ({ path, method, body, backendUrl }) => {
    const csrf = document.cookie.split("; ").find((entry) => entry.startsWith("astra_csrf="))?.split("=")[1];
    const clinic = localStorage.getItem("astra_active_clinic_id");
    const response = await fetch(`${backendUrl}${path}`, { method, credentials: "include", headers: { "Content-Type": "application/json", ...(clinic ? { "X-Clinic-Id": clinic } : {}), ...(csrf && method !== "GET" ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}) }, body: body ? JSON.stringify(body) : undefined });
    return { status: response.status, body: await response.json().catch(() => null) };
  }, { path, method, body, backendUrl: process.env.ASTRA_E2E_BACKEND_URL ?? "http://127.0.0.1:8011" });
}

test("opaque requester flow requires explicit review before clinic access", async ({ page }) => {
  await login(page, seed.users.receptionA, seed.clinics.a);
  const collision = await api(page, "/api/patients", "POST", { first_name: "E2E", last_name: "Druga Ustanova Pacijent", date_of_birth: "1990-01-02", email: "e2e.patient.foreign@example.com" });
  expect(collision.status).toBe(202);
  const requestId = (collision.body as { request_id: string }).request_id;
  const distinctCollision = await api(page, "/api/patients", "POST", { first_name: "E2E", last_name: "Distinct Candidate", date_of_birth: "1990-01-02", email: "e2e.patient.distinct@example.com" });
  const rejectedCollision = await api(page, "/api/patients", "POST", { first_name: "E2E", last_name: "Rejected Candidate", date_of_birth: "1990-01-02", email: "e2e.patient.rejected@example.com" });
  expect(distinctCollision.status).toBe(202);
  expect(rejectedCollision.status).toBe(202);
  const distinctId = (distinctCollision.body as { request_id: string }).request_id;
  const rejectedId = (rejectedCollision.body as { request_id: string }).request_id;
  expect(JSON.stringify(collision.body)).not.toContain("candidate");
  await page.goto(`/patient-identity-reconciliations/${requestId}`);
  await expect(page.getByRole("heading", { name: "Kontrolirani pregled identiteta" })).toBeVisible();
  await expect(page.getByText("Pacijent nije stvoren niti povezan automatski.")).toBeVisible();
  expect((await api(page, `/api/patients/${seed.patients.foreign}`)).status).toBe(404);

  await switchUser(page, seed.users.adminA, seed.clinics.a);
  expect((await api(page, "/api/patient-identity-reconciliations/review/pending")).status).toBe(403);

  await switchUser(page, seed.users.identityReviewer);
  await page.goto("/patient-identity-reconciliation-review");
  await page.getByRole("button", { name: new RegExp(requestId) }).click();
  await expect(page.getByRole("region", { name: "Minimalna usporedba identiteta" })).toBeVisible();
  await page.getByLabel(/Obrazlo/).fill("Synthetic browser evidence confirms the identity");
  await page.getByRole("button", { name: "Odobri povezivanje" }).click();
  await expect(page.getByRole("button", { name: new RegExp(requestId) })).toHaveCount(0);
  await page.getByRole("button", { name: new RegExp(distinctId) }).click();
  await page.getByLabel(/Obrazlo/).fill("Synthetic browser evidence confirms a distinct person");
  await page.getByRole("button", { name: "Potvrdi da je druga osoba" }).click();
  await expect(page.getByRole("button", { name: new RegExp(distinctId) })).toHaveCount(0);
  await page.getByRole("button", { name: new RegExp(rejectedId) }).click();
  await page.getByLabel(/Obrazlo/).fill("Synthetic browser evidence is insufficient");
  await page.getByRole("button", { name: /Odbij/ }).click();
  await expect(page.getByText("Nema otvorenih zahtjeva.")).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await switchUser(page, seed.users.receptionA, seed.clinics.a);
  expect((await api(page, `/api/patients/${seed.patients.foreign}`)).status).toBe(200);
  await page.goto(`/patient-identity-reconciliations/${requestId}`);
  await page.getByRole("button", { name: /Osvje/ }).click();
  await expect(page.getByText("Povezivanje s klinikom je odobreno")).toBeVisible();
  const distinctStatus = await api(page, `/api/patient-identity-reconciliations/${distinctId}`);
  const rejectedStatus = await api(page, `/api/patient-identity-reconciliations/${rejectedId}`);
  expect((distinctStatus.body as { status: string; result_patient_id: number }).status).toBe("confirmed_distinct");
  expect((distinctStatus.body as { result_patient_id: number }).result_patient_id).toBeTruthy();
  expect((rejectedStatus.body as { status: string; result_patient_id: null }).status).toBe("rejected_insufficient_evidence");
  expect((rejectedStatus.body as { result_patient_id: null }).result_patient_id).toBeNull();
});
