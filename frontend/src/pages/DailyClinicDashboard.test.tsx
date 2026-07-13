import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DailyClinicDashboard } from "./DailyClinicDashboard";

const rows = [
  {
    journey_id: 11, appointment_id: 101, time: "08:00:00", patient_name: "Sintetički Dolazak",
    service_id: 1, service_name: "Prvi pregled", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", intake_channel: "manual", workflow_stage: "ready_for_arrival",
    document_status: "complete", preparation_status: "in_progress", arrival_status: "not_arrived",
    check_in_status: "not_arrived", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "unpaid", blocker_status: "blocked",
    blocker_labels: ["Nedostaje nalaz"], blockers: [{ id: 1, title: "Nedostaje nalaz", details: "Laboratorijski nalaz nije priložen.", is_clinical: false }], allowed_actions: ["open_check_in"],
  },
  {
    journey_id: 12, appointment_id: 102, time: "09:00:00", patient_name: "Sintetički Prijem",
    service_id: 1, service_name: "Kontrola", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", intake_channel: "web", workflow_stage: "arrived",
    document_status: "requested", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "not_arrived", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear", blocker_labels: [], blockers: [], allowed_actions: ["open_check_in"],
  },
  {
    journey_id: 13, appointment_id: 103, time: "10:00:00", patient_name: "Sintetički Pregled",
    service_id: 1, service_name: "Pregled", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", intake_channel: "ai_secretary", workflow_stage: "ready_for_clinician",
    document_status: "complete", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "ready", encounter_status: "in_progress", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear", blocker_labels: [], blockers: [], allowed_actions: ["open_encounter"],
  },
];

function response(body: unknown) {
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } }));
}

function installFetchMock() {
  return vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    const url = String(input);
    if (url.includes("/api/dashboard/day")) return response({ date: "2026-07-13", refreshed_at: "2026-07-13T08:00:00Z", visible_sections: [], rows });
    if (url.endsWith("/api/providers") || url.endsWith("/api/rooms") || url.endsWith("/api/services")) return response([]);
    if (init?.method === "POST") return response({});
    throw new Error(`Neočekivani testni API poziv: ${url}`);
  });
}

function renderDashboard() {
  return render(<MemoryRouter initialEntries={["/"]}><Routes><Route path="/" element={<DailyClinicDashboard/>}/><Route path="/journeys/:id" element={<p>Otvoren radni prostor</p>}/></Routes></MemoryRouter>);
}

beforeEach(() => { installFetchMock(); });
afterEach(() => cleanup());

describe("dnevni tijek pacijenata", () => {
  test("prikazuje prevedene statuse i puni razlog blokade", async () => {
    renderDashboard();
    expect(await screen.findByText("Sintetički Dolazak")).toBeTruthy();
    expect(screen.getAllByText("U tijeku").length).toBeGreaterThan(0);
    expect(screen.getByText("Neplaćeno")).toBeTruthy();
    expect(screen.getByText("Dokumentacija je zatražena, ali još nije zaprimljena.")).toBeTruthy();
    expect(screen.getByText("Laboratorijski nalaz nije priložen.")).toBeTruthy();
    expect(screen.queryByText("in_progress")).toBeNull();
    expect(screen.queryByText("unpaid")).toBeNull();
  });

  test("ne prikazuje zaseban dolazak ni dodatni administrativni gumb", async () => {
    renderDashboard();
    expect(await screen.findByText("Sintetički Dolazak")).toBeTruthy();
    expect(screen.queryByRole("columnheader", { name: "Dolazak" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Pacijent stigao" })).toBeNull();
    expect(screen.getAllByRole("button", { name: "Otvori prijem" })).toHaveLength(2);
  });

  test("pripremu prikazuje samo kada je potrebno nešto riješiti", async () => {
    renderDashboard();
    expect(await screen.findByText("Sintetički Dolazak")).toBeTruthy();
    expect(screen.queryByRole("columnheader", { name: "Priprema" })).toBeNull();
    expect(screen.getByRole("columnheader", { name: "Potrebno riješiti" })).toBeTruthy();
    expect(screen.getByText("Priprema još nije dovršena.")).toBeTruthy();
    expect(screen.getAllByText("Nema otvorenih stavki")).toHaveLength(1);
  });

  test("dokumentaciju prikazuje samo kada je potrebno nešto riješiti", async () => {
    renderDashboard();
    expect(await screen.findByText("Sintetički Prijem")).toBeTruthy();
    expect(screen.queryByRole("columnheader", { name: "Dokumenti" })).toBeNull();
    expect(screen.getByText("Dokumentacija je zatražena, ali još nije zaprimljena.")).toBeTruthy();
  });

  test("otvara prijem i usmjerava na prijemnu provjeru", async () => {
    const user = userEvent.setup(); renderDashboard();
    const patient = await screen.findByText("Sintetički Dolazak");
    const patientRow = patient.closest("tr");
    expect(patientRow).toBeTruthy();
    await user.click(within(patientRow as HTMLTableRowElement).getByRole("button", { name: "Otvori prijem" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/patient-journeys/11/check-in"), expect.objectContaining({ method: "POST" })));
    expect(await screen.findByText("Otvoren radni prostor")).toBeTruthy();
  });

  test("otvara pregled bez automatskog pokretanja susreta", async () => {
    const user = userEvent.setup(); renderDashboard();
    await user.click(await screen.findByRole("button", { name: "Otvori pregled" }));
    expect(await screen.findByText("Otvoren radni prostor")).toBeTruthy();
    expect(fetch).not.toHaveBeenCalledWith(expect.stringContaining("/encounter"), expect.anything());
  });

  test("pretragu pacijenta šalje dnevnom API-ju", async () => {
    const user = userEvent.setup(); renderDashboard();
    const search = await screen.findByRole("textbox", { name: "Pretraži pacijenta" });
    await user.type(search, "Dolazak");
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/dashboard\/day\?.*q=Dolazak/), expect.anything()));
  });
});
