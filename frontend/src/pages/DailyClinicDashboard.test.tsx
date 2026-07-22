import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DailyClinicDashboard } from "./DailyClinicDashboard";

function activity(id: number, time: string, end_time: string, service_name: string, room_name = "Ordinacija 1", status = "ready") {
  return { id, sequence: id, time, end_time, service_name, clinician_name: "dr. Test", room_name, status };
}

const rows = [
  {
    journey_id: 1, appointment_id: 101, time: "08:00:00", patient_name: "Kratki Pregled",
    service_id: 1, service_name: "Prvi pregled", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "manual", workflow_stage: "ready_for_arrival",
    document_status: "complete", preparation_status: "complete", arrival_status: "not_arrived",
    check_in_status: "not_arrived", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear",
    operational_status: "waiting_arrival", operational_status_label: "Čeka dolazak", operational_status_severity: "neutral",
    operational_status_reasons: [{ code: "patient_not_arrived", label: "Backend kanonski status: pacijent još nije stigao" }],
    blocker_labels: [], blockers: [], reception_warning: false, reception_warning_details: [], allowed_actions: ["open_check_in"],
    activity_count: 1, current_activity_id: 1011, next_activity_id: null, activities: [activity(1011, "08:00:00", "08:30:00", "Prvi pregled")],
  },
  {
    journey_id: 2, appointment_id: 102, time: "08:15:00", patient_name: "Preklop Pacijent",
    service_id: 2, service_name: "Kontrola", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "web", workflow_stage: "arrived",
    document_status: "complete", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "in_review", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear",
    blocker_labels: [], blockers: [], reception_warning: false, reception_warning_details: [], allowed_actions: ["open_check_in"],
    activity_count: 1, current_activity_id: 1021, next_activity_id: null, activities: [activity(1021, "08:15:00", "08:45:00", "Kontrola")],
  },
  {
    journey_id: 3, appointment_id: 103, time: "09:00:00", patient_name: "Paket Gastro",
    service_id: 3, service_name: "Gastro paket", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "manual", workflow_stage: "ready_for_clinician",
    document_status: "complete", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "ready", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear",
    blocker_labels: [], blockers: [], reception_warning: false, reception_warning_details: [], allowed_actions: ["open_encounter"],
    activity_count: 2, current_activity_id: 302, next_activity_id: null, activities: [
      activity(301, "09:00:00", "09:30:00", "Prvi gastro pregled", "Ordinacija 1", "completed"),
      activity(302, "09:30:00", "10:30:00", "Gastroskopija", "Endoskopija 1", "ready"),
    ],
  },
  {
    journey_id: 4, appointment_id: 104, time: "11:00:00", patient_name: "Crvena Napomena",
    service_id: 4, service_name: "Gastroskopija", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 2, room_name: "Endoskopija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "manual", workflow_stage: "ready_for_clinician",
    document_status: "complete", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "ready", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "blocked",
    blocker_labels: ["Post nije potvrđen"], blockers: [{ id: 8, title: "Post nije potvrđen", details: "Pacijent je pio kavu s mlijekom.", is_clinical: true }],
    reception_warning: true, reception_warning_details: ["Pratnja nakon sedacije nije potvrđena."], allowed_actions: ["open_encounter"],
    activity_count: 1, current_activity_id: 401, next_activity_id: null, activities: [activity(401, "11:00:00", "11:45:00", "Gastroskopija", "Endoskopija 1")],
  },
  {
    journey_id: 5, appointment_id: 105, time: "12:00:00", patient_name: "Čeka Naplatu",
    service_id: 5, service_name: "Zahvat", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 2, room_name: "Endoskopija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "manual", workflow_stage: "awaiting_payment",
    document_status: "complete", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "ready", encounter_status: "completed", consumables_status: "confirmed",
    billing_status: "invoice_created", payment_status: "unpaid", blocker_status: "clear",
    blocker_labels: [], blockers: [], reception_warning: false, reception_warning_details: [], allowed_actions: ["open_payment"],
    activity_count: 1, current_activity_id: 501, next_activity_id: null, activities: [activity(501, "12:00:00", "12:30:00", "Zahvat", "Endoskopija 1", "completed")],
  },
  {
    journey_id: 6, appointment_id: 106, time: "13:00:00", patient_name: "Plaćeno Gotovo",
    service_id: 6, service_name: "Kontrola", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "manual", workflow_stage: "completed",
    document_status: "complete", preparation_status: "complete", arrival_status: "arrived",
    check_in_status: "ready", encounter_status: "completed", consumables_status: "not_applicable",
    billing_status: "closed", payment_status: "paid", blocker_status: "clear",
    blocker_labels: [], blockers: [], reception_warning: false, reception_warning_details: [], allowed_actions: [],
    activity_count: 1, current_activity_id: 601, next_activity_id: null, activities: [activity(601, "13:00:00", "13:30:00", "Kontrola", "Ordinacija 1", "completed")],
  },
  {
    journey_id: 7, appointment_id: 107, time: "14:00:00", patient_name: "Bez Kraja",
    service_id: 7, service_name: "Kratka kontrola", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "manual", workflow_stage: "ready_for_arrival",
    document_status: "complete", preparation_status: "complete", arrival_status: "not_arrived",
    check_in_status: "not_arrived", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear",
    blocker_labels: [], blockers: [], reception_warning: false, reception_warning_details: [], allowed_actions: ["open_check_in"],
    activity_count: 1, current_activity_id: 701, next_activity_id: null, activities: [{ id: 701, sequence: 1, time: "14:00:00", service_name: "Kratka kontrola", clinician_name: "dr. Test", room_name: "Ordinacija 1", status: "ready" }],
  },
  {
    journey_id: 8, appointment_id: 108, time: "06:30:00", patient_name: "Rani Pacijent",
    service_id: 8, service_name: "Rani pregled", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "manual", workflow_stage: "ready_for_arrival",
    document_status: "complete", preparation_status: "complete", arrival_status: "not_arrived",
    check_in_status: "not_arrived", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear",
    blocker_labels: [], blockers: [], reception_warning: false, reception_warning_details: [], allowed_actions: ["open_check_in"],
    activity_count: 1, current_activity_id: 801, next_activity_id: null, activities: [activity(801, "06:30:00", "07:00:00", "Rani pregled", "Ordinacija 1")],
  },
  {
    journey_id: 9, appointment_id: 109, time: "20:00:00", patient_name: "Kasni Pacijent",
    service_id: 9, service_name: "Kasni pregled", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 2, room_name: "Endoskopija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "manual", workflow_stage: "ready_for_arrival",
    document_status: "complete", preparation_status: "complete", arrival_status: "not_arrived",
    check_in_status: "not_arrived", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear",
    blocker_labels: [], blockers: [], reception_warning: false, reception_warning_details: [], allowed_actions: ["open_check_in"],
    activity_count: 1, current_activity_id: 901, next_activity_id: null, activities: [activity(901, "20:00:00", "20:30:00", "Kasni pregled", "Endoskopija 1")],
  },
];

let dashboardAccess = {
  viewer_role: "admin", scope: "all", scope_label: "Svi liječnici", scoped_clinician_id: null,
  can_filter_clinician: true,
  available_clinics: [{ id: 1, name: "Klinika Sjever" }, { id: 2, name: "Klinika Jug" }],
};

function response(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

function journeyResponse(id: number) {
  return {
    id, patient_id: 501, appointment_id: 101, intake_channel: "manual", current_stage: "ready_for_arrival",
    document_status: "complete", preparation_status: "complete", check_in_status: "not_arrived",
    encounter_status: "not_started", consumables_status: "not_ready", billing_status: "not_ready",
    payment_status: "not_due", closed_at: null, blockers: [], activities: [
      { id: 601, journey_id: id, appointment_id: 101, service_id: 1, activity_key: "Prvi pregled", activity_kind: "consultation", specialty_key: "gastroenterology", clinic_id: 1, primary_provider_id: 1, room_id: 1, sequence: 1, depends_on_activity_id: null, required: true, planned_start: "2026-07-13T08:00:00", planned_end: "2026-07-13T08:30:00", actual_start: null, actual_end: null, status: "ready", not_performed_reason: null, form_resolution_status: "not_started", billing_status: "not_ready", consumables_status: "not_ready" },
    ],
    patient: {
      id: 501, first_name: "Kratki", last_name: "Pregled", date_of_birth: "1992-01-06",
      oib: null, email: "synthetic@example.com", phone: "0994477445", notes: null, email_verified_at: null, updated_at: "2026-07-13T10:00:00Z",
    },
    appointment: {
      id: 101, service_id: 1, provider_id: 1, room_id: 1, date: "2026-07-13",
      start_time: "08:00:00", end_time: "08:30:00", status: "booked", source: "manual",
      service: { id: 1, name: "Prvi pregled" }, provider: { id: 1, full_name: "dr. Test" }, room: { id: 1, name: "Ordinacija 1" },
    },
  };
}

function installFetchMock() {
  return vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    const url = String(input);
    if (url.includes("/api/dashboard/day")) return response({ date: "2026-07-13", refreshed_at: "2026-07-13T08:00:00Z", visible_sections: [], ...dashboardAccess, rows });
    if (url.endsWith("/api/providers")) return response([{ id: 1, full_name: "dr. Test", staff_role: "physician" }]);
    if (url.endsWith("/api/rooms")) return response([{ id: 1, name: "Ordinacija 1", clinic_id: 1 }, { id: 2, name: "Endoskopija 1", clinic_id: 1 }]);
    if (url.endsWith("/api/services")) return response([{ id: 1, name: "Prvi pregled" }, { id: 4, name: "Gastroskopija" }]);
    if (/\/api\/patient-journeys\/\d+$/.test(url)) return response(journeyResponse(Number(url.split("/").pop())));
    if (url.endsWith("/api/patients/501") && init?.method === "PATCH") return response({ updated_at: "2026-07-13T10:05:00Z" });
    if (url.endsWith("/api/patient-journeys/1/check-in") && init?.method === "POST") return response({ id: 1, journey_id: 1, status: "in_review", arrived_at: "2026-07-13T08:00:00Z", completed_at: null, items: [] });
    if (url.endsWith("/api/patient-journeys/1/check-in/complete-reception") && init?.method === "POST") return response({ id: 1, journey_id: 1, status: "ready", arrived_at: "2026-07-13T08:00:00Z", completed_at: "2026-07-13T08:05:00Z", items: [] });
    if (init?.method === "POST") return response({});
    throw new Error(`Neočekivani testni API poziv: ${url}`);
  });
}

function renderDashboard() {
  return render(<MemoryRouter initialEntries={["/"]}><Routes><Route path="/" element={<DailyClinicDashboard/>}/><Route path="/journeys/:id" element={<p>Otvoren radni prostor</p>}/></Routes></MemoryRouter>);
}

async function findPatientBlock(label: RegExp) {
  await screen.findByText(label);
  const block = screen.getAllByLabelText(label).find(item => item.classList.contains("timeline-patient-block"));
  if (!block) throw new Error(`Nije pronađen blok pacijenta za ${label}`);
  return block;
}

beforeEach(() => {
  dashboardAccess = { viewer_role: "admin", scope: "all", scope_label: "Svi liječnici", scoped_clinician_id: null, can_filter_clinician: true, available_clinics: [{ id: 1, name: "Klinika Sjever" }, { id: 2, name: "Klinika Jug" }] };
  installFetchMock();
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("vremenska dnevna ploča", () => {
  test("single short appointment renders as one patient block on a visible time axis", async () => {
    renderDashboard();
    expect(await screen.findByRole("button", { name: "Kratki Pregled" })).toBeTruthy();
    expect(screen.getByLabelText("Vremenska os")).toBeTruthy();
    expect(screen.getAllByText("08:00").length).toBeGreaterThan(0);
    const block = await findPatientBlock(/Kratki Pregled/);
    expect(within(block).getByText("Prvi pregled")).toBeTruthy();
    expect(within(block).getByText("Ordinacija 1")).toBeTruthy();
    expect(within(block).getByLabelText(/Backend kanonski status/)).toBeTruthy();
  });

  test("multi-activity visit stays one connected block spanning multiple timeline rows", async () => {
    renderDashboard();
    const block = await findPatientBlock(/Paket Gastro/);
    expect(within(block).getByText("Prvi gastro pregled")).toBeTruthy();
    expect(within(block).getByText("Gastroskopija")).toBeTruthy();
    expect(within(block).getByText("09:00–09:30")).toBeTruthy();
    expect(within(block).getByText("09:30–10:30")).toBeTruthy();
    expect(block.classList.contains("timeline-patient-block")).toBe(true);
  });

  test("overlapping patients are both visible as separate patient blocks", async () => {
    renderDashboard();
    const first = await findPatientBlock(/Kratki Pregled/);
    const second = await findPatientBlock(/Preklop Pacijent/);
    expect(first).toBeTruthy();
    expect(second).toBeTruthy();
    expect(first).not.toBe(second);
  });

  test("red-flag status uses red color and opens structured details", async () => {
    const user = userEvent.setup();
    renderDashboard();
    const block = await findPatientBlock(/Crvena Napomena/);
    expect(block.classList.contains("tone-red")).toBe(true);
    expect(within(block).getByLabelText(/Čeka pregled\/pretragu/).classList.contains("red")).toBe(true);
    await user.click(within(block).getByRole("button", { name: "2 crvenih napomena" }));
    expect(await screen.findByRole("dialog", { name: "Crvene napomene za Crvena Napomena" })).toBeTruthy();
    expect(screen.getByText("Pacijent je pio kavu s mlijekom.")).toBeTruthy();
    expect(screen.getByText("Pratnja nakon sedacije nije potvrđena.")).toBeTruthy();
  });

  test("completed and paid state is green and has no primary action", async () => {
    renderDashboard();
    const block = await findPatientBlock(/Plaćeno Gotovo/);
    expect(block.classList.contains("tone-green")).toBe(true);
    expect(within(block).getAllByText("Završeno").length).toBeGreaterThan(0);
    expect(within(block).queryByRole("button", { name: /Naplati|Otvori prijem|Otvori pregled/ })).toBeNull();
  });

  test("room view keeps rooms and activities in a horizontally scrollable timeline", async () => {
    const user = userEvent.setup();
    renderDashboard();
    await user.click(await screen.findByRole("button", { name: "Po prostorijama" }));
    expect(screen.getByLabelText("Raspored prostorije Ordinacija 1")).toBeTruthy();
    expect(screen.getByLabelText("Raspored prostorije Endoskopija 1")).toBeTruthy();
    expect(screen.getAllByText("Endoskopija 1").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Paket Gastro" })).toHaveLength(1);
  });

  test("missing end_time falls back to a short block without losing the activity", async () => {
    renderDashboard();
    const block = await findPatientBlock(/Bez Kraja/);
    expect(within(block).getByText("Kratka kontrola")).toBeTruthy();
    expect(within(block).getAllByText("14:00").length).toBeGreaterThan(0);
  });

  test("activities outside 07:00-20:00 extend the visible time axis", async () => {
    renderDashboard();
    expect(await screen.findByRole("button", { name: "Rani Pacijent" })).toBeTruthy();
    expect(screen.getAllByText("06:30").length).toBeGreaterThan(0);
    expect(screen.getAllByText("20:30").length).toBeGreaterThan(0);
  });

  test("each patient block exposes only one primary action and moves secondary actions to menu", async () => {
    renderDashboard();
    const block = await findPatientBlock(/Kratki Pregled/);
    expect(within(block).getByRole("button", { name: "Otvori prijem" })).toBeTruthy();
    expect(within(block).getByLabelText("Dodatne radnje za Kratki Pregled")).toBeTruthy();
    expect(within(block).getAllByText("Otvori prijem")).toHaveLength(1);
  });

  test("keyboard and screen-reader status includes accessible text label", async () => {
    renderDashboard();
    const block = await findPatientBlock(/Preklop Pacijent/);
    const status = within(block).getByLabelText(/Stigao. Otvorite prijem/);
    expect(status.getAttribute("tabindex")).toBe("0");
    expect(within(status).getByRole("tooltip").textContent).toContain("Stigao");
  });

  test("otvori prijem continues to open dashboard-native reception modal", async () => {
    const user = userEvent.setup();
    renderDashboard();
    const block = await findPatientBlock(/Kratki Pregled/);
    await user.click(within(block).getByRole("button", { name: "Otvori prijem" }));
    expect(await screen.findByRole("dialog", { name: "Opći podaci pacijenta" })).toBeTruthy();
    expect(screen.queryByText("Otvoren radni prostor")).toBeNull();
  });

  test("otvori pregled opens canonical clinical workspace", async () => {
    const user = userEvent.setup();
    renderDashboard();
    const block = await findPatientBlock(/Paket Gastro/);
    await user.click(within(block).getByRole("button", { name: "Otvori pregled" }));
    expect(await screen.findByText("Otvoren radni prostor")).toBeTruthy();
  });

  test("filters and physician scoping are preserved", async () => {
    const user = userEvent.setup();
    renderDashboard();
    expect(await screen.findByText("Prikaz: Svi liječnici")).toBeTruthy();
    await user.type(screen.getByRole("textbox", { name: /Pretraži pacijenta/ }), "Gastro");
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/dashboard\/day\?.*q=Gastro/), expect.anything()));
    const advanced = screen.getByText("Dodatni filtri").closest("details") as HTMLDetailsElement;
    await user.click(advanced.querySelector("summary") as HTMLElement);
    await user.selectOptions(screen.getByRole("combobox", { name: "Klinika" }), "2");
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/dashboard\/day\?.*clinic_id=2/), expect.anything()));
  });
});
