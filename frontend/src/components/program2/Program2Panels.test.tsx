import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AISummaryPanel, BlockerPanel, CheckInChecklist, ConsumablesPanel, PreparationPanel } from "./Program2Panels";

afterEach(() => cleanup());

describe("radnje u radnom prostoru tijeka pacijenta", () => {
  test("sprema izmijenjenu stavku prijemne provjere", async () => {
    const user = userEvent.setup();
    const onUpdate = vi.fn().mockResolvedValue(undefined);
    render(<CheckInChecklist data={{ items: [{ id: 7, label: "Identitet potvrđen", state: "not_confirmed", note: null, requires_clinician: false }] }} onUpdate={onUpdate}/>);

    await user.selectOptions(screen.getByLabelText("Identitet potvrđen — stanje"), "confirmed");
    await user.type(screen.getByLabelText("Identitet potvrđen — napomena"), "Provjeren dokument");
    await user.click(screen.getByRole("button", { name: "Spremi" }));

    expect(onUpdate).toHaveBeenCalledWith(7, "confirmed", "Provjeren dokument");
  });

  test("odmah sprema odluku o stavci pripreme", async () => {
    const user = userEvent.setup();
    const onUpdate = vi.fn().mockResolvedValue(undefined);
    render(<PreparationPanel status="in_progress" data={{ template: { name: "Gastroskopija", version: 2, requirements_json: [{ key: "fasting", label: "Natašte" }] }, requirement_states_json: { fasting: "not_confirmed" } }} onUpdate={onUpdate}/>);

    await user.selectOptions(screen.getByRole("combobox"), "confirmed");
    expect(onUpdate).toHaveBeenCalledWith("fasting", "confirmed");
  });

  test("liječnik prihvaća samo pojedinačnu izvorno povezanu činjenicu", async () => {
    const user = userEvent.setup();
    const onReview = vi.fn().mockResolvedValue(undefined);
    render(<AISummaryPanel summary={{ id: 3, status: "pending_review", model_name: "local-stub", generated_at: "2026-07-13T08:00:00Z", limitations_json: [], facts: [{ id: 9, statement: "Navod iz dokumenta", fact_type: "nalaz", review_status: "pending_review", source_document_id: 4 }] }} onReview={onReview}/>);

    await user.click(screen.getByRole("button", { name: "Prihvati činjenicu" }));
    expect(onReview).toHaveBeenCalledWith(3, 9, "accept");
  });

  test("traži bilješku prije razrješenja blokatora", async () => {
    const user = userEvent.setup();
    const onResolve = vi.fn().mockResolvedValue(undefined);
    render(<BlockerPanel items={[{ id: 5, status: "open", title: "Nedostaje nalaz", details: "Potrebna je provjera liječnika." }]} onResolve={onResolve}/>);

    const button = screen.getByRole("button", { name: "Razriješi blokator" });
    expect((button as HTMLButtonElement).disabled).toBe(true);
    await user.type(screen.getByLabelText("Razrješenje — Nedostaje nalaz"), "Liječnik pregledao izvor");
    await user.click(button);
    expect(onResolve).toHaveBeenCalledWith(5, "Liječnik pregledao izvor");
  });

  test("potvrđuje odabrani potrošni materijal i količinu", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    const item = { id: 12, sku: "SYN-12", name: "Sintetička kanila", unit_of_measure: "kom", current_stock: "10", minimum_stock: "2", reorder_point: "3", purchase_price: "1.00", selling_price: "2.00" };
    render(<ConsumablesPanel status="pending" canConfirm items={[item]} onConfirm={onConfirm}/>);

    await user.selectOptions(screen.getByLabelText("Materijal 1"), "12");
    const quantity = screen.getByLabelText("Količina 1");
    await user.clear(quantity);
    await user.type(quantity, "2");
    await user.click(screen.getByRole("button", { name: "Potvrdi materijal" }));
    expect(onConfirm).toHaveBeenCalledWith([{ inventory_item_id: 12, quantity: "2", reason: undefined }], false);
  });
});
