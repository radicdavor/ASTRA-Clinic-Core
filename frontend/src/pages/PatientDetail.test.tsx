import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PatientDetail } from "./PatientDetail";

const patient = {
  id: 7,
  first_name: "Sintetička",
  last_name: "Pacijentica",
  date_of_birth: "1990-02-03",
  oib: "DEMO-OIB",
  phone: "0990000000",
  email: "synthetic@example.com",
  notes: "Demo zapis"
};

const clinicalDocument = {
  id: 21,
  patient_id: 7,
  source_type: "uploaded",
  document_type: "laboratory",
  document_date: "2026-07-20",
  title: "Sintetički laboratorijski nalaz",
  ai_extraction_status: "generated",
  physician_reviewed: false,
  review_status: "needs_physician_review",
  created_at: "2026-07-20T08:00:00Z",
  updated_at: "2026-07-20T08:00:00Z"
};

const clinicalSummary = {
  patient_id: 7,
  generated_from_reviewed_documents: 0,
  awaiting_review_count: 1,
  reviewed_summary: null,
  draft_summary: null,
  reviewed_summary_is_stale: false,
  draft_summary_is_stale: false,
  known_problems: [],
  completed_procedures: [],
  pathology: [],
  laboratory: [],
  imaging: [],
  current_therapy: [],
  open_questions: [],
  latest_recommendations: []
};

function response(body: unknown) {
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } }));
}

function installFetchMock() {
  return vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.endsWith("/api/patients/7")) return response(patient);
    if (url.includes("/api/patients/possible-duplicates")) return response([]);
    if (url.endsWith("/api/patients/7/clinical-documents")) return response([clinicalDocument]);
    if (url.endsWith("/api/patients/7/clinical-summary")) return response(clinicalSummary);
    if (url.endsWith("/api/patients/7/appointments")) return response([{
      appointment_id: 31,
      patient_id: 7,
      date: "2026-07-25",
      start_time: "09:00:00",
      end_time: "09:30:00",
      status: "booked",
      clinic: { id: 1, name: "Demo klinika" },
      service_name: "Prvi pregled",
      provider_name: "dr. Demo"
    }]);
    if (url.endsWith("/api/patients/7/workflow-tasks")) return response([]);
    if (url.endsWith("/api/laboratory/orders?patient_id=7")) return response([]);
    if (url.endsWith("/api/therapies?patient_id=7")) return response([]);
    if (url.endsWith("/api/patients/7/invoices")) return response([]);
    if (url.endsWith("/api/patients/7/clinical-findings")) return response({ patient_id: 7, findings: [], count: 0, is_read_only: true, warning: "" });
    if (url.endsWith("/api/patients/7/clinical-evidence-timeline")) return response({ patient_id: 7, events: [], count: 0, is_read_only: true, warning: "" });
    if (url.endsWith("/api/audit-log?entity_type=Patient&entity_id=7")) return response([]);
    throw new Error(`Neočekivani API poziv: ${url}`);
  });
}

function renderPatient() {
  return render(
    <MemoryRouter initialEntries={["/patients/7"]}>
      <Routes><Route path="/patients/:id" element={<PatientDetail />} /></Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  installFetchMock();
});
afterEach(() => {
  cleanup();
});

describe("pojednostavljeni karton pacijenta", () => {
  test("prikazuje identitet, sljedeći termin, pet cjelina i samo jednu glavnu radnju", async () => {
    renderPatient();
    expect(await screen.findByRole("heading", { name: "Sintetička Pacijentica" })).toBeTruthy();
    expect(screen.getByText("03. 02. 1990.")).toBeTruthy();
    expect(screen.getByText("Prvi pregled · Demo klinika")).toBeTruthy();

    const tabs = screen.getByRole("tablist", { name: "Sadržaj kartona pacijenta" });
    expect(within(tabs).getAllByRole("tab")).toHaveLength(5);
    expect(screen.getByRole("link", { name: "Novi termin" })).toBeTruthy();
    expect(document.querySelector('summary[aria-label="Dodatne radnje za pacijenta"]')).toBeTruthy();
    expect(screen.queryByText("Klinički dokumenti")).toBeNull();
    expect(screen.queryByText("Audit zapisi")).toBeNull();
  });

  test("ne učitava teške cjeline dok ih korisnik ne otvori", async () => {
    const user = userEvent.setup();
    renderPatient();
    await screen.findByRole("heading", { name: "Sintetička Pacijentica" });

    const initialUrls = vi.mocked(fetch).mock.calls.map(([input]) => String(input));
    expect(initialUrls.some((url) => url.includes("/laboratory/orders"))).toBe(false);
    expect(initialUrls.some((url) => url.includes("/invoices"))).toBe(false);
    expect(initialUrls.some((url) => url.includes("/clinical-findings"))).toBe(false);
    expect(initialUrls.some((url) => url.includes("/audit-log"))).toBe(false);

    await user.click(screen.getByRole("tab", { name: "Laboratorij i terapije" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/laboratory/orders?patient_id=7"), expect.anything()));
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/therapies?patient_id=7"), expect.anything());

    await user.click(screen.getByRole("tab", { name: "Termini i računi" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/patients/7/invoices"), expect.anything()));

    await user.click(screen.getByRole("tab", { name: "Izvori i evidencija" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/patients/7/clinical-findings"), expect.anything()));
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/patients/7/clinical-evidence-timeline"), expect.anything());
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/audit-log?entity_type=Patient&entity_id=7"), expect.anything());
  });

  test("dokument koji čeka pregled ostaje vidljiv s vrstom, izvorom i statusom", async () => {
    const user = userEvent.setup();
    renderPatient();
    await screen.findByRole("heading", { name: "Sintetička Pacijentica" });
    await user.click(screen.getByRole("tab", { name: "Dokumenti (1)" }));

    const row = await screen.findByRole("row", { name: /Sintetički laboratorijski nalaz/ });
    expect(within(row).getByText("Sintetički laboratorijski nalaz")).toBeTruthy();
    expect(row.textContent).toContain("Laboratorij");
    expect(row.textContent).toContain("Preneseno");
    expect(row.textContent).toContain("Čeka liječnički pregled");
  });

  test("tipkovnica mijenja kontroliranu karticu i zadržava ispravan fokus", async () => {
    const user = userEvent.setup();
    renderPatient();
    const firstTab = await screen.findByRole("tab", { name: "Pregled" });
    firstTab.focus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "Dokumenti (1)" }).getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(screen.getByRole("tab", { name: "Dokumenti (1)" }));
  });
});
