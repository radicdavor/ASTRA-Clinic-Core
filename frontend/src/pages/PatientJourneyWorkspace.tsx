import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, getSessionUser } from "../api/client";
import { useApi } from "../hooks/useApi";
import type { ClinicalDocument, InventoryItem, Provider, Service } from "../types";
import type { AIDiagnosisSuggestion, CheckInState, EncounterDraft, JourneyClosure, JourneyStageKey, PatientJourneyDetail, PatientJourneySummary, PatientJourneyTimelineItem, PreparationState, PublicPilotConfig, VisitDocument } from "../types/program2";
import { AISummaryPanel, BillingPanel, BlockerPanel, CheckInChecklist, ConsumablesPanel, DocumentReadinessPanel, EncounterPanel, PatientTimeline, PaymentPanel, PreparationPanel, SourceDocumentViewer } from "../components/program2/Program2Panels";
import { journeyStatusLabel } from "../components/program2/journeyStatus";
import { focusToStage, JourneyHeader, JourneyNextAction, JourneyStageStepper, stageForJourney } from "../components/program2/journey/JourneyChrome";
import { JourneyClinicalContext } from "../components/program2/journey/JourneyClinicalContext";
import { ClinicalActivityForm } from "../components/program2/ClinicalActivityForm";
import { VisitDocumentCenter } from "../components/program2/VisitDocumentCenter";

function formatDate(value?: string | null) {
  if (!value) return "nije upisano";
  const date = new Date(`${value.slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("hr-HR");
}

export function PatientJourneyWorkspace() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const journey = useApi<PatientJourneyDetail | null>(`/api/patient-journeys/${id}`, null);
  const timeline = useApi<PatientJourneyTimelineItem[]>(`/api/patient-journeys/${id}/timeline`, []);
  const summary = useApi<PatientJourneySummary | null>(`/api/patient-journeys/${id}/summary`, null);
  const checkin = useApi<CheckInState | null>(`/api/patient-journeys/${id}/check-in`, null);
  const preparation = useApi<PreparationState | null>(`/api/patient-journeys/${id}/preparation`, null);
  const encounter = useApi<EncounterDraft | null>(`/api/patient-journeys/${id}/encounter`, null);
  const closure = useApi<JourneyClosure | null>(`/api/patient-journeys/${id}/closure`, null);
  const inventory = useApi<InventoryItem[]>("/api/inventory/items", []);
  const services = useApi<Service[]>("/api/services", []);
  const providers = useApi<Provider[]>("/api/providers", []);
  const publicConfig = useApi<PublicPilotConfig>("/api/public-config", {});
  const documents = useApi<ClinicalDocument[]>(`/api/clinical-documents?patient_id=${journey.data?.patient_id ?? 0}`, []);
  const visitDocuments = useApi<VisitDocument[]>(`/api/patient-journeys/${id}/visit-documents`, []);
  const [draft, setDraft] = useState<EncounterDraft>({});
  const [activeStage, setActiveStage] = useState<JourneyStageKey>("documents");
  const [aiDiagnoses, setAiDiagnoses] = useState<AIDiagnosisSuggestion[]>([]);
  const [diagnosisBusy, setDiagnosisBusy] = useState(false);
  const [actionError, setActionError] = useState("");

  useEffect(() => { if (encounter.data) setDraft(encounter.data); }, [encounter.data]);
  useEffect(() => {
    if (!journey.data) return;
    const current = stageForJourney(journey.data.current_stage);
    const role = (getSessionUser()?.role ?? "").replace(/^demo_/, "");
    const roleDefault = role === "billing" && ["awaiting_billing", "awaiting_payment"].includes(journey.data.current_stage) ? "billing" : current;
    setActiveStage(focusToStage(searchParams.get("focus"), roleDefault));
  }, [journey.data?.id, journey.data?.current_stage, searchParams]);

  if (!journey.data) return <section className="page"><p>Učitavanje tijeka pacijenta...</p></section>;
  const j = journey.data;
  const currentStage = stageForJourney(j.current_stage);
  const serviceName = j.appointment.service?.name ?? services.data.find(item => item.id === j.appointment.service_id)?.name;
  const clinicianName = j.appointment.provider?.full_name ?? providers.data.find(item => item.id === j.appointment.provider_id)?.full_name;
  const activities = j.activities ?? [];
  const requestedActivityId = Number(searchParams.get("activity"));
  const selectedActivity = activities.find(item => item.id === requestedActivityId) ?? activities.find(item => item.status === "in_progress") ?? activities[0];
  const openBlockers = j.blockers.filter(item => item.status === "open");
  const criticalFacts = openBlockers.slice(0, 2).map(item => `Problem: ${item.title}`);
  if (["partial", "review_required", "blocked"].includes(j.document_status)) criticalFacts.push(`Dokumenti: ${journeyStatusLabel(j.document_status)}`);
  if (["review_required", "blocked"].includes(j.preparation_status)) criticalFacts.push(`Priprema: ${journeyStatusLabel(j.preparation_status)}`);

  async function perform(action: () => Promise<void>) {
    setActionError("");
    try { await action(); }
    catch (error) { setActionError(error instanceof Error ? error.message : "Radnja nije spremljena."); }
  }
  async function refresh() {
    journey.setData(await api<PatientJourneyDetail>(`/api/patient-journeys/${id}`));
    closure.setData(await api<JourneyClosure>(`/api/patient-journeys/${id}/closure`));
    visitDocuments.setData(await api<VisitDocument[]>(`/api/patient-journeys/${id}/visit-documents`));
  }
  function selectActivity(activityId: number) {
    const next = new URLSearchParams(searchParams);
    next.set("focus", "encounter"); next.set("activity", String(activityId));
    setSearchParams(next);
    setActiveStage("encounter");
  }
  async function startCheckIn() { await perform(async () => { checkin.setData(await api<CheckInState>(`/api/patient-journeys/${id}/check-in`, { method: "POST" })); await refresh(); }); }
  async function open() { await perform(async () => { encounter.setData(await api(`/api/patient-journeys/${id}/encounter`, { method: "POST" })); await refresh(); }); }
  async function save() { await perform(async () => { encounter.setData(await api(`/api/patient-journeys/${id}/encounter`, { method: "PATCH", body: JSON.stringify(draft) })); }); }
  async function suggestDiagnoses() {
    setDiagnosisBusy(true);
    await perform(async () => {
      const result = await api<{ diagnoses: Array<{ code: string; title: string }>; provider: "openai"; model: string; request_id: string }>(`/api/patient-journeys/${id}/encounter/diagnosis-suggestions`, { method: "POST", body: JSON.stringify({ anamnesis: draft.anamnesis, examination: draft.examination, patient_findings: draft.patient_findings, opinion: draft.opinion }) });
      setAiDiagnoses(result.diagnoses.map(item => ({ ...item, provider: result.provider, model: result.model, request_id: result.request_id })));
    });
    setDiagnosisBusy(false);
  }
  async function decideDiagnosis(item: AIDiagnosisSuggestion, action: "accept" | "reject") {
    await perform(async () => {
      const updated = await api<EncounterDraft>(`/api/patient-journeys/${id}/encounter/diagnosis-suggestions/decision`, { method: "POST", body: JSON.stringify({ action, code: item.code, title: item.title, provider: item.provider, model: item.model, request_id: item.request_id }) });
      setDraft(updated);
      encounter.setData(updated);
      setAiDiagnoses(current => current.filter(value => value.code !== item.code || value.title !== item.title));
    });
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

  return <section className="page journey-workspace journey-workspace-focused">
    <JourneyHeader journey={j} service={serviceName} clinician={clinicianName} formatDate={formatDate}/>
    {actionError && <p className="inline-error" role="alert">{actionError}</p>}
    {criticalFacts.length > 0 && <aside className="journey-critical-facts" aria-label="Važno sada">{criticalFacts.map(item => <span key={item}>{item}</span>)}</aside>}
    <JourneyNextAction journey={j} stage={currentStage} onSelect={setActiveStage}/>
    {activities.length > 0 && <nav className="journey-activity-selector" aria-label="Aktivnosti dolaska"><span>{activities.length} {activities.length === 1 ? "aktivnost" : "aktivnosti"}</span>{activities.map(activity => { const activityService = services.data.find(item => item.id === activity.service_id)?.name ?? activity.activity_key; return <button type="button" key={activity.id} className={selectedActivity?.id === activity.id ? "active" : ""} onClick={() => selectActivity(activity.id)}><i className={`activity-dot ${activity.status}`} aria-hidden="true"/><span><b>{activity.sequence}. {activityService}</b><small>{new Date(activity.planned_start).toLocaleTimeString("hr-HR", { hour: "2-digit", minute: "2-digit" })} · {activity.status === "in_progress" ? "u tijeku" : activity.status === "completed" ? "završeno" : "čeka"}</small></span></button>; })}</nav>}
    <JourneyStageStepper active={activeStage} current={currentStage} onSelect={setActiveStage}/>
    <main className="journey-active-stage" id={`journey-${activeStage}`} tabIndex={-1} aria-live="polite">
      {activeStage === "documents" && <><BlockerPanel items={j.blockers} onResolve={resolveBlocker}/><div className="journey-stage-pair"><DocumentReadinessPanel status={j.document_status}/><PreparationPanel status={j.preparation_status} data={preparation.data ?? undefined} onUpdate={updatePreparation}/></div><VisitDocumentCenter journeyId={j.id} items={visitDocuments.data} onChanged={refresh}/></>}
      {activeStage === "arrival" && <><BlockerPanel items={j.blockers} onResolve={resolveBlocker}/>{!checkin.data && <section className="journey-panel journey-start-panel"><h2>Dolazak i prijem</h2><p>Prijem još nije započet. Ova radnja evidentira dolazak i otvara prijemnu provjeru.</p><button type="button" className="primary" onClick={startCheckIn}>Započni prijem</button></section>}<CheckInChecklist data={checkin.data} onUpdate={updateCheckIn} onConfirmAdministrative={confirmAdministrativeCheckIn}/></>}
      {activeStage === "encounter" && <><BlockerPanel items={j.blockers} onResolve={resolveBlocker}/>{selectedActivity ? <ClinicalActivityForm journeyId={j.id} activity={selectedActivity} serviceName={services.data.find(item => item.id === selectedActivity.service_id)?.name ?? selectedActivity.activity_key} onChanged={refresh}/> : <EncounterPanel draft={draft} setDraft={setDraft} status={encounter.data?.status} aiDiagnoses={aiDiagnoses} aiDiagnosisCapability={publicConfig.data.ai_diagnosis_suggestions} diagnosisBusy={diagnosisBusy} onOpen={open} onSave={save} onComplete={complete} onSuggestDiagnoses={suggestDiagnoses} onDecideDiagnosis={decideDiagnosis}/>}</>}
      {activeStage === "consumables" && <ConsumablesPanel status={j.consumables_status} canConfirm={j.current_stage === "procedure_completed"} items={inventory.data} onConfirm={confirmConsumables}/>}
      {activeStage === "billing" && <div className="journey-stage-pair"><BillingPanel status={j.billing_status} invoice={closure.data?.invoice ?? undefined} onPrepare={prepareBilling}/><PaymentPanel status={j.payment_status} invoice={closure.data?.invoice ?? undefined} stage={j.current_stage} onPay={pay} onDefer={defer} onClose={close}/></div>}
      {activeStage === "completed" && <section className="journey-panel journey-completed"><h2>Dolazak je završen</h2><p>Pregled, materijal i naplata nemaju otvorenu operativnu radnju.</p><Link to={`/patients/${j.patient_id}`}>Otvori longitudinalni zapis pacijenta</Link></section>}
    </main>
    <JourneyClinicalContext summary={<AISummaryPanel summary={summary.data} onGenerate={generateSummary} onReview={reviewSummaryFact}/>} timeline={<PatientTimeline items={timeline.data}/>} documents={<SourceDocumentViewer documents={documents.data} onReview={reviewDocument}/>}/>
  </section>;
}
