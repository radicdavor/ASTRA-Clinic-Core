import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RouteModal } from "../components/RouteModal";
import { KnowledgeProtocolDetail } from "./KnowledgeProtocolDetail";
import { KnowledgeProtocols } from "./KnowledgeProtocols";

const protocol = {
  id: 7,
  key: "synthetic-protocol",
  title: "Sintetički protokol za gastroskopiju",
  specialty: "Gastroenterologija",
  version: "1.0",
  summary: "Detaljno objašnjenje protokola koje ne pripada osnovnom popisu.",
  source_title: "Sintetički stručni izvor",
  source_url: "https://example.test/protocol",
  status: "reviewed",
  reviewed_by: 1,
  reviewed_at: "2026-07-14T08:00:00Z",
  rules: [{ id: 1, protocol_id: 7, label: "Priprema", condition_text: "Kada je indicirano.", guidance_text: "Postupiti prema pregledanom izvoru.", evidence_level: "A", position: 0 }],
  created_at: "2026-07-14T08:00:00Z",
  updated_at: "2026-07-14T08:00:00Z",
};

function response(body: unknown) {
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } }));
}

beforeEach(() => {
  vi.spyOn(globalThis, "fetch").mockImplementation(input => response(String(input).endsWith("/api/knowledge-protocols") ? [protocol] : protocol));
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

function renderLibrary() {
  return render(<MemoryRouter initialEntries={["/knowledge"]}><Routes>
    <Route path="/knowledge" element={<KnowledgeProtocols/>}/>
    <Route path="/knowledge/:id" element={<RouteModal title="Klinički protokol"><KnowledgeProtocolDetail/></RouteModal>}/>
  </Routes></MemoryRouter>);
}

describe("sažeta klinička knjižnica", () => {
  test("u katalogu prikazuje samo naslov dokumenta", async () => {
    renderLibrary();
    const list = await screen.findByRole("region", { name: "Dokumenti kliničke knjižnice" });
    expect(within(list).getByRole("heading", { name: protocol.title })).toBeTruthy();
    expect(within(list).queryByText(protocol.summary)).toBeNull();
    expect(within(list).queryByText(protocol.specialty)).toBeNull();
    expect(within(list).queryByText("reviewed")).toBeNull();
  });

  test("klik na naslov otvara objašnjenje u modalnom prozoru", async () => {
    const user = userEvent.setup(); renderLibrary();
    await user.click(await screen.findByRole("link", { name: protocol.title }));
    const dialog = await screen.findByRole("dialog");
    await waitFor(() => expect(within(dialog).getByText(protocol.summary)).toBeTruthy());
    expect(within(dialog).getByRole("heading", { name: protocol.title })).toBeTruthy();
    expect(within(dialog).getByRole("button", { name: "Zatvori prozor" })).toBeTruthy();
  });

  test("postupanja prikazuje kao naslove i objašnjenje otvara ispod odabranog naslova", async () => {
    const user = userEvent.setup(); renderLibrary();
    await user.click(await screen.findByRole("link", { name: protocol.title }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByRole("heading", { name: "Priprema" })).toBeTruthy();
    expect(within(dialog).queryByText("Kada je indicirano.")).toBeNull();
    expect(within(dialog).queryByText("Postupiti prema pregledanom izvoru.")).toBeNull();

    const showButton = within(dialog).getByRole("button", { name: "Prikaži objašnjenje: Priprema" });
    expect(showButton.getAttribute("aria-expanded")).toBe("false");
    await user.click(showButton);
    expect(within(dialog).getByText("Kada je indicirano.")).toBeTruthy();
    expect(within(dialog).getByText("Postupiti prema pregledanom izvoru.")).toBeTruthy();

    const hideButton = within(dialog).getByRole("button", { name: "Sakrij objašnjenje: Priprema" });
    expect(hideButton.getAttribute("aria-expanded")).toBe("true");
    await user.click(hideButton);
    expect(within(dialog).queryByText("Kada je indicirano.")).toBeNull();
  });
});
