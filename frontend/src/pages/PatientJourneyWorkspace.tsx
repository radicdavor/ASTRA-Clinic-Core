import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import type { InventoryItem } from "../types";
import { AISummaryPanel, BillingPanel, BlockerPanel, CheckInChecklist, ConsumablesPanel, DocumentReadinessPanel, EncounterPanel, PatientTimeline, PaymentPanel, PreparationPanel, SourceDocumentViewer } from "../components/program2/Program2Panels";
import { journeyStageLabel, journeyStatusLabel } from "../components/program2/journeyStatus";

function formatDate(value?: string | null) {
  if (!value) return "nije upisano";
  const date = new Date(`${value.slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("hr-HR");
}

export function PatientJourneyWorkspace() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const journey = useApi<any>(`/api/patient-journeys/${id}`, null);
  const timeline = useApi<any[]>(`/api/patient-journeys/${id}/timeline`, []);
  const summary = useApi<any>(`/api/patient-journeys/${id}/summary`, null);
  const checkin = useApi<any>(`/api/patient-journeys/${id}/check-in`, null);
  const preparation = useApi<any>(`/api/patient-journeys/${id}/preparation`, null);
  const encounter = useApi<any>(`/api/patient-journeys/${id}/encounter`, null);
  const closure = useApi<any>(`/api/patient-journeys/${id}/closure`, null);
  const inventory = useApi<InventoryItem[]>("/api/inventory/items", []);
  const documents = useApi<any[]>(`/api/clinical-documents?patient_id=${journey.data?.patient_id ?? 0}`, []);
  const [draft, setDraft] = useState<any>({});
  const [aiDiagnoses, setAiDiagnoses] = useState<Array<{ code: string; title: string }>>([]);
  const [diagnosisBusy, setDiagnosisBusy] = useState(false);
  const [actionError, setActionError] = useState("");

  useEffect(() => { if (encounter.data) setDraft(encounter.data); }, [encounter.data]);
  useEffect(() => {
    const focus = searchParams.get("focus");
    if (journey.data && focus) requestAnimationFrame(() => document.getElementById(`journey-${focus}`)?.scrollIntoView({ behavior: "smooth", block: "start" }));
  }, [journey.data, searchParams]);

  if (!journey.data) return <section className="page"><p>Učitavanje tijeka pacijenta...</p></section>;
  const j = journey.data;

  async function perform(action: () => Promise<void>) {
    setActionError("");
    try { await action(); }
    catch (error) { setActionError(error instanceof Error ? error.message : "Radnja nije spremljena."); }
  }
  async function refresh() {
    journey.setData(await api(`/api/patient-journeys/${id}`));
    closure.setData(await api(`/api/patient-journeys/${id}/closure`));
  }
  async function open() { await perform(async () => { encounter.setData(await api(`/api/patient-journeys/${id}/encounter`, { method: "POST" })); await refresh(); }); }
  async function save() { await perform(async () => { encounter.setData(await api(`/api/patient-journeys/${id}/encounter`, { method: "PATCH", body: JSON.stringify(draft) })); }); }
  async function suggestDiagnoses() {
    setDiagnosisBusy(true);
    await perform(async () => {
      const result = await api<{ diagnoses: Array<{ code: string; title: string }> }>(`/api/patient-journeys/${id}/encounter/diagnosis-suggestions`, { method: "POST", body: JSON.stringify({ anamnesis: draft.anamnesis, examination: draft.examination, patient_findings: draft.patient_findings, opinion: draft.opinion }) });
      const previousSuggestions = new Set(aiDiagnoses.map(item => `${item.code} — ${item.title}`));
      const existing = String(draft.diagnosis ?? "").split("\n").map(line => line.trim()).filter(line => line && !previousSuggestions.has(line));
      const suggested = result.diagnoses.map(item => `${item.code} — ${item.title}`);
      setDraft({ ...draft, diagnosis: [...new Set([...existing, ...suggested])].join("\n") });
      setAiDiagnoses(result.diagnoses);
    });
    setDiagnosisBusy(false);
  }
  function removeDiagnosis(item: { code: string; title: string }) {
    const line = `${item.code} — ${item.title}`;
    setDraft({ ...draft, diagnosis: String(draft.diagnosis ?? "").split("\n").filter(value => value.trim() !== line).join("\n") });
    setAiDiagnoses(current => current.filter(value => value.code !== item.code || value.title !== item.title));
  }
  async function complete() {
    if (!window.confirm("Dovršiti klinički susret? Nakon toga bilješka više nije dostupna za redovno uređivanje.")) return;
    await perform(async () => { encounter.setData(await api(`/api/patient-journeys/${id}/encounter/complete`, { method: "POST" })); await refresh(); });
  }
  async function updateCheckIn(itemId: number, state: string, note: string) {
    await perform(async () => { checkin.setData(await api(`/api/patient-journeys/${id}/check-in/items/${itemId}`, { method: "PATCH", body: JSON.stringify({ state, note: note || null }) })); await refresh(); });
  }
  async function confirmAdministrativeCheckIn() {
    await perform(async () => { checkin.setData(await api(`/api/patient-journeys/${id}/check-in/confirm-administrative`, { method: "POST" })); await refresh(); });
  }
  async function updatePreparation(requirementKey: string, state: string) {
    await perform(async () => { preparation.setData(await api(`/api/patient-journeys/${id}/preparation/requirements`, { method: "PATCH", body: JSON.stringify({ requirement_key: requirementKey, state }) })); await refresh(); });
  }
  async function generateSummary() {
    await perform(async () => { summary.setData(await api(`/api/patient-journeys/${id}/summary`, { method: "POST" })); timeline.setData(await api(`/api/patient-journeys/${id}/timeline`)); });
  }
  async function reviewSummaryFact(summaryId: number, factId: number, action: "accept" | "reject") {
    await perform(async () => { summary.setData(await api(`/api/patient-journeys/${id}/summary/${summaryId}/facts/${factId}`, { method: "PATCH", body: JSON.stringify({ action }) })); });
  }
  async function reviewDocument(documentId: number) {
    await perform(async () => { await api(`/api/clinical-documents/${documentId}/review`, { method: "POST" }); documents.setData(await api(`/api/clinical-documents?patient_id=${j.patient_id}`)); await refresh(); });
  }
  async function resolveBlocker(blockerId: number, resolutionNote: string) {
    await perform(async () => { await api(`/api/patient-journeys/${id}/blockers/${blockerId}/resolve`, { method: "POST", body: JSON.stringify({ resolution_note: resolutionNote }) }); await refresh(); });
  }
  async function confirmConsumables(lines: Array<{ inventory_item_id: number; quantity: string; reason?: string }>, notApplicable: boolean) {
    const message = notApplicable ? "Potvrditi da materijal nije korišten?" : "Potvrditi navedeni materijal i skinuti ga sa zalihe?";
    if (!window.confirm(message)) return;
    await perform(async () => { await api(`/api/patient-journeys/${id}/consumables/confirm`, { method: "POST", body: JSON.stringify({ lines, not_applicable: notApplicable }) }); await refresh(); });
  }
  async function prepareBilling() {
    if (!window.confirm("Izraditi i izdati račun za ovaj dolazak?")) return;
    await perform(async () => { await api(`/api/patient-journeys/${id}/billing/prepare`, { method: "POST" }); await refresh(); });
  }
  async function pay(amount: string, method: string) {
    if (!window.confirm(`Evidentirati uplatu od ${amount} EUR?`)) return;
    await perform(async () => { await api(`/api/patient-journeys/${id}/payments`, { method: "POST", body: JSON.stringify({ amount, method }) }); await refresh(); });
  }
  async function defer() {
    const reason = window.prompt("Upišite razlog odgode plaćanja");
    if (reason?.trim()) await perform(async () => { await api(`/api/patient-journeys/${id}/payments/defer`, { method: "POST", body: JSON.stringify({ reason: reason.trim() }) }); await refresh(); });
  }
  async function close() {
    if (!window.confirm("Završiti tijek pacijenta?")) return;
    await perform(async () => { await api(`/api/patient-journeys/${id}/close`, { method: "POST" }); await refresh(); });
  }

  return <section className="page journey-workspace">
    <header className="journey-workspace-header"><div><span>TIJEK PACIJENTA · #{j.id}</span><h1>{j.patient.first_name} {j.patient.last_name}</h1><p>Rođen/a: {formatDate(j.patient.date_of_birth)} · termin {formatDate(j.appointment.date)} u {j.appointment.start_time.slice(0, 5)}</p></div><div><strong>{journeyStageLabel(j.current_stage)}</strong><Link to={`/appointments/${j.appointment_id}`}>Termin #{j.appointment_id}</Link></div></header>
    {actionError && <p className="inline-error" role="alert">{actionError}</p>}
    <div className="journey-safety-strip"><span>Dokumenti: {journeyStatusLabel(j.document_status)}</span><span>Priprema: {journeyStatusLabel(j.preparation_status)}</span><span>Prijem: {journeyStatusLabel(j.check_in_status)}</span><span>Pregled: {journeyStatusLabel(j.encounter_status)}</span></div>
    <div className="journey-columns">
      <aside><PatientTimeline items={timeline.data}/><SourceDocumentViewer documents={documents.data} onReview={reviewDocument}/><AISummaryPanel summary={summary.data} onGenerate={generateSummary} onReview={reviewSummaryFact}/></aside>
      <main id="journey-encounter" tabIndex={-1}><EncounterPanel draft={draft} setDraft={setDraft} status={encounter.data?.status} aiDiagnoses={aiDiagnoses} diagnosisBusy={diagnosisBusy} onOpen={open} onSave={save} onComplete={complete} onSuggestDiagnoses={suggestDiagnoses} onRemoveDiagnosis={removeDiagnosis}/></main>
      <aside><div id="journey-attention" tabIndex={-1}><BlockerPanel items={j.blockers} onResolve={resolveBlocker}/></div><div id="journey-check-in" tabIndex={-1}><CheckInChecklist data={checkin.data} onUpdate={updateCheckIn} onConfirmAdministrative={confirmAdministrativeCheckIn}/></div><DocumentReadinessPanel status={j.document_status}/><PreparationPanel status={j.preparation_status} data={preparation.data} onUpdate={updatePreparation}/><div id="journey-consumables" tabIndex={-1}><ConsumablesPanel status={j.consumables_status} canConfirm={j.current_stage === "procedure_completed"} items={inventory.data} onConfirm={confirmConsumables}/></div><div id="journey-billing" tabIndex={-1}><BillingPanel status={j.billing_status} invoice={closure.data?.invoice} onPrepare={prepareBilling}/></div><div id="journey-payment" tabIndex={-1}><PaymentPanel status={j.payment_status} invoice={closure.data?.invoice} stage={j.current_stage} onPay={pay} onDefer={defer} onClose={close}/></div></aside>
    </div>
  </section>;
}
