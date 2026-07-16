import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AISummaryPanel, BlockerPanel, CheckInChecklist, ConsumablesPanel, EncounterPanel, PreparationPanel } from "./Program2Panels";

afterEach(() => cleanup());

describe("radnje u radnom prostoru tijeka pacijenta", () => {
  test("pregled prikazuje samo šest jasnih kliničkih cjelina", async () => {
    const user = userEvent.setup();
    const setDraft = vi.fn();
    render(<EncounterPanel draft={{}} setDraft={setDraft} status="in_progress" onOpen={vi.fn()} onSave={vi.fn()} onComplete={vi.fn()}/>);

    for (const label of ["Anamneza", "Status", "Nalazi koje pacijent donosi", "Mišljenje", "Preporuke", "Dijagnoze (WHO ICD-10)"]) {
      expect(screen.getByLabelText(label)).toBeTruthy();
    }
    expect(screen.queryByLabelText("Terapija")).toBeNull();
    await user.type(screen.getByLabelText("Mišljenje"), "Mišljenje liječnika");
    expect(setDraft).toHaveBeenLastCalledWith({ opinion: "a" });
  });

  test("AI prijedlozi ostaju odvojeni i prihvaćaju se ili odbijaju pojedinačno", async () => {
    const user = userEvent.setup();
    const onSuggestDiagnoses = vi.fn();
    const onDecideDiagnosis = vi.fn();
    const diagnosis = { code: "K21.9", title: "Gastroezofagealna refluksna bolest", provider: "openai" as const, model: "test-model", request_id: "synthetic-request" };
    render(<EncounterPanel draft={{ diagnosis: "" }} setDraft={vi.fn()} status="in_progress" aiDiagnoses={[diagnosis]} aiDiagnosisCapability={{ enabled: true, reason: null }} onOpen={vi.fn()} onSave={vi.fn()} onComplete={vi.fn()} onSuggestDiagnoses={onSuggestDiagnoses} onDecideDiagnosis={onDecideDiagnosis}/>);

    await user.click(screen.getByRole("button", { name: "AI predloži" }));
    expect(onSuggestDiagnoses).toHaveBeenCalledOnce();
    expect(screen.getByText("Nisu dio kliničkog nalaza dok ih liječnik pojedinačno ne prihvati.")).toBeTruthy();
    expect((screen.getByLabelText("Dijagnoze (WHO ICD-10)") as HTMLTextAreaElement).value).toBe("");
    expect(screen.queryByRole("button", { name: /prihvati sve/i })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Dodaj u dijagnoze" }));
    expect(onDecideDiagnosis).toHaveBeenCalledWith(diagnosis, "accept");
    await user.click(screen.getByRole("button", { name: "Odbaci" }));
    expect(onDecideDiagnosis).toHaveBeenCalledWith(diagnosis, "reject");
  });

  test("jasno prikazuje da su AI prijedlozi dijagnoza isključeni", () => {
    render(<EncounterPanel draft={{}} setDraft={vi.fn()} status="in_progress" aiDiagnosisCapability={{ enabled: false, reason: "Kanonski WHO ICD-10 katalog nije dostupan." }} onOpen={vi.fn()} onSave={vi.fn()} onComplete={vi.fn()} onSuggestDiagnoses={vi.fn()}/>);
    expect(screen.queryByRole("button", { name: "AI predloži" })).toBeNull();
    expect(screen.getByText("Kanonski WHO ICD-10 katalog nije dostupan.")).toBeTruthy();
  });

  test("sprema izmijenjenu stavku prijemne provjere", async () => {
    const user = userEvent.setup();
    const onUpdate = vi.fn().mockResolvedValue(undefined);
    render(<CheckInChecklist data={{ items: [{ id: 7, label: "Identitet potvrđen", state: "not_confirmed", note: null, requires_clinician: false }] }} onUpdate={onUpdate}/>);

    await user.selectOptions(screen.getByLabelText("Identitet potvrđen — stanje"), "confirmed");
    await user.type(screen.getByLabelText("Identitet potvrđen — napomena"), "Provjeren dokument");
    await user.click(screen.getByRole("button", { name: "Spremi" }));

    expect(onUpdate).toHaveBeenCalledWith(7, "confirmed", "Provjeren dokument");
  });

  test("administrativne podatke potvrđuje jednom radnjom", async () => {
    const user = userEvent.setup();
    const onConfirmAdministrative = vi.fn().mockResolvedValue(undefined);
    render(<CheckInChecklist data={{ items: [{ id: 1, label: "Identitet potvrđen", state: "not_confirmed", note: null, requires_clinician: false }, { id: 2, label: "Antikoagulansi", state: "not_confirmed", note: null, requires_clinician: true }] }} onUpdate={vi.fn()} onConfirmAdministrative={onConfirmAdministrative}/>);

    await user.click(screen.getByRole("button", { name: "Potvrdi administrativne podatke" }));
    expect(onConfirmAdministrative).toHaveBeenCalledOnce();
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
