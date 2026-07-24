import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AuditLog } from "./AuditLog";

const events = [
  {
    id: 1,
    scope_type: "clinic",
    scope_label: "Sintetička klinika",
    clinic_id: 7,
    institution_id: 3,
    actor_type: "user",
    actor_user_id: 9,
    actor_name: "Demo Administrator",
    action: "clinical_document_reviewed",
    entity_type: "ClinicalDocument",
    entity_id: 44,
    request_id: "request-safe-1",
    changed_fields: ["status"],
    status: "reviewed",
    reason_code: null,
    result: "success",
    created_at: "2026-07-23T08:00:00Z",
    before_json: { raw_text: "PHI_BEFORE_SENTINEL" },
    after_json: { token: "TOKEN_VALUE_SENTINEL" },
  },
  {
    id: 2,
    scope_type: "clinic",
    scope_label: "Sintetička klinika",
    clinic_id: 7,
    institution_id: 3,
    actor_type: "user",
    actor_user_id: 9,
    actor_name: "Demo Administrator",
    action: "access_denied",
    entity_type: "Patient",
    entity_id: 55,
    request_id: "request-safe-2",
    changed_fields: [],
    status: null,
    reason_code: "foreign_scope",
    result: "denied",
    created_at: "2026-07-23T09:00:00Z",
  },
];

function json(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

function renderPage() {
  return render(<MemoryRouter><AuditLog /></MemoryRouter>);
}

describe("operativna evidencija aktivnosti", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  test("prikazuje razumljiv PHI-safe sažetak i šest primarnih stupaca", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => json(events));
    renderPage();

    const table = await screen.findByRole("table", { name: "Evidencija aktivnosti" });
    expect(within(table).getAllByRole("columnheader").map((header) => header.textContent)).toEqual([
      "Vrijeme", "Korisnik", "Radnja", "Objekt", "Scope", "Rezultat",
    ]);
    expect(within(table).getByText("Dokument pregledan")).toBeTruthy();
    expect(within(table).getByText("Pristup odbijen")).toBeTruthy();
    expect(within(table).getAllByText("Sintetička klinika")).toHaveLength(2);
    expect(within(table).queryByText("request-safe-1")).toBeNull();
    expect(document.body.textContent).not.toContain("PHI_BEFORE_SENTINEL");
    expect(document.body.textContent).not.toContain("TOKEN_VALUE_SENTINEL");
  });

  test("tehničke detalje prikazuje samo u draweru i vraća fokus", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => json(events));
    renderPage();
    const detailButton = (await screen.findAllByRole("button", { name: /Klinički dokument/ }))[0];
    detailButton.focus();
    fireEvent.click(detailButton);

    const dialog = screen.getByRole("dialog", { name: "Tehnički detalj događaja" });
    expect(within(dialog).getByText("clinical_document_reviewed")).toBeTruthy();
    expect(within(dialog).getByText("ClinicalDocument #44")).toBeTruthy();
    expect(within(dialog).getByText("request-safe-1")).toBeTruthy();
    expect(within(dialog).getByText("status")).toBeTruthy();
    expect(within(dialog).queryByText("PHI_BEFORE_SENTINEL")).toBeNull();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(detailButton);
  });

  test("filtrira odbijene događaje i jasno prikazuje scope", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => json(events));
    renderPage();
    await screen.findByRole("table", { name: "Evidencija aktivnosti" });

    fireEvent.change(screen.getByLabelText("Rezultat"), { target: { value: "denied" } });
    const table = screen.getByRole("table", { name: "Evidencija aktivnosti" });
    expect(within(table).getByText("Pristup odbijen")).toBeTruthy();
    expect(within(table).queryByText("Dokument pregledan")).toBeNull();
    expect(screen.getByText("Prikaz:").parentElement?.textContent).toContain("Sintetička klinika");
  });

  test("zabranu pristupa ne prikazuje kao praznu evidenciju", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => json({ detail: "Zabranjeno" }, 403));
    renderPage();

    expect(await screen.findByText("Nemate dozvolu")).toBeTruthy();
    expect(screen.queryByText("Nema događaja")).toBeNull();
  });
});
