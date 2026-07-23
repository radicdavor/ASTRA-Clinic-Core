import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { getActiveClinicId, getDemoPersonaKey, setSessionUser } from "../api/client";
import { AppShell, navigationForRole } from "./AppShell";

function mockShellFetch(
  clinics = [{ id: 1, name: "Demo klinika", timezone: "Europe/Zagreb" }],
  switcherEnabled = true,
) {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    const payload = url.includes("/auth/me/clinics")
      ? { clinics, default_clinic_id: clinics.length === 1 ? clinics[0].id : null, requires_selection: clinics.length > 1 }
      : { demo_mode: true, real_data_allowed: false, demo_persona_switcher_enabled: switcherEnabled };
    return Promise.resolve(new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } }));
  });
}

function renderShell(role: string, clinics?: Array<{ id: number; name: string; timezone: string }>) {
  setSessionUser({ id: 1, name: "Test", email: "test@example.invalid", role });
  mockShellFetch(clinics);
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<p>Početna</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

function topLevelEntries() {
  const nav = screen.getByRole("navigation", { name: "Glavna navigacija" });
  return nav.querySelectorAll(":scope > a, :scope > details");
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); sessionStorage.clear(); });

describe("navigacija prema zadatku i ulozi", () => {
  test.each([
    ["demo_receptionist", 5, ["Danas", "Pacijenti", "Naručivanje", "Prijem", "Dokumenti"]],
    ["demo_physician", 5, ["Danas", "Pacijenti", "Klinički rad", "Zadaci", "Naručivanje"]],
    ["demo_nurse", 5, ["Danas", "Pacijenti", "Zadaci", "Klinička podrška", "Raspored i zalihe"]],
    ["demo_billing", 3, ["Danas", "Pacijenti", "Računi"]],
    ["demo_inventory_manager", 3, ["Inventar", "Dobavljači", "Narudžbenice"]],
    ["demo_document_reviewer", 3, ["Danas", "Pacijenti", "Dokumenti"]],
  ])("%s vidi najviše pet ulaza vezanih uz svoju ulogu", (role, count, labels) => {
    renderShell(role);
    expect(topLevelEntries()).toHaveLength(count);
    const nav = screen.getByRole("navigation", { name: "Glavna navigacija" });
    for (const label of labels) expect(within(nav).getByText(label)).toBeTruthy();
  });

  test("recepcija ne vidi administraciju, sigurnost ni kliničke odluke", () => {
    renderShell("demo_receptionist");
    expect(screen.queryByText("Administracija")).toBeNull();
    expect(screen.queryByText("Sigurnost")).toBeNull();
    expect(screen.queryByText("Klinički rad")).toBeNull();
  });

  test("administrator vidi pet smislenih područja umjesto generičkog izbornika Više", () => {
    renderShell("demo_admin");
    expect(topLevelEntries()).toHaveLength(5);
    expect(screen.getByRole("link", { name: "Danas" })).toBeTruthy();
    expect(screen.getByText("Operacije")).toBeTruthy();
    expect(screen.getByText("Nabava i financije")).toBeTruthy();
    expect(screen.getByText("Administracija")).toBeTruthy();
    expect(screen.getByText("Sigurnost")).toBeTruthy();
    expect(screen.queryByText("Više")).toBeNull();
  });

  test("grupirani klinički rad ostaje na drugoj i posljednjoj razini", () => {
    renderShell("demo_physician");
    const groupSummary = screen.getByText("Klinički rad").closest("summary");
    expect(groupSummary).toBeTruthy();
    fireEvent.click(groupSummary!);
    const group = groupSummary!.closest("details")!;
    expect(within(group).getByRole("link", { name: "Dokumenti" })).toBeTruthy();
    expect(within(group).getByRole("link", { name: "Gastroenterologija" })).toBeTruthy();
    expect(group.querySelector("details")).toBeNull();
  });

  test("topbar jasno prikazuje ulogu običnim hrvatskim nazivom", async () => {
    renderShell("demo_nurse");
    expect(await screen.findByLabelText("Demo prikaz uloge")).toBeTruthy();
    expect(await screen.findByText(/DEMO · Medicinska sestra/)).toBeTruthy();
  });

  test("postojeća prijava čita ulogu iz spremljene sesije", () => {
    renderShell("demo_admin");
    expect(screen.getByText("Administrator")).toBeTruthy();
    expect(screen.getByText("Administracija")).toBeTruthy();
  });

  test("demo switcher nudi svih pet stvarnih persona i traži potvrdu", async () => {
    renderShell("demo_admin");
    const picker = await screen.findByLabelText("Demo prikaz uloge");
    expect(within(picker).getAllByRole("option")).toHaveLength(5);
    fireEvent.change(picker, { target: { value: "physician_2" } });
    expect(screen.getByRole("dialog", { name: "Promijeniti demo ulogu?" })).toBeTruthy();
    expect(screen.getByText(/klinika i podaci ponovno učitati s ovlastima/)).toBeTruthy();
    expect(getDemoPersonaKey()).toBeNull();
  });

  test("demo switcher nije prikazan kada ga backend konfiguracija ne dopušta", async () => {
    setSessionUser({ id: 1, name: "Admin", email: "admin@example.invalid", role: "demo_admin" });
    mockShellFetch(undefined, false);
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes><Route element={<AppShell />}><Route index element={<p>Početna</p>} /></Route></Routes>
      </MemoryRouter>,
    );
    await screen.findByText("Uloga:");
    expect(screen.queryByLabelText("Demo prikaz uloge")).toBeNull();
  });

  test("korisnik s više klinika vidi izbor i potvrdu prije promjene konteksta", async () => {
    renderShell("demo_admin", [
      { id: 1, name: "Gastroenterologija", timezone: "Europe/Zagreb" },
      { id: 2, name: "Estetika", timezone: "Europe/Zagreb" },
    ]);
    expect(await screen.findByText("Odaberite kliniku za prikaz podataka.")).toBeTruthy();
    const picker = screen.getByLabelText("Aktivna klinika");
    fireEvent.change(picker, { target: { value: "2" } });
    expect(screen.getByRole("dialog", { name: "Promijeniti aktivnu kliniku?" })).toBeTruthy();
    expect(screen.getByText(/Spremite otvorene skice prije nastavka/)).toBeTruthy();
    expect(getActiveClinicId()).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Odustani" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(getActiveClinicId()).toBeNull();
  });

  test("ne prikazuje nefunkcionalnu globalnu pretragu", () => {
    renderShell("demo_physician");
    expect(screen.queryByPlaceholderText(/Pretraži pacijenta, uslugu/i)).toBeNull();
  });

  test("konfiguracija svake ljudske uloge ima najviše pet primarnih ulaza", () => {
    for (const role of ["admin", "physician", "nurse", "receptionist", "billing", "inventory_manager", "document_reviewer"]) {
      expect(navigationForRole(role, true).length).toBeLessThanOrEqual(5);
    }
  });
});
