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

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function appointmentSlot(label: string, clinicId: number, date: string, time = "08:00") {
  return [{
    time,
    span: 1,
    empty: false,
    appointment: {
      id: clinicId,
      patient_id: clinicId,
      service_id: 1,
      provider_id: clinicId,
      room_id: clinicId,
      date,
      start_time: `${time}:00`,
      end_time: "08:30:00",
      duration_minutes: 30,
      status: "arrived",
      source: "manual",
      identity_verified_at: "2026-07-27T06:00:00Z",
      patient: { id: clinicId, first_name: label, last_name: "Pacijent" },
      service: { id: 1, name: "Pregled", duration_minutes: 30 },
      provider: { id: clinicId, full_name: `Liječnik ${clinicId}`, clinic_id: clinicId },
      room: { id: clinicId, name: `Soba ${clinicId}`, clinic_id: clinicId },
    },
  }];
}

function installFetchMock() {
  return vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.includes("/api/reception/day")) return response([]);
    if (url.includes("/api/appointments?")) return response([]);
    if (url.endsWith("/api/clinics")) return response([
      { id: 1, name: "Klinika A", active: true },
      { id: 2, name: "Klinika B", active: true },
    ]);
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
      && String(input).includes("clinic_id=1")
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
      && String(input).includes("clinic_id=2")
    )).toBe(true));
    expect(dayRequests().some(([input]) => String(input).includes("clinic_id=1"))).toBe(false);
    expect((screen.getByRole("combobox", { name: "Aktivna klinika" }) as HTMLSelectElement).value).toBe("2");
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

  test.each([
    [null, /nema postavljenu vremensku zonu/i],
    ["", /nema postavljenu vremensku zonu/i],
    ["Invalid/Zone", /nije valjana/i],
  ])("fails closed without Reception requests for timezone %j", (timezone, message) => {
    installFetchMock();
    render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone,
      error: null,
    }));

    expect(screen.getByText(message)).toBeTruthy();
    expect(fetch).not.toHaveBeenCalled();
  });

  test("recovers safely after an invalid timezone is replaced", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-27T01:30:00.000Z"));
    installFetchMock();
    const view = render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Invalid/Zone",
      error: null,
    }));
    expect(fetch).not.toHaveBeenCalled();

    view.rerender(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "2",
      timezone: "America/Los_Angeles",
      error: null,
    }));

    await waitFor(() => expect(dayRequests().some(([input]) =>
      String(input).includes("date=2026-07-26")
      && String(input).includes("clinic_id=2")
    )).toBe(true));
  });

  test("never combines clinic B with clinic A provider or room filters during a switch", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-27T12:00:00.000Z"));
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/api/reception/day") || url.includes("/api/appointments?")) return response([]);
      if (url.endsWith("/api/clinics")) return response([
        { id: 1, name: "Klinika A", active: true },
        { id: 2, name: "Klinika B", active: true },
      ]);
      if (url.endsWith("/api/providers")) return response([
        { id: 11, full_name: "Liječnik A", work_start: "08:00", work_end: "16:00", staff_role: "physician", clinic_id: 1 },
        { id: 21, full_name: "Liječnik B", work_start: "08:00", work_end: "16:00", staff_role: "physician", clinic_id: 2 },
      ]);
      if (url.endsWith("/api/rooms")) return response([
        { id: 12, name: "Soba A", clinic_id: 1 },
        { id: 22, name: "Soba B", clinic_id: 2 },
      ]);
      if (url.endsWith("/api/services")) return response([]);
      throw new Error(`Unexpected filter-scope Reception request: ${url}`);
    });
    const view = render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Etc/UTC",
      error: null,
    }));
    await waitFor(() => expect(screen.getByRole("option", { name: /Liječnik A/ })).toBeTruthy());
    const filters = screen.getAllByRole("combobox");
    fireEvent.change(filters[1], { target: { value: "11" } });
    fireEvent.change(filters[2], { target: { value: "12" } });
    await waitFor(() => expect(dayRequests().some(([input]) =>
      String(input).includes("provider_id=11") && String(input).includes("room_id=12")
    )).toBe(true));
    fetchMock.mockClear();

    view.rerender(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "2",
      timezone: "Etc/UTC",
      error: null,
    }));

    await waitFor(() => expect(dayRequests().some(([input]) => String(input).includes("clinic_id=2"))).toBe(true));
    expect(dayRequests().every(([input]) =>
      !String(input).includes("provider_id=11") && !String(input).includes("room_id=12")
    )).toBe(true);
    await waitFor(() => {
      const nextFilters = screen.getAllByRole("combobox") as HTMLSelectElement[];
      expect(nextFilters[1].value).toBe("");
      expect(nextFilters[2].value).toBe("");
    });
  });

  test("uses timezone-neutral previous and next calendar-day navigation", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-12-31T12:00:00.000Z"));
    installFetchMock();
    render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Etc/UTC",
      error: null,
    }));
    await waitFor(() => expect(dayRequests().length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole("button", { name: /Sljedeći dan/i }));
    await waitFor(() => expect(dayRequests().some(([input]) => String(input).includes("date=2027-01-01"))).toBe(true));
    fireEvent.click(screen.getByRole("button", { name: /Prethodni dan/i }));
    await waitFor(() => expect(dayRequests().some(([input]) => String(input).includes("date=2026-12-31"))).toBe(true));
  });

  test("discards a deferred clinic-A direct refresh after switching to clinic B", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-27T01:30:00.000Z"));
    const fetchMock = installFetchMock();
    const view = render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Europe/Zagreb",
      error: null,
    }));
    await waitFor(() => expect(dayRequests().length).toBeGreaterThan(0));
    fetchMock.mockClear();

    const staleDay = deferred<Response>();
    const staleWeek = deferred<Response>();
    const staleSignals: AbortSignal[] = [];
    fetchMock.mockImplementation((input, init) => {
      const url = String(input);
      if (url.includes("/api/reception/day") && url.includes("clinic_id=1")) {
        if (init?.signal) staleSignals.push(init.signal);
        return staleDay.promise;
      }
      if (url.includes("/api/appointments?") && url.includes("date_from=2026-07-27")) {
        if (init?.signal) staleSignals.push(init.signal);
        return staleWeek.promise;
      }
      if (url.includes("/api/reception/day") && url.includes("clinic_id=2")) return response(appointmentSlot("ClinicB", 2, "2026-07-26"));
      if (url.includes("/api/appointments?")) return response([]);
      if (url.endsWith("/api/clinics")) return response([{ id: 2, name: "Klinika B", active: true }]);
      if (url.endsWith("/api/rooms") || url.endsWith("/api/providers") || url.endsWith("/api/services")) return response([]);
      throw new Error(`Unexpected deferred Reception request: ${url}`);
    });

    window.dispatchEvent(new Event("astra:appointments-changed"));
    await waitFor(() => expect(staleSignals.length).toBe(2));

    view.rerender(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "2",
      timezone: "America/Los_Angeles",
      error: null,
    }));
    await waitFor(() => expect(screen.getByText("ClinicB Pacijent")).toBeTruthy());
    expect(staleSignals.every((signal) => signal.aborted)).toBe(true);

    staleDay.resolve(await response(appointmentSlot("ClinicA", 1, "2026-07-27")));
    staleWeek.resolve(await response([]));
    await Promise.resolve();
    expect(screen.queryByText("ClinicA Pacijent")).toBeNull();
    expect(screen.getByText("ClinicB Pacijent")).toBeTruthy();
  });

  test("aborts a direct refresh on date change and unmount without surfacing an error", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-27T12:00:00.000Z"));
    const fetchMock = installFetchMock();
    const view = render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Etc/UTC",
      error: null,
    }));
    await waitFor(() => expect(dayRequests().length).toBeGreaterThan(0));
    fetchMock.mockClear();

    const pending = deferred<Response>();
    const signals: AbortSignal[] = [];
    fetchMock.mockImplementation((input, init) => {
      const url = String(input);
      if (init?.signal) signals.push(init.signal);
      if (url.includes("/api/reception/day") || url.includes("/api/appointments?")) return pending.promise;
      return response([]);
    });

    window.dispatchEvent(new Event("astra:appointments-changed"));
    await waitFor(() => expect(signals.length).toBe(2));
    fireEvent.click(screen.getByRole("button", { name: /Sljedeći dan/i }));
    await waitFor(() => expect(signals.slice(0, 2).every((signal) => signal.aborted)).toBe(true));
    expect(screen.queryByRole("alert")).toBeNull();

    view.unmount();
    expect(signals.every((signal) => signal.aborted)).toBe(true);
  });

  test("shows a current direct-refresh rejection but clears it on a safe context change", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-27T12:00:00.000Z"));
    const fetchMock = installFetchMock();
    const view = render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Etc/UTC",
      error: null,
    }));
    await waitFor(() => expect(dayRequests().length).toBeGreaterThan(0));
    fetchMock.mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/api/reception/day")) return Promise.reject(new Error("Kontrolirani refresh problem"));
      if (url.includes("/api/appointments?")) return response([]);
      return response([]);
    });

    window.dispatchEvent(new Event("astra:appointments-changed"));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Kontrolirani refresh problem"));

    view.rerender(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "2",
      timezone: "Etc/UTC",
      error: null,
    }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });

  test("does not start a stale mutation-triggered refresh after the clinic changes", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-07-27T12:00:00.000Z"));
    const mutation = deferred<Response>();
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/api/appointments/1/start-service")) return mutation.promise;
      if (url.includes("/api/reception/day") && url.includes("clinic_id=1")) return response(appointmentSlot("ClinicA", 1, "2026-07-27"));
      if (url.includes("/api/reception/day") && url.includes("clinic_id=2")) return response(appointmentSlot("ClinicB", 2, "2026-07-27"));
      if (url.includes("/api/appointments?")) return response([]);
      if (url.endsWith("/api/clinics")) return response([
        { id: 1, name: "Klinika A", active: true },
        { id: 2, name: "Klinika B", active: true },
      ]);
      if (url.endsWith("/api/rooms") || url.endsWith("/api/providers") || url.endsWith("/api/services")) return response([]);
      throw new Error(`Unexpected mutation Reception request: ${url}`);
    });
    const view = render(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "1",
      timezone: "Etc/UTC",
      error: null,
    }));
    await waitFor(() => expect(screen.getByText("ClinicA Pacijent")).toBeTruthy());
    fireEvent.click(screen.getByText("ClinicA Pacijent").closest("button")!);
    fireEvent.click(screen.getByText("Zapocni uslugu").closest("button")!);
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => String(input).includes("/api/appointments/1/start-service"))).toBe(true));
    fetchMock.mockClear();

    view.rerender(receptionWithClinicContext({
      status: "clinic_context_ready",
      ready: true,
      clinicId: "2",
      timezone: "Etc/UTC",
      error: null,
    }));
    await waitFor(() => expect(screen.getByText("ClinicB Pacijent")).toBeTruthy());
    mutation.resolve(await response({ id: 1 }));
    await Promise.resolve();
    await Promise.resolve();

    expect(dayRequests().some(([input]) => String(input).includes("clinic_id=1"))).toBe(false);
    expect(screen.queryByText("ClinicA Pacijent")).toBeNull();
    expect(screen.getByText("ClinicB Pacijent")).toBeTruthy();
  });
});
