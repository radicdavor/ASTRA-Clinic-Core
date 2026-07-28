import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { ClinicContextProvider, type ClinicContextValue } from "../contexts/ClinicContext";
import { Reception } from "./Reception";

function response(body: unknown) {
  return Promise.resolve(new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  }));
}

function installFetchMock() {
  return vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.includes("/api/reception/day")) return response([]);
    if (url.includes("/api/appointments?")) return response([]);
    if (url.endsWith("/api/clinics")) return response([{ id: 1, name: "Klinika", active: true }]);
    if (url.endsWith("/api/rooms")) return response([]);
    if (url.endsWith("/api/providers")) return response([]);
    if (url.endsWith("/api/services")) return response([]);
    throw new Error(`Unexpected Reception test request: ${url}`);
  });
}

function receptionWithClinicContext(value: ClinicContextValue) {
  return (
    <ClinicContextProvider value={value}>
      <MemoryRouter><Reception /></MemoryRouter>
    </ClinicContextProvider>
  );
}

function dayRequests() {
  return vi.mocked(fetch).mock.calls.filter(([input]) => String(input).includes("/api/reception/day"));
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("Reception clinic-local date contract", () => {
  test("does not request data before active clinic and timezone readiness", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-26T22:30:00.000Z"));
    installFetchMock();
    const view = render(receptionWithClinicContext({
      status: "clinic_context_loading",
      ready: false,
      clinicId: null,
      timezone: null,
      error: null,
    }));

    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getByText(/čeka aktivnu kliniku/i)).toBeTruthy();

    view.rerender(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Europe/Zagreb",
      error: null,
    }));

    await waitFor(() => expect(dayRequests().some(([input]) =>
      String(input).includes("date=2026-07-27")
    )).toBe(true));
  });

  test("clinic switch recalculates auto-today and aborts the stale clinic date", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-27T01:30:00.000Z"));
    installFetchMock();
    const view = render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Europe/Zagreb",
      error: null,
    }));
    await waitFor(() => expect(dayRequests().some(([input]) =>
      String(input).includes("date=2026-07-27")
    )).toBe(true));
    vi.mocked(fetch).mockClear();

    view.rerender(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "2",
      timezone: "America/Los_Angeles",
      error: null,
    }));

    await waitFor(() => expect(dayRequests().some(([input]) =>
      String(input).includes("date=2026-07-26")
    )).toBe(true));
    expect(dayRequests().some(([input]) => String(input).includes("date=2026-07-27"))).toBe(false);
  });

  test("manual date survives clinic switch and Today returns to clinic-local automatic mode", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-27T01:30:00.000Z"));
    installFetchMock();
    const view = render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Europe/Zagreb",
      error: null,
    }));
    await waitFor(() => expect(dayRequests().length).toBeGreaterThan(0));

    fireEvent.change(document.querySelector("input.native-date-picker") as HTMLInputElement, {
      target: { value: "2026-08-03" },
    });
    await waitFor(() => expect(dayRequests().some(([input]) =>
      String(input).includes("date=2026-08-03")
    )).toBe(true));

    view.rerender(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "2",
      timezone: "America/Los_Angeles",
      error: null,
    }));
    expect(screen.getByDisplayValue("03. 08. 2026.")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Danas" }));
    await waitFor(() => expect(dayRequests().some(([input]) =>
      String(input).includes("date=2026-07-26")
    )).toBe(true));
  });

  test("long-lived auto-today view advances once across clinic midnight", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-26T21:59:30.000Z"));
    installFetchMock();
    render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Europe/Zagreb",
      error: null,
    }));

    await waitFor(() => expect(dayRequests().some(([input]) =>
      String(input).includes("date=2026-07-26")
    )).toBe(true));
    await vi.advanceTimersByTimeAsync(60_000);
    await waitFor(() => expect(dayRequests().some(([input]) =>
      String(input).includes("date=2026-07-27")
    )).toBe(true));

    expect(dayRequests()).toHaveLength(2);
  });
});
