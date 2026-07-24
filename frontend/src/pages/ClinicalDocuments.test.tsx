import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClinicalDocuments } from "./ClinicalDocuments";

const patient = {
  id: 12,
  first_name: "Sintetička",
  last_name: "Pacijentica",
  date_of_birth: "1990-02-03",
  oib: null,
  phone: null,
  email: "synthetic@example.com",
  notes: null,
  updated_at: "2026-07-23T08:00:00Z",
};

function document(overrides: Record<string, unknown> = {}) {
  return {
    id: 41,
    patient_id: 12,
    patient,
    source_type: "uploaded",
    document_type: "laboratory",
    origin: "Sintetički laboratorij",
    document_date: "2026-07-22",
    title: "Sintetički laboratorijski nalaz",
    ai_extraction_status: "generated",
    physician_reviewed: false,
    review_status: "needs_physician_review",
    record_classification: "clinical",
    created_at: "2026-07-22T08:00:00Z",
    updated_at: "2026-07-22T08:00:00Z",
    ...overrides,
  };
}

function json(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/clinical-documents"]}>
      <Routes>
        <Route path="/clinical-documents" element={<ClinicalDocuments />} />
        <Route path="/clinical-documents/:id" element={<div>Detalj dokumenta</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("operativni popis kliničkih dokumenata", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  test("prikazuje samo šest primarnih stupaca, jedan status i jednu radnju", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/api/clinical-documents")) return json([document()]);
      return json([]);
    });
    renderPage();

    const table = await screen.findByRole("table", { name: "Klinički dokumenti" });
    expect(within(table).getAllByRole("columnheader").map((header) => header.textContent)).toEqual([
      "Pacijent",
      "Dokument",
      "Datum",
      "Tip",
      "Status",
      "Radnja",
    ]);
    expect(within(table).queryByRole("columnheader", { name: "Izvor" })).toBeNull();
    expect(within(table).queryByRole("columnheader", { name: "Klasifikacija" })).toBeNull();
    expect(within(table).queryByRole("columnheader", { name: "AI ekstrakcija" })).toBeNull();
    expect(within(table).getByLabelText("Čeka liječnički pregled")).toBeTruthy();
    expect(within(table).getAllByRole("link", { name: "Pregledaj" })).toHaveLength(1);

    const urls = fetchMock.mock.calls.map(([input]) => String(input));
    expect(urls.filter((url) => url.includes("/api/clinical-documents"))).toHaveLength(1);
    expect(urls.some((url) => /clinical-documents\/41/.test(url))).toBe(false);
    expect(urls.some((url) => url.includes("__no_patient__"))).toBe(false);
  });

  test("patient autocomplete bira identitet bez izlaganja sirovog ID filtra", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/api/patients?q=Sint")) return json([patient]);
      if (url.includes("/api/clinical-documents")) return json([document()]);
      return json([]);
    });
    renderPage();
    await screen.findByRole("table", { name: "Klinički dokumenti" });

    expect(screen.queryByPlaceholderText("Patient ID")).toBeNull();
    fireEvent.change(screen.getByRole("textbox", { name: "Pacijent" }), { target: { value: "Sint" } });
    const result = await screen.findByRole("option", { name: "Sintetička Pacijentica" });
    fireEvent.click(result);

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map(([input]) => String(input));
      expect(urls.some((url) => url.includes("patient_id=12"))).toBe(true);
    });
    expect(screen.getByLabelText("Aktivni filtri").textContent).toContain("Pacijent: Sintetička Pacijentica");
  });

  test("primarna radnja slijedi operativni status", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      if (String(input).includes("/api/clinical-documents")) {
        return json([
          document({ id: 1, record_classification: "unclassified", review_status: "draft" }),
          document({ id: 2, review_status: "reviewed", physician_reviewed: true }),
        ]);
      }
      return json([]);
    });
    renderPage();

    expect(await screen.findByRole("link", { name: "Dovrši klasifikaciju" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Otvori" })).toBeTruthy();
    expect(screen.getByLabelText("Čeka klasifikaciju")).toBeTruthy();
    expect(screen.getByLabelText("Pregledano")).toBeTruthy();
  });

  test("razlikuje zabranu pristupa od praznog rezultata i tehničke greške", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => json({ detail: "Zabranjeno" }, 403));
    const { unmount } = renderPage();
    expect(await screen.findByText("Nemate dozvolu")).toBeTruthy();
    expect(screen.queryByText("Nema dokumenata")).toBeNull();
    unmount();

    fetchMock.mockImplementation(() => json([], 200));
    renderPage();
    expect(await screen.findByText("Nema dokumenata")).toBeTruthy();
  });

  test("tekstualna pretraga je odgođena i prethodni request se prekida", async () => {
    const signals: AbortSignal[] = [];
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url.includes("/api/clinical-documents")) {
        if (init?.signal) signals.push(init.signal);
        return json([document()]);
      }
      return json([]);
    });
    renderPage();
    await screen.findByRole("table", { name: "Klinički dokumenti" });

    const search = screen.getByRole("textbox", { name: "Pretraži dokumente" });
    fireEvent.change(search, { target: { value: "prvi" } });
    fireEvent.change(search, { target: { value: "drugi" } });

    await waitFor(() => {
      expect(fetchMock.mock.calls.some(([input]) => String(input).includes("q=drugi"))).toBe(true);
    }, { timeout: 1000 });
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes("q=prvi"))).toBe(false);
    expect(signals[0]?.aborted).toBe(true);
  });
});
