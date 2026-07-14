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
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "blocked",
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
  {
    journey_id: 14, appointment_id: 104, time: "11:00:00", patient_name: "Sintetički Materijal",
    service_id: 1, service_name: "Završeni zahvat", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", intake_channel: "manual", workflow_stage: "procedure_completed",
    document_status: "complete", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "ready", encounter_status: "completed", consumables_status: "pending",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear", blocker_labels: [], blockers: [], allowed_actions: ["record_consumables"],
  },
  {
    journey_id: 15, appointment_id: 105, time: "12:00:00", patient_name: "Sintetička Naplata",
    service_id: 1, service_name: "Naplata usluge", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", intake_channel: "manual", workflow_stage: "awaiting_payment",
    document_status: "complete", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "ready", encounter_status: "completed", consumables_status: "confirmed",
    billing_status: "invoice_created", payment_status: "unpaid", blocker_status: "clear", blocker_labels: [], blockers: [], allowed_actions: ["open_payment"],
  },
  {
    journey_id: 16, appointment_id: 106, time: "13:00:00", patient_name: "Sintetički Čeka",
    service_id: 1, service_name: "Kontrola", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", intake_channel: "manual", workflow_stage: "ready_for_arrival",
    document_status: "complete", preparation_status: "complete", arrival_status: "not_arrived",
    check_in_status: "not_arrived", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear", blocker_labels: [], blockers: [], allowed_actions: ["open_check_in"],
  },
  {
    journey_id: 17, appointment_id: 107, time: "14:00:00", patient_name: "Sintetički Završeno",
    service_id: 1, service_name: "Kontrola", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", intake_channel: "manual", workflow_stage: "completed",
    document_status: "complete", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "ready", encounter_status: "completed", consumables_status: "not_applicable",
    billing_status: "closed", payment_status: "paid", blocker_status: "clear", blocker_labels: [], blockers: [], allowed_actions: [],
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

beforeEach(() => { installFetchMock(); vi.spyOn(window, "confirm").mockReturnValue(true); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("pojednostavljeni dnevni tijek pacijenata", () => {
  test("prikazuje samo četiri operativna stupca", async () => {
    renderDashboard();
    expect(await screen.findByText("Sintetički Dolazak")).toBeTruthy();
    expect(screen.getAllByRole("columnheader").map(item => item.textContent)).toEqual(["Vrijeme i pacijent", "Usluga i liječnik", "Trenutačno stanje", "Sljedeća radnja"]);
    expect(screen.queryByRole("columnheader", { name: "Dokumenti" })).toBeNull();
    expect(screen.queryByRole("columnheader", { name: "Naplata" })).toBeNull();
  });

  test("prikazuje jedno stanje i puni razlog problema", async () => {
    renderDashboard();
    const patient = await screen.findByText("Sintetički Dolazak");
    const row = patient.closest("tr") as HTMLTableRowElement;
    expect(within(row).getByText("Nedostaje nalaz")).toBeTruthy();
    expect(within(row).getByText("Laboratorijski nalaz nije priložen.")).toBeTruthy();
    const signal = within(row).getByLabelText("Nedostaje nalaz. Laboratorijski nalaz nije priložen.");
    expect(signal.classList.contains("problem")).toBe(true);
    expect(within(signal).getByRole("tooltip").textContent).toContain("Laboratorijski nalaz");
  });

  test("zeleni semafor nema dodatnu administrativnu radnju", async () => {
    renderDashboard();
    const patient = await screen.findByText("Sintetički Završeno");
    const row = patient.closest("tr") as HTMLTableRowElement;
    expect(within(row).getByText("Završeno")).toBeTruthy();
    expect(within(row).getByLabelText(/Završeno/).classList.contains("resolved")).toBe(true);
    expect(within(row).queryByRole("button")).toBeNull();
  });

  test("jednim klikom započinje prijem i evidentira dolazak", async () => {
    const user = userEvent.setup(); renderDashboard();
    const row = (await screen.findByText("Sintetički Čeka")).closest("tr") as HTMLTableRowElement;
    await user.click(within(row).getByRole("button", { name: "Započni prijem" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/patient-journeys/16/check-in"), expect.objectContaining({ method: "POST" })));
    expect(await screen.findByText("Otvoren radni prostor")).toBeTruthy();
  });

  test("za prijem u tijeku prikazuje samo Nastavi prijem", async () => {
    renderDashboard();
    const row = (await screen.findByText("Sintetički Prijem")).closest("tr") as HTMLTableRowElement;
    expect(within(row).getByRole("button", { name: "Nastavi prijem" })).toBeTruthy();
    expect(within(row).getAllByRole("button")).toHaveLength(1);
  });

  test("pregled, materijal i naplata dobivaju po jednu kontekstualnu radnju", async () => {
    renderDashboard();
    expect(await screen.findByRole("button", { name: "Otvori pregled" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Evidentiraj materijal" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Naplati" })).toBeTruthy();
  });

  test("naplata otvara postojeći račun bez dodatne mutacije", async () => {
    const user = userEvent.setup(); renderDashboard();
    await user.click(await screen.findByRole("button", { name: "Naplati" }));
    expect(await screen.findByText("Otvoren radni prostor")).toBeTruthy();
    expect(fetch).not.toHaveBeenCalledWith(expect.stringContaining("/billing/prepare"), expect.anything());
  });

  test("pretragu pacijenta šalje dnevnom API-ju", async () => {
    const user = userEvent.setup(); renderDashboard();
    const search = await screen.findByRole("textbox", { name: "Pretraži pacijenta" });
    await user.type(search, "Dolazak");
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/dashboard\/day\?.*q=Dolazak/), expect.anything()));
  });
});
