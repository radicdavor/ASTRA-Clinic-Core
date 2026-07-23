import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Invoices } from "./Invoices";

const partial = {
  id: 1,
  patient_id: 10,
  patient_name: "Sintetička Pacijentica",
  invoice_number: "ASTRA-2026-1",
  invoice_date: "2026-07-23",
  status: "partially_paid",
  payment_status: "partially_paid",
  total_amount: "120.00",
  paid_amount: "40.00",
  outstanding_amount: "80.00",
  payment_count: 1,
  can_issue: true,
  can_record_payment: true,
};
const paid = {
  ...partial,
  id: 2,
  invoice_number: "ASTRA-2026-2",
  patient_name: "Plaćeni Pacijent",
  status: "paid",
  payment_status: "paid",
  paid_amount: "120.00",
  outstanding_amount: "0.00",
};

function detail(id = 1) {
  return {
    id,
    patient_id: 10,
    invoice_number: `ASTRA-2026-${id}`,
    invoice_date: "2026-07-23",
    status: id === 1 ? "partially_paid" : "paid",
    payment_status: id === 1 ? "partially_paid" : "paid",
    total_amount: "120.00",
    lines: [{ id: 4, invoice_id: id, description: "Sintetička usluga", quantity: "1", unit_price: "120.00", vat_rate: "25", total: "120.00" }],
    payments: [{ id: 5, invoice_id: id, amount: id === 1 ? "40.00" : "120.00", method: "card", paid_at: "2026-07-23T09:00:00Z" }],
  };
}

function json(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

function renderPage() {
  return render(<MemoryRouter><Invoices /></MemoryRouter>);
}

describe("operativni popis računa", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  test("prikazuje pacijenta, iznose, jedan status i jednu primarnu radnju", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      if (String(input).includes("/api/invoices/operational-list")) return json([partial, paid]);
      return json(detail());
    });
    renderPage();

    const table = await screen.findByRole("table", { name: "Računi i plaćanja" });
    expect(within(table).getAllByRole("columnheader").map((header) => header.textContent)).toEqual([
      "Pacijent", "Datum", "Iznos", "Otvoreno", "Status", "Radnja",
    ]);
    expect(within(table).getByLabelText(/Djelomično plaćen/)).toBeTruthy();
    expect(within(table).getByLabelText("Plaćen")).toBeTruthy();
    expect(within(table).getByText("Plaćeno")).toBeTruthy();
    expect(within(table).getByRole("button", { name: "Nastavi naplatu" })).toBeTruthy();

    const urls = fetchMock.mock.calls.map(([input]) => String(input));
    expect(urls).toHaveLength(1);
    expect(urls[0]).toContain("/api/invoices/operational-list");
    expect(urls.some((url) => /\/api\/invoices\/1$/.test(url))).toBe(false);
    expect(urls.some((url) => url.includes("/payments"))).toBe(false);
  });

  test("stavke i povijest uplata dohvaća tek nakon otvaranja detalja", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/api/invoices/operational-list")) return json([partial]);
      if (/\/api\/invoices\/1$/.test(url)) return json(detail());
      return json([]);
    });
    renderPage();
    const action = await screen.findByRole("button", { name: "Nastavi naplatu" });

    expect(screen.queryByRole("table", { name: "Povijest uplata" })).toBeNull();
    fireEvent.click(action);

    const dialog = await screen.findByRole("dialog", { name: "ASTRA-2026-1" });
    expect(within(dialog).getByRole("table", { name: "Stavke računa" })).toBeTruthy();
    expect(within(dialog).getByRole("table", { name: "Povijest uplata" })).toBeTruthy();
    expect(fetchMock.mock.calls.filter(([input]) => /\/api\/invoices\/1$/.test(String(input)))).toHaveLength(1);
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/payments"))).toBe(false);
  });

  test("read-only capability ne prikazuje financijsku mutaciju", async () => {
    const readOnly = { ...partial, status: "issued", payment_status: "unpaid", can_issue: false, can_record_payment: false };
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      if (String(input).includes("/api/invoices/operational-list")) return json([readOnly]);
      return json({ ...detail(), status: "issued", payment_status: "unpaid" });
    });
    renderPage();

    const open = await screen.findByRole("button", { name: "Otvori račun" });
    fireEvent.click(open);
    const dialog = await screen.findByRole("dialog", { name: "ASTRA-2026-1" });
    await waitFor(() => expect(within(dialog).getByText("Stavke računa")).toBeTruthy());
    expect(within(dialog).queryByRole("button", { name: "Izdaj račun" })).toBeNull();
  });

  test("filtri su lokalni i prazno filtrirano stanje je jasno", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => json([partial]));
    renderPage();
    await screen.findByRole("table", { name: "Računi i plaćanja" });

    fireEvent.change(screen.getByRole("textbox", { name: "Pretraži račune" }), { target: { value: "ne postoji" } });
    expect(await screen.findByText("Nema rezultata za filtre")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Očisti" }));
    expect(await screen.findByRole("table", { name: "Računi i plaćanja" })).toBeTruthy();
  });
});
