import { useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, getSessionUser } from "../api/client";
import { DateInput } from "../components/DateInput";
import { useApi } from "../hooks/useApi";
import type { ClinicalDocument, InventoryItem, Provider, Service } from "../types";
import type { ActivityPreparationState, AIDiagnosisSuggestion, CheckInState, EncounterDraft, JourneyClosure, JourneyStageKey, PathologyCase, PatientJourneyDetail, PatientJourneySummary, PatientJourneyTimelineItem, PreparationState, PublicPilotConfig, VisitDocument } from "../types/program2";
import { AISummaryPanel, BillingPanel, BlockerPanel, CheckInChecklist, ConsumablesPanel, DocumentReadinessPanel, EncounterPanel, PatientTimeline, PaymentPanel, PreparationPanel, ReceptionMedicalHandoff, SourceDocumentViewer } from "../components/program2/Program2Panels";
import { activityClockTime, journeyStatusLabel } from "../components/program2/journeyStatus";
import { focusToStage, JourneyHeader, JourneyNextAction, JourneyStageStepper, stageForJourney } from "../components/program2/journey/JourneyChrome";
import { JourneyClinicalContext, type JourneyContextTab } from "../components/program2/journey/JourneyClinicalContext";
import { ClinicalActivityForm, type ClinicalActivityFormHandle } from "../components/program2/ClinicalActivityForm";
import { VisitDocumentCenter } from "../components/program2/VisitDocumentCenter";
import { PathologyFollowUpPanel } from "../components/program2/PathologyFollowUpPanel";
import { ActivityInterventionsPanel } from "../components/program2/ActivityInterventionsPanel";

function formatDate(value?: string | null) {
  if (!value) return "nije upisano";
  const date = new Date(`${value.slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("hr-HR");
}

type WorkspaceConfirmation = {
  title: string;
  text: string;
  confirmLabel: string;
  reasonLabel?: string;
  reason?: string;
  action: (reason?: string) => Promise<void>;
};

type PendingFormNavigation = { kind: "activity"; activityId: number } | { kind: "stage"; stage: JourneyStageKey };

type ReceptionModal = "identity" | "checklist" | null;
type PatientReceptionDraft = { first_name: string; last_name: string; date_of_birth: string; oib: string; phone: string; email: string; notes: string };
type ReceptionChecklistDraft = {
  consent_status: boolean; laboratory_results: boolean; anesthesia_questionnaire: boolean; informed_consent: boolean;
  fasting_6h: boolean; bowel_preparation_clear: boolean; sedation_escort: boolean; pacemaker: boolean;
  current_medication_text: string; drug_allergy_text: string;
};

const receptionDefaults: ReceptionChecklistDraft = {
  consent_status: true,
  laboratory_results: true,
  anesthesia_questionnaire: true,
  informed_consent: true,
  fasting_6h: true,
  bowel_preparation_clear: true,
  sedation_escort: true,
  pacemaker: false,
  current_medication_text: "",
  drug_allergy_text: "",
};

const receptionChecklist: Array<{ key: keyof Omit<ReceptionChecklistDraft, "current_medication_text" | "drug_allergy_text">; label: string; defaultChecked: boolean; warning: string }> = [
  { key: "consent_status", label: "Status privole potvrđen", defaultChecked: true, warning: "Status privole nije potvrđen." },
  { key: "laboratory_results", label: "Potrebni laboratorijski nalazi", defaultChecked: true, warning: "Potrebni laboratorijski nalazi nisu potvrđeni." },
  { key: "anesthesia_questionnaire", label: "Anesteziološki upitnik", defaultChecked: true, warning: "Anesteziološki upitnik nije potvrđen." },
  { key: "informed_consent", label: "Informirani pristanak", defaultChecked: true, warning: "Informirani pristanak nije potvrđen." },
  { key: "fasting_6h", label: "Post (6 sati)", defaultChecked: true, warning: "Post od 6 sati nije potvrđen." },
  { key: "bowel_preparation_clear", label: "Priprema crijeva (stolica bistra)", defaultChecked: true, warning: "Priprema crijeva nije potvrđena kao uredna." },
  { key: "sedation_escort", label: "Pratnja nakon sedacije", defaultChecked: true, warning: "Pratnja nakon sedacije nije potvrđena." },
  { key: "pacemaker", label: "Elektrostimulator", defaultChecked: false, warning: "Pacijent navodi elektrostimulator." },
];

export function PatientJourneyWorkspace() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeStage, setActiveStage] = useState<JourneyStageKey>(() => focusToStage(searchParams.get("focus"), "documents"));
  const [clinicalContextOpen, setClinicalContextOpen] = useState(false);
  const [clinicalContextTab, setClinicalContextTab] = useState<JourneyContextTab>("summary");
  const [loadedClinicalContextTabs, setLoadedClinicalContextTabs] = useState<Set<JourneyContextTab>>(() => new Set());
  const journey = useApi<PatientJourneyDetail | null>(`/api/patient-journeys/${id}`, null);
  const timeline = useApi<PatientJourneyTimelineItem[]>(loadedClinicalContextTabs.has("timeline") ? `/api/patient-journeys/${id}/timeline` : null, []);
  const summary = useApi<PatientJourneySummary | null>(loadedClinicalContextTabs.has("summary") ? `/api/patient-journeys/${id}/summary` : null, null);
  const checkin = useApi<CheckInState | null>(["arrival", "encounter"].includes(activeStage) ? `/api/patient-journeys/${id}/check-in` : null, null);
  const preparation = useApi<PreparationState | null>(activeStage === "documents" ? `/api/patient-journeys/${id}/preparation` : null, null);
  const activityPreparation = useApi<ActivityPreparationState | null>(activeStage === "documents" ? `/api/patient-journeys/${id}/activity-preparation` : null, null);
  const encounter = useApi<EncounterDraft | null>(activeStage === "encounter" ? `/api/patient-journeys/${id}/encounter` : null, null);
  const closure = useApi<JourneyClosure | null>(activeStage === "billing" ? `/api/patient-journeys/${id}/closure` : null, null);
  const inventory = useApi<InventoryItem[]>(activeStage === "consumables" ? "/api/inventory/items" : null, []);
  const services = useApi<Service[]>("/api/services", []);
  const providers = useApi<Provider[]>(journey.data && !journey.data.appointment.provider ? "/api/providers" : null, []);
  const publicConfig = useApi<PublicPilotConfig>(activeStage === "encounter" ? "/api/public-config" : null, {});
  const documents = useApi<ClinicalDocument[]>(loadedClinicalContextTabs.has("documents") && journey.data?.patient_id ? `/api/clinical-documents?patient_id=${journey.data.patient_id}` : null, []);
  const visitDocuments = useApi<VisitDocument[]>(activeStage === "documents" ? `/api/patient-journeys/${id}/visit-documents` : null, []);
  const pathologyCases = useApi<PathologyCase[]>(activeStage === "documents" ? `/api/patient-journeys/${id}/pathology-cases` : null, []);
  const [draft, setDraft] = useState<EncounterDraft>({});
  const [aiDiagnoses, setAiDiagnoses] = useState<AIDiagnosisSuggestion[]>([]);
  const [diagnosisBusy, setDiagnosisBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [confirmation, setConfirmation] = useState<WorkspaceConfirmation | null>(null);
  const [pendingFormNavigation, setPendingFormNavigation] = useState<PendingFormNavigation | null>(null);
  const [receptionModal, setReceptionModal] = useState<ReceptionModal>(null);
  const [receptionBusy, setReceptionBusy] = useState(false);
  const [patientReceptionDraft, setPatientReceptionDraft] = useState<PatientReceptionDraft>({ first_name: "", last_name: "", date_of_birth: "", oib: "", phone: "", email: "", notes: "" });
  const [receptionDraft, setReceptionDraft] = useState<ReceptionChecklistDraft>(receptionDefaults);
  const [receptionCompletionKey, setReceptionCompletionKey] = useState("");
  const clinicalFormRef = useRef<ClinicalActivityFormHandle | null>(null);
  const autoReceptionOpenedRef = useRef<string | null>(null);

  useEffect(() => { if (encounter.data) setDraft(encounter.data); }, [encounter.data]);
  useEffect(() => {
    if (!journey.data?.patient) return;
    setPatientReceptionDraft({
      first_name: journey.data.patient.first_name ?? "",
      last_name: journey.data.patient.last_name ?? "",
      date_of_birth: journey.data.patient.date_of_birth ?? "",
      oib: journey.data.patient.oib ?? "",
      phone: journey.data.patient.phone ?? "",
      email: journey.data.patient.email ?? "",
      notes: "",
    });
  }, [journey.data?.patient]);
  useEffect(() => {
    if (!journey.data) return;
    const current = stageForJourney(journey.data.current_stage);
    const role = (getSessionUser()?.role ?? "").replace(/^demo_/, "");
    const roleDefault = role === "billing" && ["awaiting_billing", "awaiting_payment"].includes(journey.data.current_stage) ? "billing" : current;
    if (!clinicalFormRef.current?.hasUnsavedChanges()) setActiveStage(focusToStage(searchParams.get("focus"), roleDefault));
  }, [journey.data?.id, journey.data?.current_stage, searchParams]);
  useEffect(() => {
    if (!journey.data || searchParams.get("reception") !== "1") return;
    const key = String(journey.data.id);
    if (autoReceptionOpenedRef.current === key) return;
    autoReceptionOpenedRef.current = key;
    setActiveStage("arrival");
    openReception();
  }, [journey.data?.id, searchParams]);

  if (!journey.data) return <section className="page"><p>Učitavanje tijeka pacijenta...</p></section>;
  const j = journey.data;
  const currentStage = stageForJourney(j.current_stage);
  const serviceName = j.appointment.service?.name ?? services.data.find(item => item.id === j.appointment.service_id)?.name;
  const clinicianName = j.appointment.provider?.full_name ?? providers.data.find(item => item.id === j.appointment.provider_id)?.full_name;
  const activities = j.activities ?? [];
  const role = (getSessionUser()?.role ?? "").replace(/^demo_/, "");
  const canRecordMedicalDisposition = ["admin", "physician", "nurse"].includes(role);
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
    if (activeStage === "billing") closure.setData(await api<JourneyClosure>(`/api/patient-journeys/${id}/closure`));
    if (activeStage === "documents") {
      visitDocuments.setData(await api<VisitDocument[]>(`/api/patient-journeys/${id}/visit-documents`));
      pathologyCases.setData(await api<PathologyCase[]>(`/api/patient-journeys/${id}/pathology-cases`));
    }
  }
  function applyFormNavigation(target: PendingFormNavigation) {
    if (target.kind === "stage") { setActiveStage(target.stage); return; }
    const next = new URLSearchParams(searchParams);
    next.set("focus", "encounter"); next.set("activity", String(target.activityId));
    setSearchParams(next);
    setActiveStage("encounter");
  }
  function requestFormNavigation(target: PendingFormNavigation) {
    if (target.kind === "activity" && selectedActivity?.id === target.activityId) return;
    if (target.kind === "stage" && activeStage === target.stage) return;
    if (clinicalFormRef.current?.hasUnsavedChanges()) { setPendingFormNavigation(target); return; }
    applyFormNavigation(target);
  }
  function loadClinicalContextTab(tab: JourneyContextTab) {
    setLoadedClinicalContextTabs(current => current.has(tab) ? current : new Set([...current, tab]));
  }
  function handleClinicalContextOpen(open: boolean) {
    setClinicalContextOpen(open);
    if (open) loadClinicalContextTab(clinicalContextTab);
  }
  function handleClinicalContextTab(tab: JourneyContextTab) {
    setClinicalContextTab(tab);
    if (clinicalContextOpen) loadClinicalContextTab(tab);
  }
  function selectActivity(activityId: number) { requestFormNavigation({ kind: "activity", activityId }); }
  async function startCheckIn() { openReception(); }
  async function openReception() {
    setReceptionDraft(receptionDefaults);
    setReceptionCompletionKey(`workspace-reception-${id}-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    setReceptionModal("identity");
  }
  async function confirmPatientReceptionData() {
    setReceptionBusy(true);
    await perform(async () => {
      await api(`/api/patients/${j.patient_id}`, { method: "PATCH", body: JSON.stringify({
        first_name: patientReceptionDraft.first_name.trim(),
        last_name: patientReceptionDraft.last_name.trim(),
        date_of_birth: patientReceptionDraft.date_of_birth || null,
        oib: patientReceptionDraft.oib.trim() || null,
        phone: patientReceptionDraft.phone.trim() || null,
        email: patientReceptionDraft.email.trim() || null,
      }) });
      checkin.setData(await api<CheckInState>(`/api/patient-journeys/${id}/check-in`, { method: "POST" }));
      await refresh();
      setReceptionModal("checklist");
    });
    setReceptionBusy(false);
  }
  function receptionWarnings() {
    const warnings = receptionChecklist.filter(item => Boolean(receptionDraft[item.key]) !== item.defaultChecked).map(item => item.warning);
    if (receptionDraft.current_medication_text.trim()) warnings.push(`Lijekovi: ${receptionDraft.current_medication_text.trim()}`);
    if (receptionDraft.drug_allergy_text.trim()) warnings.push(`Alergije na lijekove: ${receptionDraft.drug_allergy_text.trim()}`);
    return warnings;
  }
  async function completeReception() {
    setReceptionBusy(true);
    await perform(async () => {
      const notes = new Map<string, string>();
      for (const item of receptionChecklist) if (Boolean(receptionDraft[item.key]) !== item.defaultChecked) notes.set(item.key, item.warning);
      if (receptionDraft.current_medication_text.trim()) notes.set("current_medication", `Lijekovi: ${receptionDraft.current_medication_text.trim()}`);
      if (receptionDraft.drug_allergy_text.trim()) notes.set("drug_allergies", `Alergije na lijekove: ${receptionDraft.drug_allergy_text.trim()}`);
      checkin.setData(await api<CheckInState>(`/api/patient-journeys/${id}/check-in/complete-reception`, { method: "POST", body: JSON.stringify({ idempotency_key: receptionCompletionKey, reception_note: patientReceptionDraft.notes.trim() || null, items: Array.from(notes.entries()).map(([item_key, note]) => ({ item_key, note })) }) }));
      await refresh();
      setActiveStage("encounter");
      setReceptionModal(null);
    });
    setReceptionBusy(false);
  }
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
    setConfirmation({
      title: "Dovrši klinički susret",
      text: "Nakon dovršetka bilješka više nije dostupna za redovno uređivanje.",
      confirmLabel: "Dovrši susret",
      action: async () => { await perform(async () => { encounter.setData(await api(`/api/patient-journeys/${id}/encounter/complete`, { method: "POST" })); await refresh(); }); },
    });
  }
  async function updateCheckIn(itemId: number, state: string, note: string) {
    await perform(async () => { checkin.setData(await api(`/api/patient-journeys/${id}/check-in/items/${itemId}`, { method: "PATCH", body: JSON.stringify({ state, note: note || null }) })); await refresh(); });
  }
  async function confirmAdministrativeCheckIn() {
    await perform(async () => { checkin.setData(await api(`/api/patient-journeys/${id}/check-in/confirm-administrative`, { method: "POST" })); await refresh(); });
  }
  async function recordCheckInMedicalDisposition(itemId: number, disposition: string, note: string) {
    await perform(async () => {
      checkin.setData(await api<CheckInState>(`/api/patient-journeys/${id}/check-in/items/${itemId}/medical-disposition`, { method: "POST", body: JSON.stringify({ disposition, note }) }));
      await refresh();
    });
  }
  async function updatePreparation(requirementKey: string, state: string) {
    await perform(async () => { preparation.setData(await api(`/api/patient-journeys/${id}/preparation/requirements`, { method: "PATCH", body: JSON.stringify({ requirement_key: requirementKey, state }) })); await refresh(); });
  }
  async function updateActivityPreparation(requirementId: number, state: string) {
    await perform(async () => { activityPreparation.setData(await api(`/api/patient-journeys/${id}/activity-preparation/${requirementId}`, { method: "PATCH", body: JSON.stringify({ state }) })); await refresh(); });
  }
  async function generateSummary() {
    await perform(async () => { summary.setData(await api(`/api/patient-journeys/${id}/summary`, { method: "POST" })); });
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
    const endpoint = selectedActivity ? `/api/patient-journeys/${id}/activities/${selectedActivity.id}/consumables/confirm` : `/api/patient-journeys/${id}/consumables/confirm`;
    setConfirmation({
      title: notApplicable ? "Materijal nije korišten" : "Potvrdi potrošni materijal",
      text: notApplicable ? "Potvrdite da za ovu aktivnost nije korišten potrošni materijal." : "Navedene količine bit će evidentirane uz aktivnost i skinute sa zalihe.",
      confirmLabel: "Potvrdi",
      action: async () => { await perform(async () => { await api(endpoint, { method: "POST", body: JSON.stringify({ lines, not_applicable: notApplicable }) }); await refresh(); }); },
    });
  }
  async function prepareBilling() {
    setConfirmation({
      title: "Izradi račun",
      text: "Račun će obuhvatiti potvrđene aktivnosti i potrošni materijal ovog dolaska.",
      confirmLabel: "Izradi račun",
      action: async () => { await perform(async () => { await api(`/api/patient-journeys/${id}/billing/prepare`, { method: "POST" }); await refresh(); }); },
    });
  }
  async function pay(amount: string, method: string) {
    setConfirmation({
      title: "Evidentiraj uplatu",
      text: `Evidentirat će se uplata od ${amount} EUR.`,
      confirmLabel: "Evidentiraj uplatu",
      action: async () => { await perform(async () => { await api(`/api/patient-journeys/${id}/payments`, { method: "POST", body: JSON.stringify({ amount, method }) }); await refresh(); }); },
    });
  }
  async function defer() {
    setConfirmation({
      title: "Odgodi plaćanje",
      text: "Upišite razlog zbog kojeg plaćanje ostaje otvoreno.",
      confirmLabel: "Spremi odgodu",
      reasonLabel: "Razlog odgode",
      reason: "",
      action: async reason => { await perform(async () => { await api(`/api/patient-journeys/${id}/payments/defer`, { method: "POST", body: JSON.stringify({ reason: reason?.trim() }) }); await refresh(); }); },
    });
  }
  async function close() {
    setConfirmation({
      title: "Završi dolazak",
      text: "Dolazak se može završiti samo ako su pregled, materijal, račun i plaćanje administrativno razriješeni.",
      confirmLabel: "Završi dolazak",
      action: async () => { await perform(async () => { await api(`/api/patient-journeys/${id}/close`, { method: "POST" }); await refresh(); }); },
    });
  }

  return <section className="page journey-workspace journey-workspace-focused">
    <JourneyHeader journey={j} service={serviceName} clinician={clinicianName} formatDate={formatDate}/>
    {actionError && <p className="inline-error" role="alert">{actionError}</p>}
    {criticalFacts.length > 0 && <aside className="journey-critical-facts" aria-label="Važno sada">{criticalFacts.map(item => <span key={item}>{item}</span>)}</aside>}
    <JourneyNextAction journey={j} stage={currentStage} onSelect={stage => requestFormNavigation({ kind: "stage", stage })}/>
    {activities.length > 0 && <nav className="journey-activity-selector" aria-label="Aktivnosti dolaska"><span>{activities.length} {activities.length === 1 ? "aktivnost" : "aktivnosti"}</span>{activities.map(activity => { const activityService = services.data.find(item => item.id === activity.service_id)?.name ?? activity.activity_key; return <button type="button" key={activity.id} className={selectedActivity?.id === activity.id ? "active" : ""} onClick={() => selectActivity(activity.id)}><i className={`activity-dot ${activity.status}`} aria-hidden="true"/><span><b>{activity.sequence}. {activityService}</b><small>{activityClockTime(activity.planned_start)} · {activity.status === "in_progress" ? "u tijeku" : activity.status === "completed" ? "završeno" : "čeka"}</small></span></button>; })}</nav>}
    <JourneyStageStepper active={activeStage} current={currentStage} onSelect={stage => requestFormNavigation({ kind: "stage", stage })}/>
    <main className="journey-active-stage" id={`journey-${activeStage}`} tabIndex={-1} aria-live="polite">
      {activeStage === "documents" && <><BlockerPanel items={j.blockers} onResolve={resolveBlocker}/><div className="journey-stage-pair"><DocumentReadinessPanel status={j.document_status}/><PreparationPanel status={j.preparation_status} data={preparation.data ?? undefined} activityData={activityPreparation.data ?? undefined} onUpdate={updatePreparation} onActivityUpdate={updateActivityPreparation}/></div><PathologyFollowUpPanel items={pathologyCases.data} onChanged={refresh}/><VisitDocumentCenter journeyId={j.id} items={visitDocuments.data} patientEmail={j.patient.email} emailVerified={Boolean(j.patient.email_verified_at)} onChanged={refresh}/></>}
      {activeStage === "arrival" && <><BlockerPanel items={j.blockers} onResolve={resolveBlocker}/>{!checkin.data && <section className="journey-panel journey-start-panel"><h2>Dolazak i prijem</h2><p>Kada se pacijent javi tajnici ili sestri, otvorite prijem i provjerite samo podatke nužne prije pregleda.</p><button type="button" className="primary" onClick={startCheckIn}>Otvori prijem</button></section>}<CheckInChecklist data={checkin.data} onUpdate={updateCheckIn} onConfirmAdministrative={confirmAdministrativeCheckIn}/></>}
      {activeStage === "encounter" && <><BlockerPanel items={j.blockers} onResolve={resolveBlocker}/><ReceptionMedicalHandoff data={checkin.data} activities={activities} onMedicalDisposition={canRecordMedicalDisposition ? recordCheckInMedicalDisposition : undefined}/>{selectedActivity ? <><ClinicalActivityForm ref={clinicalFormRef} journeyId={j.id} activity={selectedActivity} serviceName={services.data.find(item => item.id === selectedActivity.service_id)?.name ?? selectedActivity.activity_key} onChanged={refresh}/><ActivityInterventionsPanel journeyId={j.id} activity={selectedActivity} onChanged={refresh}/></> : <EncounterPanel draft={draft} setDraft={setDraft} status={encounter.data?.status} aiDiagnoses={aiDiagnoses} aiDiagnosisCapability={publicConfig.data.ai_diagnosis_suggestions} diagnosisBusy={diagnosisBusy} onOpen={open} onSave={save} onComplete={complete} onSuggestDiagnoses={suggestDiagnoses} onDecideDiagnosis={decideDiagnosis}/>}</>}
      {activeStage === "consumables" && <ConsumablesPanel status={selectedActivity?.consumables_status ?? j.consumables_status} canConfirm={j.current_stage === "procedure_completed"} items={inventory.data} onConfirm={confirmConsumables}/>}
      {activeStage === "billing" && <div className="journey-stage-pair"><BillingPanel status={j.billing_status} invoice={closure.data?.invoice ?? undefined} onPrepare={prepareBilling}/><PaymentPanel status={j.payment_status} invoice={closure.data?.invoice ?? undefined} stage={j.current_stage} onPay={pay} onDefer={defer} onClose={close}/></div>}
      {activeStage === "completed" && <section className="journey-panel journey-completed"><h2>Dolazak je završen</h2><p>Pregled, materijal i naplata nemaju otvorenu operativnu radnju.</p><Link to={`/patients/${j.patient_id}`}>Otvori longitudinalni zapis pacijenta</Link></section>}
    </main>
    <JourneyClinicalContext
      summary={<AISummaryPanel summary={summary.data} onGenerate={generateSummary} onReview={reviewSummaryFact}/>}
      timeline={<PatientTimeline items={timeline.data}/>}
      documents={<SourceDocumentViewer documents={documents.data} onReview={reviewDocument}/>}
      onOpenChange={handleClinicalContextOpen}
      onTabChange={handleClinicalContextTab}
    />
    {pendingFormNavigation && <div className="modal-backdrop"><section className="modal-panel clinical-draft-navigation" role="dialog" aria-modal="true" aria-labelledby="draft-navigation-title"><header><div><span className="eyebrow">Nespremljena skica</span><h2 id="draft-navigation-title">Želite li spremiti promjene?</h2></div></header><p>Promjena aktivnosti ili faze ne smije odbaciti uneseni klinički tekst bez vaše odluke.</p><footer><button type="button" onClick={() => setPendingFormNavigation(null)}>Ostani</button><button type="button" onClick={() => { clinicalFormRef.current?.discardLocalChanges(); const target = pendingFormNavigation; setPendingFormNavigation(null); applyFormNavigation(target); }}>Odbaci i nastavi</button><button type="button" className="primary" onClick={async () => { const saved = await clinicalFormRef.current?.saveDraft(); if (saved) { const target = pendingFormNavigation; setPendingFormNavigation(null); applyFormNavigation(target); } }}>Spremi skicu i nastavi</button></footer></section></div>}
    {receptionModal === "identity" && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && setReceptionModal(null)}>
      <section className="modal-panel reception-modal" role="dialog" aria-modal="true" aria-labelledby="reception-identity-title">
        <header><div><span className="eyebrow">Prijem pacijenta</span><h2 id="reception-identity-title">Opći podaci pacijenta</h2></div></header>
        <p>Provjerite podatke s pacijentom ili na tabletu. Ako nešto ispravite, spremit će se prije prijemne provjere.</p>
        <div className="form-grid two">
          <label>Ime<input value={patientReceptionDraft.first_name} onChange={event => setPatientReceptionDraft(current => ({ ...current, first_name: event.target.value }))}/></label>
          <label>Prezime<input value={patientReceptionDraft.last_name} onChange={event => setPatientReceptionDraft(current => ({ ...current, last_name: event.target.value }))}/></label>
          <label>Datum rođenja<DateInput value={patientReceptionDraft.date_of_birth} onChange={value => setPatientReceptionDraft(current => ({ ...current, date_of_birth: value }))}/></label>
          <label>OIB<input value={patientReceptionDraft.oib} onChange={event => setPatientReceptionDraft(current => ({ ...current, oib: event.target.value }))} placeholder="Demo OIB ili prazno"/></label>
          <label>Telefon<input value={patientReceptionDraft.phone} onChange={event => setPatientReceptionDraft(current => ({ ...current, phone: event.target.value }))}/></label>
          <label>E-pošta<input value={patientReceptionDraft.email} onChange={event => setPatientReceptionDraft(current => ({ ...current, email: event.target.value }))}/></label>
          <label className="span-2">Napomena za današnji dolazak<input value={patientReceptionDraft.notes} onChange={event => setPatientReceptionDraft(current => ({ ...current, notes: event.target.value }))}/></label>
        </div>
        <footer><button type="button" onClick={() => setReceptionModal(null)}>Odustani</button><button type="button" className="primary" disabled={receptionBusy || !patientReceptionDraft.first_name.trim() || !patientReceptionDraft.last_name.trim()} onClick={confirmPatientReceptionData}>{receptionBusy ? "Spremam…" : "Podaci su točni"}</button></footer>
      </section>
    </div>}
    {receptionModal === "checklist" && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && setReceptionModal(null)}>
      <section className="modal-panel reception-modal" role="dialog" aria-modal="true" aria-labelledby="reception-checklist-title">
        <header><div><span className="eyebrow">Prije pregleda/pretrage</span><h2 id="reception-checklist-title">Kratka prijemna provjera</h2></div></header>
        <p>Ovo nije klinička odluka. Ako nešto odstupa, pacijent svejedno ide liječniku/anesteziologu, a red na ploči postaje crven.</p>
        <div className="reception-checklist">
          {receptionChecklist.map(item => <label key={item.key} className={Boolean(receptionDraft[item.key]) !== item.defaultChecked ? "changed" : ""}><input type="checkbox" checked={Boolean(receptionDraft[item.key])} onChange={event => setReceptionDraft(current => ({ ...current, [item.key]: event.target.checked }))}/><span>{item.label}</span></label>)}
        </div>
        <div className="form-grid two">
          <label>Lijekovi koje pacijent uzima<textarea rows={2} value={receptionDraft.current_medication_text} placeholder="Upisati samo kratak navod, detalji idu u anamnezu." onChange={event => setReceptionDraft(current => ({ ...current, current_medication_text: event.target.value }))}/></label>
          <label>Alergije na lijekove<textarea rows={2} value={receptionDraft.drug_allergy_text} placeholder="Ako navodi alergiju, upisati lijek/reakciju." onChange={event => setReceptionDraft(current => ({ ...current, drug_allergy_text: event.target.value }))}/></label>
        </div>
        {receptionWarnings().length > 0 && <div className="reception-warning" role="alert"><strong>Crvena napomena za liječnika/anesteziologa</strong>{receptionWarnings().map(item => <small key={item}>{item}</small>)}</div>}
        <footer><button type="button" onClick={() => setReceptionModal("identity")}>Natrag</button><button type="button" className="primary" disabled={receptionBusy} onClick={completeReception}>{receptionBusy ? "Spremam…" : "Provjereno"}</button></footer>
      </section>
    </div>}
    {confirmation && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && setConfirmation(null)}>
      <section className="modal-panel" role="dialog" aria-modal="true" aria-labelledby="workspace-confirmation-title">
        <header><div><span className="eyebrow">Potvrda radnje</span><h2 id="workspace-confirmation-title">{confirmation.title}</h2></div></header>
        <p>{confirmation.text}</p>
        {confirmation.reasonLabel && <label>{confirmation.reasonLabel}<textarea autoFocus rows={3} value={confirmation.reason ?? ""} onChange={event => setConfirmation(current => current ? { ...current, reason: event.target.value } : current)}/></label>}
        <footer><button type="button" onClick={() => setConfirmation(null)}>Odustani</button><button type="button" className="primary" disabled={Boolean(confirmation.reasonLabel && !confirmation.reason?.trim())} onClick={async () => { const current = confirmation; setConfirmation(null); await current.action(current.reason); }}>{confirmation.confirmLabel}</button></footer>
      </section>
    </div>}
  </section>;
}
