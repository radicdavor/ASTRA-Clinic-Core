import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { setSessionUser } from "../api/client";
import { AppShell } from "./AppShell";

function mockShellFetch(clinics = [{ id: 1, name: "Demo klinika" }]) {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    const payload = url.includes("/auth/me/clinics")
      ? { clinics, default_clinic_id: clinics.length === 1 ? clinics[0].id : null, requires_selection: clinics.length > 1 }
      : { demo_mode: true, real_data_allowed: false };
    return Promise.resolve(new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } }));
  });
}

function renderShell(role: string) {
  setSessionUser({ id: 1, name: "Test", email: "test@example.invalid", role });
  mockShellFetch();
  return render(<MemoryRouter initialEntries={["/"]}><Routes><Route element={<AppShell/>}><Route index element={<p>Početna</p>}/></Route></Routes></MemoryRouter>);
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); sessionStorage.clear(); });

describe("navigacija prema zadatku i ulozi", () => {
  test("recepcija ima tri primarna zadatka i nema administraciju", () => {
    renderShell("demo_receptionist");
    const nav = screen.getByRole("navigation", { name: "Glavna navigacija" });
    expect(nav.querySelectorAll(":scope > a")).toHaveLength(3);
    expect(screen.getByRole("link", { name: "Danas" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Pacijenti" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Naručivanje" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: "Znanje" })).toBeNull();
    expect(screen.queryByText("Administracija")).toBeNull();
  });

  test("administrator vidi četiri primarna zadatka i grupirane alate", () => {
    renderShell("demo_admin");
    const nav = screen.getByRole("navigation", { name: "Glavna navigacija" });
    expect(nav.querySelectorAll(":scope > a")).toHaveLength(4);
    expect(screen.getByText("Administracija")).toBeTruthy();
    expect(screen.getByText("Nabava i zalihe")).toBeTruthy();
    expect(screen.getByText("Demo")).toBeTruthy();
  });

  test("postojeća prijava čita ulogu iz tokena kada zapis korisnika još ne postoji", () => {
    setSessionUser({ id: 1, name: "Admin", email: "admin@example.invalid", role: "demo_admin" });
    mockShellFetch();
    render(<MemoryRouter initialEntries={["/"]}><Routes><Route element={<AppShell/>}><Route index element={<p>Početna</p>}/></Route></Routes></MemoryRouter>);
    expect(screen.getByText("Administracija")).toBeTruthy();
  });

  test("korisnik s vise klinika bira aktivnu kliniku u topbaru", async () => {
    setSessionUser({ id: 1, name: "Admin", email: "admin@example.invalid", role: "demo_admin" });
    mockShellFetch([{ id: 1, name: "Gastroenterologija" }, { id: 2, name: "Estetika" }]);
    render(<MemoryRouter initialEntries={["/"]}><Routes><Route element={<AppShell/>}><Route index element={<p>Početna</p>}/></Route></Routes></MemoryRouter>);
    expect(await screen.findByText("Odaberite kliniku za prikaz podataka.")).toBeTruthy();
    expect(screen.getByLabelText("Aktivna klinika")).toBeTruthy();
  });

  test("ne prikazuje nefunkcionalnu globalnu pretragu", () => {
    renderShell("demo_physician");
    expect(screen.queryByPlaceholderText(/Pretraži pacijenta, uslugu/i)).toBeNull();
  });
});
