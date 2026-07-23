import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

type PersonaKey = "admin" | "receptionist" | "nurse" | "physician_1" | "physician_2";
type Seed = {
  password: string;
  personas: Record<PersonaKey, string>;
  clinics: { a: number; b: number };
};

const seedPath = process.env.ASTRA_E2E_SEED_FILE;
if (!seedPath) throw new Error("ASTRA_E2E_SEED_FILE is required for DB-backed E2E tests.");
const seed = JSON.parse(readFileSync(seedPath, "utf-8")) as Seed;

async function loginController(page: Page) {
  await page.goto("/login");
  await page.getByLabel(/E-po/).fill(seed.personas.admin);
  await page.getByLabel("Lozinka").fill(seed.password);
  await page.getByRole("button", { name: "Prijava" }).click();
  await expect(page.getByLabel("Demo prikaz uloge")).toHaveValue("admin");
}

async function selectClinic(page: Page, clinicId: number) {
  const picker = page.getByLabel("Aktivna klinika");
  if (await picker.inputValue() !== String(clinicId)) {
    await picker.selectOption(String(clinicId));
    const confirmation = page.getByRole("dialog", { name: "Promijeniti aktivnu kliniku?" });
    if (await confirmation.isVisible()) {
      await confirmation.getByRole("button", { name: "Promijeni kliniku" }).click();
    }
  }
  await expect.poll(() => page.evaluate(() => localStorage.getItem("astra_active_clinic_id"))).toBe(String(clinicId));
}

async function switchPersonaAndWaitForStableContext(
  page: Page,
  persona: PersonaKey,
  expectedClinicId?: number,
) {
  const sessionResponse = page.waitForResponse((response) => (
    response.url().endsWith("/auth/demo/persona-session")
    && response.request().method() === "POST"
  ));
  await page.getByLabel("Demo prikaz uloge").selectOption(persona);
  const dialog = page.getByRole("dialog", { name: "Promijeniti demo ulogu?" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Promijeni demo ulogu" }).click();
  expect((await sessionResponse).status()).toBe(200);

  await page.waitForURL((url) => url.pathname === "/");
  await expect(page.getByLabel("Demo prikaz uloge")).toHaveValue(persona);
  if (expectedClinicId) {
    await expect(page.getByRole("heading", { name: "Danas u poliklinici" })).toBeVisible();
    await expect(page.getByLabel("Aktivna klinika")).toHaveValue(String(expectedClinicId));
    await expect.poll(() => page.evaluate(() => localStorage.getItem("astra_active_clinic_id"))).toBe(String(expectedClinicId));
  } else {
    await expect(page.getByRole("heading", { name: "Odaberite aktivnu kliniku" })).toBeVisible();
    await expect(page.getByLabel("Aktivna klinika")).toHaveValue("");
    await expect.poll(() => page.evaluate(() => localStorage.getItem("astra_active_clinic_id"))).toBeNull();
  }

  const session = await page.evaluate(async (backendUrl) => {
    const response = await fetch(`${backendUrl}/auth/session`, { credentials: "include" });
    return { status: response.status, body: await response.json() };
  }, process.env.ASTRA_E2E_BACKEND_URL);
  expect(session.status).toBe(200);
  expect(session.body.user.email).toBe(seed.personas[persona]);
}

test("five demo personas switch real sessions, clinics and permitted navigation", async ({ page }) => {
  await loginController(page);
  await selectClinic(page, seed.clinics.a);

  await switchPersonaAndWaitForStableContext(page, "receptionist", seed.clinics.a);
  await expect(page.getByRole("link", { name: "Prijem" })).toBeVisible();
  await expect(page.getByText("Sigurnost", { exact: true })).toHaveCount(0);

  await switchPersonaAndWaitForStableContext(page, "nurse", seed.clinics.a);
  await expect(page.getByText(/Klinička podrška/)).toBeVisible();
  await expect(page.getByRole("link", { name: /API klju/ })).toHaveCount(0);

  await switchPersonaAndWaitForStableContext(page, "physician_1", seed.clinics.a);
  await expect(page.getByText(/Klinički rad/)).toBeVisible();
  await expect(page.getByText("E2E Zajednicki Pacijent").first()).toBeVisible();
  await expect(page.getByText("E2E Samo B Pacijent")).toHaveCount(0);

  await switchPersonaAndWaitForStableContext(page, "physician_2", seed.clinics.b);
  await expect(page.getByText("E2E Samo B Pacijent")).toBeVisible();
  await expect(page.getByText("E2E Placeni Pacijent")).toHaveCount(0);

  await switchPersonaAndWaitForStableContext(page, "admin");
  await selectClinic(page, seed.clinics.b);
  await expect(page.getByText("Administracija", { exact: true })).toBeVisible();
  await expect(page.getByText("Sigurnost", { exact: true })).toBeVisible();
});
