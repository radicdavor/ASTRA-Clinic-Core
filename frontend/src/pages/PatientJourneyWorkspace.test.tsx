import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { setSessionUser } from "../api/client";
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

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); setSessionUser({ id: 1, name: "Liječnik", email: "doctor@example.invalid", role: "demo_physician" }); installFetch(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); sessionStorage.clear(); });

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

  test("izravni ulazak u pregled ne dohvaća podatke skrivenih faza", async () => {
    render(<MemoryRouter initialEntries={["/journeys/32?focus=encounter"]}><Routes><Route path="/journeys/:id" element={<PatientJourneyWorkspace/>}/></Routes></MemoryRouter>);
    await screen.findByText("Pregled pacijenta");
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledWith(expect.stringContaining("/encounter"), expect.anything()));

    const urls = vi.mocked(globalThis.fetch).mock.calls.map(([input]) => String(input));
    expect(urls.some(url => url.endsWith("/check-in"))).toBe(true);
    expect(urls.some(url => url.endsWith("/public-config"))).toBe(true);
    expect(urls.some(url => url.endsWith("/activity-preparation"))).toBe(false);
    expect(urls.some(url => url.endsWith("/preparation"))).toBe(false);
    expect(urls.some(url => url.endsWith("/closure"))).toBe(false);
    expect(urls.some(url => url.endsWith("/inventory/items"))).toBe(false);
    expect(urls.some(url => url.endsWith("/visit-documents"))).toBe(false);
    expect(urls.some(url => url.endsWith("/pathology-cases"))).toBe(false);
  });

  test("promjena aktivnosti ne odbacuje nespremljeni klinički unos", async () => {
    vi.restoreAllMocks();
    const activities = [
      { id: 101, journey_id: 32, appointment_id: 32, service_id: 1, activity_key: "prvi-pregled", activity_kind: "specialist_consultation", specialty_key: "gastroenterology", clinic_id: 1, primary_provider_id: 1, room_id: 1, sequence: 1, depends_on_activity_id: null, required: true, planned_start: "2026-07-15T10:00:00Z", planned_end: "2026-07-15T10:30:00Z", actual_start: null, actual_end: null, status: "in_progress", not_performed_reason: null, form_resolution_status: "resolved", billing_status: "pending", consumables_status: "pending" },
      { id: 102, journey_id: 32, appointment_id: 33, service_id: 2, activity_key: "gastroskopija", activity_kind: "gastroscopy", specialty_key: "gastroenterology", clinic_id: 1, primary_provider_id: 1, room_id: 1, sequence: 2, depends_on_activity_id: 101, required: true, planned_start: "2026-07-15T10:30:00Z", planned_end: "2026-07-15T11:00:00Z", actual_start: null, actual_end: null, status: "planned", not_performed_reason: null, form_resolution_status: "resolved", billing_status: "pending", consumables_status: "pending" },
    ];
    const form = (activityId: number) => ({
      id: activityId + 500, activity_id: activityId, form_version_id: 5, purpose: "clinical_report", status: "draft", data_json: {}, rendered_summary: null,
      completed_by: null, signed_by: null, completed_at: null, signed_at: null, amended_from_instance_id: null, binding_source: "default_service",
      resolved_at: "2026-07-15T09:50:00Z", revision_number: 0, updated_at: "2026-07-15T09:50:00Z",
      form_version: { id: 5, definition_id: 2, version: 1, status: "published", output_document_type: "clinical_report", sections_json: [{ section_key: "main", title: "Nalaz", fields: [{ field_key: "opinion", label: "Mišljenje", type: "long_text", required: true }] }] },
    });
    vi.spyOn(globalThis, "fetch").mockImplementation(input => {
      const url = String(input);
      if (/patient-journeys\/32$/.test(url)) return response({ ...journey, current_stage: "in_encounter", encounter_status: "in_progress", activities });
      if (url.endsWith("/api/services")) return response([{ id: 1, name: "Prvi pregled" }, { id: 2, name: "Gastroskopija" }]);
      if (/activities\/101\/form$/.test(url)) return response(form(101));
      if (/activities\/102\/form$/.test(url)) return response(form(102));
      if (url.endsWith("/timeline") || url.includes("/interventions") || url.includes("/pathology-specimens")) return response([]);
      if (url.endsWith("/summary") || url.endsWith("/check-in") || url.endsWith("/preparation") || url.endsWith("/encounter")) return response(null);
      if (url.endsWith("/closure")) return response({ journey_id: 32, stage: "in_encounter", consumables_status: "not_ready", billing_status: "not_ready", payment_status: "not_due", invoice: null, consumables: [] });
      return response([]);
    });

    const user = userEvent.setup();
    render(<MemoryRouter initialEntries={["/journeys/32?focus=encounter&activity=101"]}><Routes><Route path="/journeys/:id" element={<PatientJourneyWorkspace/>}/></Routes></MemoryRouter>);
    await user.type(await screen.findByLabelText("Mišljenje *"), "Lokalni klinički unos");
    await user.click(await screen.findByRole("button", { name: /2\. Gastroskopija/ }));

    expect(await screen.findByRole("dialog", { name: "Želite li spremiti promjene?" })).toBeTruthy();
    expect((screen.getByLabelText("Mišljenje *") as HTMLTextAreaElement).value).toBe("Lokalni klinički unos");
    await user.click(screen.getByRole("button", { name: "Odbaci i nastavi" }));
    await waitFor(() => expect(screen.getByText("Gastroskopija", { selector: "h2" })).toBeTruthy());
  });
});
