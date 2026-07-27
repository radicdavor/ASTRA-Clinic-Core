import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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

function renderShellWithLogin(role: string) {
  setSessionUser({ id: 1, name: "Test", email: "test@example.invalid", role });
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/login" element={<p>Prijava</p>} />
        <Route element={<AppShell/>}><Route index element={<p>Početna</p>}/></Route>
      </Routes>
    </MemoryRouter>,
  );
}

function shellFetchWithLogout(logoutRequest: () => Promise<Response>) {
  return vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.includes("/auth/browser/logout")) return logoutRequest();
    const payload = url.includes("/auth/me/clinics")
      ? { clinics: [{ id: 1, name: "Demo klinika", timezone: "Europe/Zagreb" }], default_clinic_id: 1, requires_selection: false }
      : { demo_mode: true, real_data_allowed: false };
    return Promise.resolve(new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } }));
  });
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

  test("uspješna odjava briše lokalno stanje i vodi na prijavu", async () => {
    shellFetchWithLogout(async () => new Response(
      JSON.stringify({ logged_out: true, revoked: true }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    ));
    renderShellWithLogin("demo_receptionist");

    fireEvent.click(screen.getByRole("button", { name: "Odjava" }));

    expect(await screen.findByText("Prijava")).toBeTruthy();
    expect(localStorage.getItem("astra_user")).toBeNull();
    expect(screen.queryByText("Odjava nije uspjela. Pokušajte ponovno.")).toBeNull();
  });

  test("HTTP 403 zadržava prijavu i dopušta uspješan ponovni pokušaj", async () => {
    let attempt = 0;
    shellFetchWithLogout(async () => {
      attempt += 1;
      if (attempt === 1) {
        return new Response(
          JSON.stringify({ detail: "CSRF provjera nije uspjela" }),
          { status: 403, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(
        JSON.stringify({ logged_out: true, revoked: true }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    renderShellWithLogin("demo_receptionist");

    const logoutButton = screen.getByRole("button", { name: "Odjava" });
    fireEvent.click(logoutButton);

    expect(await screen.findByText("Odjava nije uspjela. Pokušajte ponovno.")).toBeTruthy();
    expect(screen.queryByText("CSRF provjera nije uspjela")).toBeNull();
    expect(screen.getByText("Početna")).toBeTruthy();
    expect(localStorage.getItem("astra_user")).toContain("Test");
    await waitFor(() => expect((logoutButton as HTMLButtonElement).disabled).toBe(false));

    fireEvent.click(logoutButton);

    expect(await screen.findByText("Prijava")).toBeTruthy();
    expect(localStorage.getItem("astra_user")).toBeNull();
    expect(attempt).toBe(2);
  });

  test("mrežna pogreška zadržava prijavu i ponovno aktivira odjavu", async () => {
    shellFetchWithLogout(async () => {
      throw new TypeError("Network request failed");
    });
    renderShellWithLogin("demo_receptionist");

    const logoutButton = screen.getByRole("button", { name: "Odjava" });
    fireEvent.click(logoutButton);

    expect(await screen.findByText("Odjava nije uspjela. Pokušajte ponovno.")).toBeTruthy();
    expect(screen.getByText("Početna")).toBeTruthy();
    expect(localStorage.getItem("astra_user")).toContain("Test");
    await waitFor(() => expect((logoutButton as HTMLButtonElement).disabled).toBe(false));
  });

  test("dvostruki klik ne šalje paralelne logout zahtjeve", async () => {
    let resolveLogout: ((response: Response) => void) | undefined;
    const pendingLogout = new Promise<Response>((resolve) => {
      resolveLogout = resolve;
    });
    const fetchMock = shellFetchWithLogout(() => pendingLogout);
    renderShellWithLogin("demo_receptionist");

    const logoutButton = screen.getByRole("button", { name: "Odjava" });
    fireEvent.click(logoutButton);
    fireEvent.click(logoutButton);

    await waitFor(() => expect(
      fetchMock.mock.calls.filter(([input]) => String(input).includes("/auth/browser/logout")),
    ).toHaveLength(1));
    expect((logoutButton as HTMLButtonElement).disabled).toBe(true);

    await act(async () => {
      resolveLogout?.(new Response(
        JSON.stringify({ logged_out: true, revoked: true }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ));
      await pendingLogout;
    });
    expect(await screen.findByText("Prijava")).toBeTruthy();
  });
});
