import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { setSessionUser, setToken } from "../api/client";
import { AppShell } from "./AppShell";

function renderShell(role: string) {
  setToken("test-token");
  setSessionUser({ id: 1, name: "Test", email: "test@example.invalid", role });
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ demo_mode: true, real_data_allowed: false }), { status: 200, headers: { "Content-Type": "application/json" } }));
  return render(<MemoryRouter initialEntries={["/"]}><Routes><Route element={<AppShell/>}><Route index element={<p>Početna</p>}/></Route></Routes></MemoryRouter>);
}

beforeEach(() => localStorage.clear());
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); });

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
    const payload = btoa(JSON.stringify({ sub: "1", role: "demo_admin" })).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
    setToken(`header.${payload}.signature`);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ demo_mode: true, real_data_allowed: false }), { status: 200, headers: { "Content-Type": "application/json" } }));
    render(<MemoryRouter initialEntries={["/"]}><Routes><Route element={<AppShell/>}><Route index element={<p>Početna</p>}/></Route></Routes></MemoryRouter>);
    expect(screen.getByText("Administracija")).toBeTruthy();
  });

  test("ne prikazuje nefunkcionalnu globalnu pretragu", () => {
    renderShell("demo_physician");
    expect(screen.queryByPlaceholderText(/Pretraži pacijenta, uslugu/i)).toBeNull();
  });
});
