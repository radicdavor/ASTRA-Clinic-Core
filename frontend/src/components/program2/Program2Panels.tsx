import { ExternalLink, Plus, ShieldAlert, Trash2 } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import type { InventoryItem } from "../../types";
import type { AIDiagnosisSuggestion } from "../../types/program2";
import { journeyStatusLabel } from "./journeyStatus";

export function Panel({ title, children }: { title: string; children: ReactNode }) {
  return <section className="journey-panel"><h2>{title}</h2>{children}</section>;
}

export function DocumentReadinessPanel({ status }: { status: string }) {
  return <Panel title="Dokumenti"><p>Status: <strong>{journeyStatusLabel(status)}</strong></p></Panel>;
}

const reviewStates = [
  ["not_confirmed", "Nije potvrđeno"],
  ["confirmed", "Potvrđeno"],
  ["not_applicable", "Nije primjenjivo"],
  ["requires_clinician_review", "Treba liječničku provjeru"],
  ["blocked", "Blokirano"],
];

export function PreparationPanel({ status, data, activityData, onUpdate, onActivityUpdate }: { status: string; data?: any; activityData?: any; onUpdate?: (key: string, state: string) => Promise<void>; onActivityUpdate?: (id: number, state: string) => Promise<void> }) {
  const requirements = Object.entries(data?.requirement_states_json ?? {}) as Array<[string, string]>;
  const labels = new Map<string, string>((data?.template?.requirements_json ?? []).map((item: any) => [item.key, item.label]));
  return <Panel title="Priprema">
    <p>Status: <strong>{journeyStatusLabel(status)}</strong></p>
    {activityData?.requirements?.map((item: any) => <article className={`journey-review-row activity-preparation-row ${item.contradictory ? "blocked" : ""}`} key={item.requirement_key}>
      <span><strong>{item.label}</strong><small>{item.patient_instruction}</small><small>Odnosi se na: {item.activities.map((activity: any) => activity.service_name).join(", ")}</small></span>
      {item.activities.map((activity: any) => <label key={activity.requirement_id}>{activity.service_name}<select aria-label={`${item.label} — ${activity.service_name}`} value={activity.state ?? item.state} onChange={event => onActivityUpdate?.(activity.requirement_id, event.target.value)}>{reviewStates.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>)}
      {item.contradictory && <small className="inline-error">Upute su protuslovne i zahtijevaju kliničku provjeru.</small>}
    </article>)}
    {data?.template && <p className="journey-panel-context"><strong>{data.template.name}</strong><small>Verzija {data.template.version}</small></p>}
    {requirements.map(([key, state]) => <label className="journey-review-row" key={key}><span>{labels.get(key) ?? key}</span><select value={state} onChange={event => onUpdate?.(key, event.target.value)}>{reviewStates.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>)}
    {!data && !activityData?.requirements?.length && <p>Priprema nije dodijeljena.</p>}
  </Panel>;
}

function CheckInItemRow({ item, onUpdate }: { item: any; onUpdate: (id: number, state: string, note: string) => Promise<void> }) {
  const [state, setState] = useState(item.state);
  const [note, setNote] = useState(item.note ?? "");
  const [busy, setBusy] = useState(false);
  useEffect(() => { setState(item.state); setNote(item.note ?? ""); }, [item.state, item.note]);
  async function save() { setBusy(true); try { await onUpdate(item.id, state, note); } finally { setBusy(false); } }
  return <div className="journey-check-editor">
    <div><strong>{item.label}</strong>{item.requires_clinician && <small>Liječnička odluka</small>}</div>
    <select aria-label={`${item.label} — stanje`} value={state} onChange={event => setState(event.target.value)}>{reviewStates.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
    <input aria-label={`${item.label} — napomena`} placeholder="Napomena" value={note} onChange={event => setNote(event.target.value)}/>
    <button type="button" disabled={busy || (state === item.state && note === (item.note ?? ""))} onClick={save}>Spremi</button>
  </div>;
}

export function CheckInChecklist({ data, onUpdate, onConfirmAdministrative }: { data: any; onUpdate?: (id: number, state: string, note: string) => Promise<void>; onConfirmAdministrative?: () => Promise<void> }) {
  const administrativeOpen = data?.items?.some((item: any) => !item.requires_clinician && !["confirmed", "not_applicable"].includes(item.state));
  return <Panel title="Prijemna provjera">
    {administrativeOpen && onConfirmAdministrative && <div className="check-in-quick-action"><span><strong>Administrativni podaci</strong><small>Identitet, kontakt, platitelj i zaprimljeni dokumenti.</small></span><button type="button" className="primary" onClick={onConfirmAdministrative}>Potvrdi administrativne podatke</button></div>}
    {data?.items?.map((item: any) => onUpdate ? <CheckInItemRow item={item} onUpdate={onUpdate} key={item.id}/> : <p className="journey-check" key={item.id}><span>{item.label}</span><strong>{journeyStatusLabel(item.state)}</strong></p>)}
    {!data && <p>Provjera nije započeta.</p>}
  </Panel>;
}

export function PatientTimeline({ items }: { items: any[] }) {
  return <Panel title="Vremenska crta">{items.map(item => <article className="journey-timeline-item" key={`${item.event_type}-${item.date}-${item.title}`}><small>{new Date(item.date).toLocaleString("hr-HR")}</small><strong>{item.title}</strong>{item.summary && <span>{item.summary}</span>}{item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer">Otvori izvor <ExternalLink size={13}/></a>}</article>)}</Panel>;
}

export function SourceDocumentViewer({ documents, onReview }: { documents: any[]; onReview?: (id: number) => Promise<void> }) {
  return <Panel title="Izvorni dokumenti">{documents.map(item => <div className="journey-source" key={item.id}><a href={`/api/clinical-documents/${item.id}/source`} target="_blank" rel="noreferrer"><span><strong>{item.title}</strong><small>{journeyStatusLabel(item.review_status)}</small></span><ExternalLink size={15}/></a>{item.review_status !== "reviewed" && onReview && <button type="button" onClick={() => onReview(item.id)}>Označi pregledanim</button>}</div>)}{!documents.length && <p>Nema povezanih dokumenata.</p>}</Panel>;
}

function AISummaryFact({ summaryId, fact, onReview }: { summaryId: number; fact: any; onReview?: (summaryId: number, factId: number, action: "accept" | "reject") => Promise<void> }) {
  return <article className="journey-ai-fact"><strong>{fact.statement}</strong><small>{fact.fact_type} · {journeyStatusLabel(fact.review_status)}</small>{fact.source_document_id && <a href={`/api/clinical-documents/${fact.source_document_id}/source`} target="_blank" rel="noreferrer">Otvori izvor #{fact.source_document_id}</a>}{fact.review_status === "pending_review" && onReview && <div className="fact-review-actions"><button type="button" onClick={() => onReview(summaryId, fact.id, "reject")}>Odbaci</button><button type="button" className="primary" onClick={() => onReview(summaryId, fact.id, "accept")}>Prihvati činjenicu</button></div>}</article>;
}

export function AISummaryPanel({ summary, onGenerate, onReview }: { summary: any; onGenerate?: () => Promise<void>; onReview?: (summaryId: number, factId: number, action: "accept" | "reject") => Promise<void> }) {
  const facts = summary?.facts ?? [];
  const risks = facts.filter((fact: any) => /risk|rizik/i.test(fact.fact_type)).slice(0, 3);
  const missing = facts.filter((fact: any) => /missing|nedost/i.test(fact.fact_type)).slice(0, 3);
  const highlightedIds = new Set([...risks, ...missing].map((fact: any) => fact.id));
  const important = facts.filter((fact: any) => !highlightedIds.has(fact.id)).slice(0, 5);
  const shownIds = new Set([...important, ...risks, ...missing].map((fact: any) => fact.id));
  const remaining = facts.filter((fact: any) => !shownIds.has(fact.id));
  return <Panel title="AI prijedlog — pregled obavezan">
    {summary && <p className="journey-panel-context"><strong>{journeyStatusLabel(summary.status)}</strong><small>{summary.model_name} · {new Date(summary.generated_at).toLocaleString("hr-HR")}</small></p>}
    {summary?.limitations_json?.slice(0, 3).map((item: string) => <small className="journey-limitation" key={item}>{item}</small>)}
    {important.length > 0 && <section className="ai-summary-section"><h3>Najvažnije</h3>{important.map((fact: any) => <AISummaryFact summaryId={summary.id} fact={fact} onReview={onReview} key={fact.id}/>)}</section>}
    {risks.length > 0 && <section className="ai-summary-section"><h3>Rizici za današnji pregled</h3>{risks.map((fact: any) => <AISummaryFact summaryId={summary.id} fact={fact} onReview={onReview} key={fact.id}/>)}</section>}
    {missing.length > 0 && <section className="ai-summary-section"><h3>Što nedostaje</h3>{missing.map((fact: any) => <AISummaryFact summaryId={summary.id} fact={fact} onReview={onReview} key={fact.id}/>)}</section>}
    {remaining.length > 0 && <details className="ai-summary-full"><summary>Prikaži cijeli AI sažetak</summary>{remaining.map((fact: any) => <AISummaryFact summaryId={summary.id} fact={fact} onReview={onReview} key={fact.id}/>)}</details>}
    {!summary && <><p>Sažetak nije generiran.</p>{onGenerate && <button type="button" onClick={onGenerate}>Generiraj iz izvornih dokumenata</button>}</>}
  </Panel>;
}

export function EncounterPanel({ draft, setDraft, status, aiDiagnoses = [], aiDiagnosisCapability, diagnosisBusy = false, onOpen, onSave, onComplete, onSuggestDiagnoses, onDecideDiagnosis }: { draft: any; setDraft: (value: any) => void; status?: string; aiDiagnoses?: AIDiagnosisSuggestion[]; aiDiagnosisCapability?: { enabled: boolean; reason: string | null }; diagnosisBusy?: boolean; onOpen: () => void; onSave: () => void; onComplete: () => void; onSuggestDiagnoses?: () => void; onDecideDiagnosis?: (diagnosis: AIDiagnosisSuggestion, action: "accept" | "reject") => void }) {
  const fields = [
    ["anamnesis", "Anamneza", "Glavna tegoba, tijek bolesti, ranije bolesti, terapija i alergije."],
    ["examination", "Status", "Objektivni status utvrđen tijekom pregleda."],
    ["patient_findings", "Nalazi koje pacijent donosi", "Sažeto navedite vrstu, datum i važan sadržaj donesenih nalaza."],
    ["opinion", "Mišljenje", "Kliničko mišljenje liječnika."],
    ["recommendations", "Preporuke", "Dogovorene preporuke i sljedeći koraci."],
    ["diagnosis", "Dijagnoze (WHO ICD-10)", "Jedna dijagnoza po retku, npr. K21.9 — Gastroezofagealna refluksna bolest."],
  ];
  return <Panel title="Pregled pacijenta">
    <div className="encounter-note-heading"><span>Status pregleda: <strong>{status ? journeyStatusLabel(status) : "nije otvoren"}</strong></span><small>Sadržaj unosi i potvrđuje liječnik.</small></div>
    {status ? <div className="encounter-note-grid">{fields.map(([key, label, placeholder]) => <label className={`encounter-field encounter-field-${key}`} key={key}><span className="encounter-field-title"><span>{label}</span>{key === "diagnosis" && status === "in_progress" && aiDiagnosisCapability?.enabled && onSuggestDiagnoses && <button type="button" className="ai-diagnosis-button" aria-label="AI predloži" disabled={diagnosisBusy} onClick={onSuggestDiagnoses}>{diagnosisBusy ? "AI obrađuje…" : "AI predloži"}</button>}</span><textarea aria-label={label} disabled={status === "completed"} value={draft[key] ?? ""} placeholder={placeholder} onChange={event => setDraft({ ...draft, [key]: event.target.value })}/>{key === "diagnosis" && <><small>Formalnu dijagnozu unosi i potvrđuje liječnik.</small>{status === "in_progress" && aiDiagnosisCapability && !aiDiagnosisCapability.enabled && <small className="ai-diagnosis-disabled">{aiDiagnosisCapability.reason ?? "AI prijedlozi dijagnoza su isključeni."}</small>}</>}</label>)}</div> : <div className="encounter-empty"><p>Pregled još nije započet.</p><button className="primary" onClick={onOpen}>Započni pregled</button></div>}
    {status === "in_progress" && aiDiagnoses.length > 0 && <section className="ai-diagnosis-panel" aria-label="AI prijedlozi dijagnoza"><header><strong>AI prijedlozi dijagnoza</strong><small>Nisu dio kliničkog nalaza dok ih liječnik pojedinačno ne prihvati.</small></header>{aiDiagnoses.map(item => <article key={`${item.request_id}-${item.code}`}><span><strong>{item.code} — {item.title}</strong><small>{item.provider} · {item.model}</small></span><div><button type="button" onClick={() => onDecideDiagnosis?.(item, "reject")}>Odbaci</button><button type="button" className="primary" onClick={() => onDecideDiagnosis?.(item, "accept")}>Dodaj u dijagnoze</button></div></article>)}</section>}
    {status === "in_progress" && <div className="form-actions encounter-note-actions"><button onClick={onSave}>Spremi pregled</button><button className="primary" onClick={onComplete}>Dovrši pregled</button></div>}
  </Panel>;
}

type ConsumableDraft = { inventory_item_id: string; quantity: string; reason: string };
export function ConsumablesPanel({ status, canConfirm, items, onConfirm }: { status: string; canConfirm: boolean; items: InventoryItem[]; onConfirm?: (lines: Array<{ inventory_item_id: number; quantity: string; reason?: string }>, notApplicable: boolean) => Promise<void> }) {
  const [lines, setLines] = useState<ConsumableDraft[]>([{ inventory_item_id: "", quantity: "1", reason: "" }]);
  const valid = lines.every(line => line.inventory_item_id && Number(line.quantity) > 0);
  function update(index: number, patch: Partial<ConsumableDraft>) { setLines(current => current.map((line, position) => position === index ? { ...line, ...patch } : line)); }
  return <Panel title="Potrošni materijal"><p>Status: <strong>{journeyStatusLabel(status)}</strong></p>{canConfirm && !["confirmed", "not_applicable"].includes(status) && <div className="consumables-editor">{lines.map((line, index) => <div className="consumable-line" key={index}><select aria-label={`Materijal ${index + 1}`} value={line.inventory_item_id} onChange={event => update(index, { inventory_item_id: event.target.value })}><option value="">Odaberite materijal</option>{items.map(item => <option key={item.id} value={item.id}>{item.name} ({item.current_stock} {item.unit_of_measure})</option>)}</select><input aria-label={`Količina ${index + 1}`} type="number" min="0.01" step="0.01" value={line.quantity} onChange={event => update(index, { quantity: event.target.value })}/><input aria-label={`Razlog ${index + 1}`} placeholder="Razlog ili napomena" value={line.reason} onChange={event => update(index, { reason: event.target.value })}/>{lines.length > 1 && <button type="button" aria-label={`Ukloni materijal ${index + 1}`} onClick={() => setLines(current => current.filter((_, position) => position !== index))}><Trash2 size={15}/></button>}</div>)}<button type="button" onClick={() => setLines(current => [...current, { inventory_item_id: "", quantity: "1", reason: "" }])}><Plus size={15}/>Dodaj stavku</button><div className="form-actions"><button type="button" onClick={() => onConfirm?.([], true)}>Nije korišten materijal</button><button type="button" className="primary" disabled={!valid} onClick={() => onConfirm?.(lines.map(line => ({ inventory_item_id: Number(line.inventory_item_id), quantity: line.quantity, reason: line.reason || undefined })), false)}>Potvrdi materijal</button></div>{!items.length && <small>Za evidentiranje stavki potreban je pristup inventaru.</small>}</div>}</Panel>;
}

export function BillingPanel({ status, invoice, onPrepare }: { status: string; invoice?: any; onPrepare?: () => void }) {
  return <Panel title="Račun"><p>Status: <strong>{journeyStatusLabel(status)}</strong></p>{invoice && <p>{invoice.number}<br/><strong>{invoice.total} EUR</strong></p>}{status === "ready" && onPrepare && <button className="primary" onClick={onPrepare}>Izradi i izdaj račun</button>}</Panel>;
}

export function PaymentPanel({ status, invoice, stage, onPay, onDefer, onClose }: { status: string; invoice?: any; stage?: string; onPay?: (amount: string, method: string) => void; onDefer?: () => void; onClose?: () => void }) {
  const [amount, setAmount] = useState(invoice?.total ?? ""); const [method, setMethod] = useState("card");
  useEffect(() => { if (invoice?.total) setAmount(invoice.total); }, [invoice?.total]);
  const methods = [["card", "Kartica"], ["cash", "Gotovina"], ["bank_transfer", "Bankovna uplata"], ["insurance", "Osiguranje"]];
  return <Panel title="Plaćanje"><p>Status: <strong>{journeyStatusLabel(status)}</strong></p>{status === "unpaid" && <><p>Puni iznos: <strong>{invoice?.total ?? amount} EUR</strong></p><div className="payment-method-actions">{methods.map(([value, label]) => <button type="button" key={value} onClick={() => onPay?.(invoice?.total ?? amount, value)}>{label}</button>)}</div><details className="partial-payment"><summary>Drugi iznos ili djelomična uplata</summary><label className="encounter-field">Iznos<input type="number" min="0.01" step="0.01" value={amount} onChange={event => setAmount(event.target.value)}/></label><label className="encounter-field">Način<select value={method} onChange={event => setMethod(event.target.value)}>{methods.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><button type="button" disabled={!amount || Number(amount) <= 0} onClick={() => onPay?.(amount, method)}>Evidentiraj drugi iznos</button></details><button type="button" className="payment-defer" onClick={onDefer}>Platit će naknadno</button></>}{["paid", "deferred", "refunded", "cancelled"].includes(status) && (stage === "completed" ? <p className="payment-complete">Tijek je automatski završen.</p> : onClose && <button className="primary" onClick={onClose}>Završi tijek pacijenta</button>)}</Panel>;
}

function BlockerItem({ item, onResolve }: { item: any; onResolve: (id: number, note: string) => Promise<void> }) {
  const [note, setNote] = useState(""); const [busy, setBusy] = useState(false);
  async function resolve() { setBusy(true); try { await onResolve(item.id, note); } finally { setBusy(false); } }
  return <div className="journey-blocker"><ShieldAlert size={15}/><span><strong>{item.title}</strong><small>{item.details}</small><textarea aria-label={`Razrješenje — ${item.title}`} placeholder="Upišite kako je stavka razriješena" value={note} onChange={event => setNote(event.target.value)}/><button type="button" disabled={busy || note.trim().length < 2} onClick={resolve}>Razriješi blokator</button></span></div>;
}

export function BlockerPanel({ items, onResolve }: { items: any[]; onResolve?: (id: number, note: string) => Promise<void> }) {
  const open = items.filter(item => item.status === "open");
  return <Panel title="Potrebno riješiti">{open.map(item => onResolve ? <BlockerItem item={item} onResolve={onResolve} key={item.id}/> : <p className="journey-blocker" key={item.id}><ShieldAlert size={15}/><span><strong>{item.title}</strong><small>{item.details}</small></span></p>)}{!open.length && <p>Nema otvorenih blokatora.</p>}</Panel>;
}
