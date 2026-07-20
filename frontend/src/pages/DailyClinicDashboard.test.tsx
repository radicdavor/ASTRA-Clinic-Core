import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DailyClinicDashboard } from "./DailyClinicDashboard";

const rows = [
  {
    journey_id: 11, appointment_id: 101, time: "08:00:00", patient_name: "Sintetički Dolazak",
    service_id: 1, service_name: "Prvi pregled", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", clinic_id: 1, clinic_name: "Klinika Sjever", intake_channel: "manual", workflow_stage: "ready_for_arrival",
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
    activity_count: 2, current_activity_id: 132, next_activity_id: null, activities: [
      { id: 131, sequence: 1, time: "10:00:00", service_name: "Gastro pregled", clinician_name: "dr. Test", room_name: "Ordinacija 1", status: "completed" },
      { id: 132, sequence: 2, time: "10:30:00", service_name: "Gastroskopija", clinician_name: "dr. Test", room_name: "Endoskopija 1", status: "in_progress" },
    ],
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
    journey_id: 18, appointment_id: 108, time: "13:30:00", patient_name: "Sintetički Dokumenti",
    service_id: 1, service_name: "Gastroskopija", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", intake_channel: "manual", workflow_stage: "awaiting_documents",
    document_status: "requested", preparation_status: "complete", arrival_status: "not_arrived",
    check_in_status: "not_arrived", encounter_status: "not_started", consumables_status: "not_ready",
    billing_status: "not_ready", payment_status: "not_due", blocker_status: "clear", blocker_labels: [], blockers: [], allowed_actions: ["open_check_in"],
  },
  {
    journey_id: 19, appointment_id: 109, time: "13:45:00", patient_name: "Sintetički Priprema",
    service_id: 1, service_name: "Gastroskopija", clinician_id: 1, clinician_name: "dr. Test",
    room_id: 1, room_name: "Ordinacija 1", intake_channel: "manual", workflow_stage: "preparation_in_progress",
    document_status: "complete", preparation_status: "in_progress", arrival_status: "not_arrived",
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

let dashboardAccess: {
  viewer_role: string; scope: string; scope_label: string; scoped_clinician_id: number | null;
  can_filter_clinician: boolean; available_clinics: Array<{ id: number; name: string }>;
} = {
  viewer_role: "admin", scope: "all", scope_label: "Svi liječnici", scoped_clinician_id: null,
  can_filter_clinician: true,
  available_clinics: [{ id: 1, name: "Klinika Sjever" }, { id: 2, name: "Klinika Jug" }],
};

function response(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

function journeyResponse(id: number) {
  return {
    id, patient_id: 501, appointment_id: 106, intake_channel: "manual", current_stage: "ready_for_arrival",
    document_status: "complete", preparation_status: "complete", check_in_status: "not_arrived",
    encounter_status: "not_started", consumables_status: "not_ready", billing_status: "not_ready",
    payment_status: "not_due", closed_at: null, blockers: [], activities: [
      { id: 601, journey_id: id, appointment_id: 106, service_id: 1, activity_key: "Prvi pregled", activity_kind: "consultation", specialty_key: "gastroenterology", clinic_id: 1, primary_provider_id: 1, room_id: 1, sequence: 1, depends_on_activity_id: null, required: true, planned_start: "2026-07-13T13:00:00", planned_end: "2026-07-13T13:30:00", actual_start: null, actual_end: null, status: "ready", not_performed_reason: null, form_resolution_status: "not_started", billing_status: "not_ready", consumables_status: "not_ready" },
      { id: 602, journey_id: id, appointment_id: 106, service_id: 1, activity_key: "Gastroskopija", activity_kind: "procedure", specialty_key: "gastroenterology", clinic_id: 1, primary_provider_id: 1, room_id: 1, sequence: 2, depends_on_activity_id: null, required: true, planned_start: "2026-07-13T13:30:00", planned_end: "2026-07-13T14:00:00", actual_start: null, actual_end: null, status: "ready", not_performed_reason: null, form_resolution_status: "not_started", billing_status: "not_ready", consumables_status: "not_ready" },
    ],
    patient: {
      id: 501, first_name: "Sintetički", last_name: "Čeka", date_of_birth: "1992-01-06",
      oib: null, email: "synthetic@example.com", phone: "0994477445", notes: null, email_verified_at: null, updated_at: "2026-07-13T10:00:00Z",
    },
    appointment: {
      id: 106, service_id: 1, provider_id: 1, room_id: 1, date: "2026-07-13",
      start_time: "13:00:00", end_time: "13:30:00", status: "booked", source: "manual",
      service: { id: 1, name: "Kontrola" }, provider: { id: 1, full_name: "dr. Test" }, room: { id: 1, name: "Ordinacija 1" },
    },
  };
}

function installFetchMock() {
  return vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    const url = String(input);
    if (url.includes("/api/dashboard/day")) return response({ date: "2026-07-13", refreshed_at: "2026-07-13T08:00:00Z", visible_sections: [], ...dashboardAccess, rows });
    if (url.endsWith("/api/providers")) return response([{ id: 1, full_name: "dr. Test", staff_role: "physician" }]);
    if (url.endsWith("/api/rooms") || url.endsWith("/api/services")) return response([]);
    if (/\/api\/patient-journeys\/\d+$/.test(url)) return response(journeyResponse(Number(url.split("/").pop())));
    if (url.endsWith("/api/patients/501") && init?.method === "PATCH") return response({ updated_at: "2026-07-13T10:05:00Z" });
    if (url.endsWith("/api/patient-journeys/16/check-in") && init?.method === "POST") return response({ id: 1, journey_id: 16, status: "in_review", arrived_at: "2026-07-13T11:00:00Z", completed_at: null, items: [] });
    if (url.endsWith("/api/patient-journeys/16/check-in/complete-reception") && init?.method === "POST") return response({ id: 1, journey_id: 16, status: "ready", arrived_at: "2026-07-13T11:00:00Z", completed_at: "2026-07-13T11:05:00Z", items: [] });
    if (init?.method === "POST") return response({});
    throw new Error(`Neočekivani testni API poziv: ${url}`);
  });
}

function renderDashboard() {
  return render(<MemoryRouter initialEntries={["/"]}><Routes><Route path="/" element={<DailyClinicDashboard/>}/><Route path="/journeys/:id" element={<p>Otvoren radni prostor</p>}/></Routes></MemoryRouter>);
}

beforeEach(() => {
  dashboardAccess = { viewer_role: "admin", scope: "all", scope_label: "Svi liječnici", scoped_clinician_id: null, can_filter_clinician: true, available_clinics: [{ id: 1, name: "Klinika Sjever" }, { id: 2, name: "Klinika Jug" }] };
  installFetchMock(); vi.spyOn(window, "confirm").mockReturnValue(true);
});
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

  test("otvaranje prijema ostaje na dnevnoj ploči i otvara float prozor", async () => {
    const user = userEvent.setup(); renderDashboard();
    const row = (await screen.findByText("Sintetički Čeka")).closest("tr") as HTMLTableRowElement;
    await user.click(within(row).getByRole("button", { name: "Otvori prijem" }));
    expect(await screen.findByRole("dialog", { name: "Opći podaci pacijenta" })).toBeTruthy();
    expect(screen.queryByText("Otvoren radni prostor")).toBeNull();
    expect(fetch).not.toHaveBeenCalledWith(expect.stringContaining("/api/patient-journeys/16/check-in"), expect.objectContaining({ method: "POST" }));
  });

  test("red flag prijem ima ciljane dropdownove i šalje activity provenance", async () => {
    const user = userEvent.setup(); renderDashboard();
    const row = (await screen.findByRole("link", { name: /Sinteti.*eka/ })).closest("tr") as HTMLTableRowElement;
    await user.click(within(row).getByRole("button", { name: "Otvori prijem" }));
    await user.click(await screen.findByRole("button", { name: "Podaci su točni" }));
    await user.click(await screen.findByLabelText(/Problem s postom/));
    await user.selectOptions(screen.getByLabelText("Zadnji unos"), "2–4 sata");
    await user.selectOptions(screen.getByLabelText("Vrsta unosa"), "kava s mlijekom");
    await user.selectOptions(screen.getByLabelText("Odnosi se na aktivnost"), "602");
    await user.click(screen.getByRole("button", { name: "Provjereno" }));

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/patient-journeys/16/check-in/complete-reception"), expect.anything()));
    const completionCall = vi.mocked(fetch).mock.calls.find(([url]) => String(url).includes("/api/patient-journeys/16/check-in/complete-reception"));
    const body = JSON.parse(String(completionCall?.[1]?.body));
    expect(body.items[0].item_key).toBe("fasting_6h");
    expect(body.items[0].details).toMatchObject({ last_intake_timing: "2–4 sata", intake_type: "kava s mlijekom" });
    expect(body.items[0].activity_ids).toEqual([602]);
  });

  test("floating prijem salje expected version i visit-scoped napomenu bez patient.notes", async () => {
    const user = userEvent.setup(); renderDashboard();
    const row = (await screen.findByRole("link", { name: /Sinteti.*eka/ })).closest("tr") as HTMLTableRowElement;
    await user.click(within(row).getByRole("button", { name: "Otvori prijem" }));
    await user.clear(await screen.findByLabelText("Telefon"));
    await user.type(screen.getByLabelText("Telefon"), "091222333");
    await user.type(screen.getByLabelText("Napomena za današnji dolazak"), "Pacijent treba pomoc pri kretanju.");
    await user.click(await screen.findByRole("button", { name: "Podaci su točni" }));
    await user.click(await screen.findByRole("button", { name: "Provjereno" }));

    const patientCall = vi.mocked(fetch).mock.calls.find(([url, init]) => String(url).endsWith("/api/patients/501") && init?.method === "PATCH");
    const patientPayload = JSON.parse(String(patientCall?.[1]?.body));
    expect(patientPayload).toMatchObject({ expected_updated_at: "2026-07-13T10:00:00Z", phone: "091222333" });
    expect(patientPayload.notes).toBeUndefined();
    const completionCall = vi.mocked(fetch).mock.calls.find(([url]) => String(url).includes("/api/patient-journeys/16/check-in/complete-reception"));
    const completionPayload = JSON.parse(String(completionCall?.[1]?.body));
    expect(completionPayload.reception_note).toBe("Pacijent treba pomoc pri kretanju.");
  });

  test("zatvaranje prijema čuva filter, prikaz i fokus na istom retku", async () => {
    const user = userEvent.setup(); renderDashboard();
    const search = await screen.findByRole("textbox", { name: /Pretra/ });
    await user.type(search, "Čeka");
    await user.click(screen.getByRole("button", { name: "Po prostorijama" }));
    await user.click(screen.getByRole("button", { name: "Po pacijentima" }));
    const row = (await screen.findByRole("link", { name: /Sinteti.*eka/ })).closest("tr") as HTMLTableRowElement;
    const button = within(row).getByRole("button", { name: "Otvori prijem" });
    await user.click(button);
    await user.click(await screen.findByRole("button", { name: "Zatvori prijem" }));
    await waitFor(() => expect(document.activeElement).toBe(button));
    expect((screen.getByRole("textbox", { name: /Pretra/ }) as HTMLInputElement).value).toBe("Čeka");
    expect(screen.getByRole("button", { name: "Po pacijentima" }).classList.contains("active")).toBe(true);
  });

  test("za pacijenta koji je stigao prikazuje samo Otvori prijem", async () => {
    renderDashboard();
    const row = (await screen.findByText("Sintetički Prijem")).closest("tr") as HTMLTableRowElement;
    expect(within(row).getByText("Stigao")).toBeTruthy();
    expect(within(row).getByRole("button", { name: "Otvori prijem" })).toBeTruthy();
    expect(within(row).getByRole("link", { name: /Sinteti.*Prijem/ })).toBeTruthy();
  });

  test("nalaze koje pacijent donosi ne prikazuje kao uvjet za pregled", async () => {
    renderDashboard();
    const row = (await screen.findByText("Sintetički Dokumenti")).closest("tr") as HTMLTableRowElement;
    expect(within(row).getByText("Naručen")).toBeTruthy();
    expect(within(row).getAllByText(/to ne blokira početak pregleda/).length).toBeGreaterThan(0);
    expect(within(row).queryByText("Nalazi za pregled")).toBeNull();
    expect(within(row).queryByText("Potrebna priprema")).toBeNull();
  });

  test("pripremu prije dolaska ne prikazuje kao dodatni administrativni alarm", async () => {
    renderDashboard();
    const row = (await screen.findByText("Sintetički Priprema")).closest("tr") as HTMLTableRowElement;
    expect(within(row).getByText("Naručen")).toBeTruthy();
    expect(within(row).getByText("Priprema će se kratko provjeriti u prijemu.")).toBeTruthy();
    expect(within(row).queryByText("Potrebna priprema")).toBeNull();
  });

  test("pregled, materijal i naplata dobivaju po jednu kontekstualnu radnju", async () => {
    renderDashboard();
    expect(await screen.findByRole("button", { name: "Otvori pregled" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Evidentiraj materijal" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Naplati" })).toBeTruthy();
  });

  test("više usluga ostaje u jednom retku s jasnom tračnicom aktivnosti", async () => {
    renderDashboard();
    const row = (await screen.findByText("2 aktivnosti")).closest("tr") as HTMLTableRowElement;
    expect(within(row).getByText(/10:00 Gastro pregled/)).toBeTruthy();
    expect(within(row).getByText(/10:30 Gastroskopija/)).toBeTruthy();
    expect(within(row).getByLabelText(/Gastroskopija. U tijeku/).classList.contains("active")).toBe(true);
  });

  test("naplata otvara postojeći račun bez dodatne mutacije", async () => {
    const user = userEvent.setup(); renderDashboard();
    await user.click(await screen.findByRole("button", { name: "Naplati" }));
    expect(await screen.findByText("Otvoren radni prostor")).toBeTruthy();
    expect(fetch).not.toHaveBeenCalledWith(expect.stringContaining("/billing/prepare"), expect.anything());
  });

  test("pretragu pacijenta šalje dnevnom API-ju", async () => {
    const user = userEvent.setup(); renderDashboard();
    const search = await screen.findByRole("textbox", { name: /Pretra/ });
    await user.type(search, "Dolazak");
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/dashboard\/day\?.*q=Dolazak/), expect.anything()));
  });

  test("administrator vidi sve liječnike i filter klinike kada ih ima više", async () => {
    const user = userEvent.setup(); renderDashboard();
    expect(await screen.findByText("Prikaz: Svi liječnici")).toBeTruthy();
    expect(screen.getByRole("combobox", { name: "Liječnik" })).toBeTruthy();
    const advanced = screen.getByText("Dodatni filtri").closest("details") as HTMLDetailsElement;
    expect(advanced.open).toBe(false);
    await user.click(advanced.querySelector("summary") as HTMLElement);
    expect(advanced.open).toBe(true);
    const clinic = screen.getByRole("combobox", { name: "Klinika" });
    await user.selectOptions(clinic, "2");
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/dashboard\/day\?.*clinic_id=2/), expect.anything()));
  });

  test("liječnik vidi vlastiti opseg bez filtera drugih liječnika", async () => {
    dashboardAccess = { viewer_role: "physician", scope: "own_clinician", scope_label: "dr. Test", scoped_clinician_id: 1, can_filter_clinician: false, available_clinics: [{ id: 1, name: "Klinika Sjever" }] };
    renderDashboard();
    expect(await screen.findByText("Prikaz: dr. Test")).toBeTruthy();
    expect(screen.queryByRole("combobox", { name: "Liječnik" })).toBeNull();
    expect(screen.queryByRole("combobox", { name: "Klinika" })).toBeNull();
  });

  test("zadano prikazuje samo pretragu, problem i liječnika, a ostalo skriva", async () => {
    const user = userEvent.setup(); renderDashboard();
    await screen.findByText("Sintetički Dolazak");
    expect(screen.getByRole("textbox", { name: /Pretra/ })).toBeTruthy();
    expect(screen.getByRole("combobox", { name: "Problem" })).toBeTruthy();
    const advanced = screen.getByText("Dodatni filtri").closest("details") as HTMLDetailsElement;
    expect(advanced.open).toBe(false);
    await user.click(advanced.querySelector("summary") as HTMLElement);
    expect(advanced.open).toBe(true);
    expect(screen.getByRole("combobox", { name: "Prostorija" })).toBeTruthy();
  });
});
