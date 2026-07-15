import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { setSessionUser, setToken } from "../api/client";
import { PatientJourneyWorkspace } from "./PatientJourneyWorkspace";

const journey = {
  id: 32, patient_id: 19, appointment_id: 32, intake_channel: "manual", current_stage: "ready_for_clinician",
  document_status: "complete", preparation_status: "complete", check_in_status: "ready", encounter_status: "not_started",
  consumables_status: "not_ready", billing_status: "not_ready", payment_status: "not_due", closed_at: null,
  patient: { id: 19, first_name: "Sintetički", last_name: "Pacijent", date_of_birth: "1980-01-01", oib: null },
  appointment: {
    id: 32, service_id: 1, provider_id: 1, room_id: 1, date: "2026-07-15", start_time: "10:00:00", end_time: "10:30:00", status: "scheduled", source: "manual",
    service: { id: 1, name: "Povijesna usluga" }, provider: { id: 1, full_name: "dr. Kanonski" }, room: { id: 1, name: "Ordinacija 1" },
  },
  blockers: [], events: [], created_at: "2026-07-15T08:00:00Z", updated_at: "2026-07-15T08:00:00Z",
};

function response(value: unknown) { return Promise.resolve(new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } })); }
function installFetch() {
  return vi.spyOn(globalThis, "fetch").mockImplementation(input => {
    const url = String(input);
    if (/patient-journeys\/32$/.test(url)) return response(journey);
    if (url.endsWith("/timeline")) return response([{ date: "2026-07-15T08:00:00Z", event_type: "booked", title: "Termin potvrđen", summary: null, source_url: null, provenance: {}, review_state: null, journey_id: 32 }]);
    if (url.endsWith("/summary") || url.endsWith("/check-in") || url.endsWith("/preparation") || url.endsWith("/encounter")) return response(null);
    if (url.endsWith("/closure")) return response({ journey_id: 32, stage: "ready_for_clinician", consumables_status: "not_ready", billing_status: "not_ready", payment_status: "not_due", invoice: null, consumables: [] });
    if (url.endsWith("/api/services") || url.endsWith("/api/providers")) return response([]);
    return response([]);
  });
}

beforeEach(() => { localStorage.clear(); setToken("test-token"); setSessionUser({ id: 1, name: "Liječnik", email: "doctor@example.invalid", role: "demo_physician" }); installFetch(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); });

describe("fokusirani radni prostor tijeka pacijenta", () => {
  test("prikazuje sljedeću radnju i samo trenutačnu fazu", async () => {
    render(<MemoryRouter initialEntries={["/journeys/32"]}><Routes><Route path="/journeys/:id" element={<PatientJourneyWorkspace/>}/></Routes></MemoryRouter>);
    expect(await screen.findByText("Pacijent čeka liječnika")).toBeTruthy();
    expect(await screen.findByText(/Povijesna usluga · dr. Kanonski/)).toBeTruthy();
    expect(await screen.findByText("Pregled pacijenta")).toBeTruthy();
    expect(screen.queryByText("Prijemna provjera")).toBeNull();
  });

  test("drugu fazu otvara bez prikaza svih ostalih faza", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter initialEntries={["/journeys/32"]}><Routes><Route path="/journeys/:id" element={<PatientJourneyWorkspace/>}/></Routes></MemoryRouter>);
    await screen.findByText("Pregled pacijenta");
    await user.click(screen.getByRole("button", { name: /Dolazak i prijem/ }));
    expect(await screen.findByText("Prijemna provjera")).toBeTruthy();
    expect(screen.queryByText("Pregled pacijenta")).toBeNull();
  });

  test("klinički kontekst je sekundaran, ali dokumenti su dostupni jednim otvaranjem", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter initialEntries={["/journeys/32"]}><Routes><Route path="/journeys/:id" element={<PatientJourneyWorkspace/>}/></Routes></MemoryRouter>);
    await screen.findByText("Pacijent čeka liječnika");
    await user.click(screen.getByText("Klinički kontekst"));
    expect(screen.getByRole("tab", { name: "Dokumenti" })).toBeTruthy();
  });
});
