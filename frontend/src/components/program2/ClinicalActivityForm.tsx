import { forwardRef, useEffect, useImperativeHandle, useRef, useState, type ReactNode } from "react";
import { Check, FileSignature, Play, Plus, Save, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ApiError, api, type ApiValidationDetail } from "../../api/client";
import { clinicalFormStructuredTypes } from "../../constants/clinicalRegistries";
import type { ClinicalFormField, ClinicalFormInstance, JourneyActivity } from "../../types/program2";
import { activityClockTime } from "./journeyStatus";

function inputValue(value: unknown) { return value == null ? "" : String(value); }
const formStatusLabels: Record<string, string> = { draft: "Skica", in_progress: "U izradi", completed: "Dovršeno", signed: "Potpisano", amended: "Zamijenjeno ispravkom", void: "Poništeno" };

function StructuredField({ field, value, disabled, error, onChange }: { field: ClinicalFormField; value: unknown; disabled: boolean; error?: string; onChange: (value: unknown) => void }) {
  const rows = Array.isArray(value) ? value as Array<Record<string, unknown>> : [];
  const itemFields = field.item_fields ?? [];
  const add = () => onChange([...rows, { item_id: crypto.randomUUID() }]);
  const update = (index: number, key: string, itemValue: unknown) => onChange(rows.map((row, position) => position === index ? { ...row, [key]: itemValue } : row));
  return <fieldset className="structured-repeatable-field" disabled={disabled} aria-invalid={Boolean(error)}><legend>{field.label}{field.required && " *"}</legend>
    {rows.map((row, index) => <article key={String(row.item_id)}><header><strong>Stavka {index + 1}</strong><button type="button" aria-label={`Ukloni stavku ${index + 1}`} onClick={() => onChange(rows.filter((_, position) => position !== index))}><Trash2 size={15}/></button></header><div className="structured-item-grid">
      {itemFields.map(item => <label key={item.field_key}>{item.label}{item.required && " *"}{
        item.type === "select"
          ? <select value={inputValue(row[item.field_key])} onChange={event => update(index, item.field_key, event.target.value)}><option value="">Odaberite</option>{(item.options ?? []).map(option => { const normalized = typeof option === "string" ? { value: option, label: option } : option; return <option key={normalized.value} value={normalized.value}>{normalized.label}</option>; })}</select>
          : item.type === "checkbox"
            ? <input type="checkbox" checked={Boolean(row[item.field_key])} onChange={event => update(index, item.field_key, event.target.checked)}/>
            : item.type === "long_text" || item.type === "rich_text_limited"
              ? <textarea rows={3} value={inputValue(row[item.field_key])} onChange={event => update(index, item.field_key, event.target.value)}/>
              : <input type={item.type === "integer" || item.type === "decimal" ? "number" : item.type === "time" ? "time" : item.type === "date" ? "date" : "text"} value={inputValue(row[item.field_key])} onChange={event => update(index, item.field_key, event.target.value)}/>
      }</label>)}
    </div></article>)}
    <button type="button" onClick={add} disabled={disabled || rows.length >= (field.max_items ?? 50)}><Plus size={15}/>Dodaj stavku</button>
    {field.help_text && <small>{field.help_text}</small>}
    {error && <small className="field-error" role="alert">{error}</small>}
  </fieldset>;
}

function FormField({ field, value, disabled, error, onChange }: { field: ClinicalFormField; value: unknown; disabled: boolean; error?: string; onChange: (value: unknown) => void }) {
  if (clinicalFormStructuredTypes.has(field.type)) return <StructuredField field={field} value={value} disabled={disabled} error={error} onChange={onChange}/>;
  const id = `clinical-field-${field.field_key}`;
  const errorId = `${id}-error`;
  if (field.type === "checkbox") return <label className="clinical-form-check" htmlFor={id}><input id={id} type="checkbox" checked={Boolean(value)} disabled={disabled} aria-invalid={Boolean(error)} aria-describedby={error ? errorId : undefined} onChange={event => onChange(event.target.checked)}/><span>{field.label}{field.required && " *"}{error && <small id={errorId} className="field-error" role="alert">{error}</small>}</span></label>;
  if (field.type === "select") return <label className="encounter-field" htmlFor={id}>{field.label}{field.required && " *"}<select id={id} value={inputValue(value)} disabled={disabled} aria-invalid={Boolean(error)} aria-describedby={error ? errorId : undefined} onChange={event => onChange(event.target.value)}><option value="">Odaberite</option>{(field.options ?? []).map(option => { const item = typeof option === "string" ? { value: option, label: option } : option; return <option key={item.value} value={item.value}>{item.label}</option>; })}</select>{error && <small id={errorId} className="field-error" role="alert">{error}</small>}</label>;
  if (["short_text", "integer", "decimal", "date", "time"].includes(field.type)) return <label className="encounter-field" htmlFor={id}>{field.label}{field.required && " *"}<input id={id} type={field.type === "integer" || field.type === "decimal" ? "number" : ["date", "time"].includes(field.type) ? field.type : "text"} value={inputValue(value)} disabled={disabled} aria-invalid={Boolean(error)} aria-describedby={error ? errorId : undefined} onChange={event => onChange(event.target.value)}/>{error && <small id={errorId} className="field-error" role="alert">{error}</small>}</label>;
  const legacyList = ["multi_select", "diagnosis_list", "medication_list", "procedure_intervention_list", "specimen_list", "anatomical_site"].includes(field.type);
  return <label className="encounter-field" htmlFor={id}>{field.label}{field.required && " *"}<textarea id={id} rows={4} value={Array.isArray(value) ? value.join(", ") : inputValue(value)} disabled={disabled} aria-invalid={Boolean(error)} aria-describedby={error ? errorId : undefined} onChange={event => onChange(legacyList ? event.target.value.split(",").map(item => item.trim()).filter(Boolean) : event.target.value)}/>{field.help_text && <small>{field.help_text}</small>}{error && <small id={errorId} className="field-error" role="alert">{error}</small>}</label>;
}

type Confirmation = { title: string; text: string; action: () => Promise<void> };
type FormConflict = { actualRevision: number; updatedAt: string | null; serverData: Record<string, unknown> };

export type ClinicalActivityFormHandle = {
  hasUnsavedChanges: () => boolean;
  saveDraft: () => Promise<boolean>;
  discardLocalChanges: () => void;
};

type ClinicalActivityFormProps = { journeyId: number; activity: JourneyActivity; serviceName: string; onChanged: () => Promise<void> };

export const ClinicalActivityForm = forwardRef<ClinicalActivityFormHandle, ClinicalActivityFormProps>(function ClinicalActivityForm({ journeyId, activity, serviceName, onChanged }, ref) {
  const navigate = useNavigate();
  const [form, setForm] = useState<ClinicalFormInstance | null>(null);
  const [data, setData] = useState<Record<string, unknown>>({});
  const [savedData, setSavedData] = useState<Record<string, unknown>>({});
  const [busy, setBusy] = useState(false); const [loadingForm, setLoadingForm] = useState(true); const [error, setError] = useState(""); const [confirmation, setConfirmation] = useState<Confirmation | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({}); const [statusMessage, setStatusMessage] = useState(""); const [conflict, setConflict] = useState<FormConflict | null>(null); const [pendingRoute, setPendingRoute] = useState<string | null>(null);
  const completionKey = useRef(crypto.randomUUID());
  const base = `/api/patient-journeys/${journeyId}/activities/${activity.id}`;
  useEffect(() => {
    let active = true;
    setForm(null); setData({}); setSavedData({}); setError(""); setFieldErrors({}); setStatusMessage(""); setConflict(null); setConfirmation(null); setLoadingForm(true); completionKey.current = crypto.randomUUID();
    api<ClinicalFormInstance>(`${base}/form`, { suppressErrorToast: true })
      .then(item => { if (active) { setForm(item); setData(item.data_json); setSavedData(item.data_json); } })
      .catch(reason => { if (active && (!(reason instanceof ApiError) || reason.status !== 404)) setError(reason instanceof Error ? reason.message : "Obrazac nije učitan."); })
      .finally(() => { if (active) setLoadingForm(false); });
    return () => { active = false; };
  }, [activity.id, base]);
  async function run(action: () => Promise<void>) { setBusy(true); setError(""); setFieldErrors({}); setStatusMessage(""); setConflict(null); try { await action(); return true; } catch (reason) { if (reason instanceof ApiError && reason.detail && typeof reason.detail === "object") { const details = reason.detail as ApiValidationDetail; const invalidFields = details.fields ?? details.errors ?? []; setFieldErrors(Object.fromEntries(invalidFields.filter(item => item.field_key && item.message).map(item => [item.field_key as string, item.message as string]))); if (details.code === "stale_form" && details.actual_revision_number != null && details.server_data) setConflict({ actualRevision: details.actual_revision_number, updatedAt: details.current_updated_at ?? null, serverData: details.server_data }); } setError(reason instanceof Error ? reason.message : "Radnja nije spremljena."); return false; } finally { setBusy(false); } }
  async function resolve() { return run(async () => { const item = await api<ClinicalFormInstance>(`${base}/form/resolve`, { method: "POST" }); setForm(item); setData(item.data_json); setSavedData(item.data_json); await onChanged(); }); }
  async function save() { if (!form) return false; return run(async () => { const item = await api<ClinicalFormInstance>(`${base}/form`, { method: "PATCH", body: JSON.stringify({ data, expected_instance_id: form.id, expected_revision_number: form.revision_number }) }); setForm(item); setData(item.data_json); setSavedData(item.data_json); setStatusMessage("Skica spremljena"); completionKey.current = crypto.randomUUID(); }); }
  async function completeForm() { if (!form) return; await run(async () => { const item = await api<ClinicalFormInstance>(`${base}/form/complete`, { method: "POST", body: JSON.stringify({ data, expected_instance_id: form.id, expected_revision_number: form.revision_number, idempotency_key: completionKey.current }) }); setForm(item); setData(item.data_json); setSavedData(item.data_json); setStatusMessage("Obrazac dovršen"); await onChanged(); }); }
  async function sign() { await run(async () => { setForm(await api<ClinicalFormInstance>(`${base}/form/sign`, { method: "POST" })); await onChanged(); }); }
  async function start() { await run(async () => { if (activity.status === "planned") await api(`${base}/transition`, { method: "POST", body: JSON.stringify({ target_status: "ready" }) }); await api(`${base}/transition`, { method: "POST", body: JSON.stringify({ target_status: "in_progress" }) }); await onChanged(); }); }
  async function completeActivity() { await run(async () => { await api(`${base}/transition`, { method: "POST", body: JSON.stringify({ target_status: "completed" }) }); await onChanged(); }); }
  const ask = (title: string, text: string, action: () => Promise<void>) => setConfirmation({ title, text, action });
  const locked = form ? ["completed", "signed", "amended", "void"].includes(form.status) : false;
  const dirty = Boolean(form) && JSON.stringify(data) !== JSON.stringify(savedData);
  const changeField = (key: string, value: unknown) => { setData(current => ({ ...current, [key]: value })); setFieldErrors(current => { const next = { ...current }; delete next[key]; return next; }); setStatusMessage(""); };
  const discardLocalChanges = () => { setData(savedData); setFieldErrors({}); setError(""); setConflict(null); setStatusMessage(""); };
  useImperativeHandle(ref, () => ({ hasUnsavedChanges: () => dirty, saveDraft: save, discardLocalChanges }), [dirty, form, data, savedData]);
  useEffect(() => {
    const firstInvalidKey = Object.keys(fieldErrors)[0];
    if (!firstInvalidKey) return;
    const target = document.getElementById(`clinical-field-${firstInvalidKey}`);
    target?.scrollIntoView?.({ block: "center", behavior: "smooth" });
    target?.focus();
  }, [fieldErrors]);
  useEffect(() => {
    if (!dirty) return;
    const protectUnload = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    const protectInternalLink = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const target = event.target instanceof Element ? event.target.closest("a[href]") : null;
      if (!(target instanceof HTMLAnchorElement) || target.target === "_blank" || target.hasAttribute("download")) return;
      const url = new URL(target.href, window.location.href);
      if (url.origin !== window.location.origin || `${url.pathname}${url.search}${url.hash}` === `${window.location.pathname}${window.location.search}${window.location.hash}`) return;
      event.preventDefault(); event.stopPropagation(); setPendingRoute(`${url.pathname}${url.search}${url.hash}`);
    };
    window.addEventListener("beforeunload", protectUnload);
    document.addEventListener("click", protectInternalLink, true);
    return () => { window.removeEventListener("beforeunload", protectUnload); document.removeEventListener("click", protectInternalLink, true); };
  }, [dirty]);
  let primary: { label: string; icon: ReactNode; disabled?: boolean; action: () => void } | null = null;
  if (form && ["draft", "in_progress"].includes(form.status)) primary = { label: "Dovrši obrazac", icon: <Check size={15}/>, action: () => ask("Dovrši obrazac", "Provjerite obvezna polja prije zaključavanja radne verzije.", completeForm) };
  else if (form?.status === "completed") primary = { label: "Potpiši nalaz", icon: <FileSignature size={15}/>, action: () => ask("Potpiši nalaz", "Potpisana verzija je nepromjenjiva; ispravak stvara novu verziju.", sign) };
  else if (form?.status === "signed" && ["planned", "ready"].includes(activity.status)) primary = { label: "Započni aktivnost", icon: <Play size={15}/>, action: start };
  else if (form?.status === "signed" && activity.status === "in_progress") primary = { label: "Dovrši aktivnost", icon: <Check size={15}/>, action: () => ask("Dovrši aktivnost", "Potvrdite da su nalaz, intervencije, komplikacije i uzorci evidentirani.", completeActivity) };
  const conflictRows = conflict && form ? form.form_version.sections_json.flatMap(section => section.fields).filter(field => JSON.stringify(data[field.field_key]) !== JSON.stringify(conflict.serverData[field.field_key])).map(field => ({ label: field.label, local: inputValue(data[field.field_key]), server: inputValue(conflict.serverData[field.field_key]) })) : [];
  const reloadServerVersion = () => { if (!form || !conflict) return; setForm({ ...form, data_json: conflict.serverData, revision_number: conflict.actualRevision, updated_at: conflict.updatedAt ?? form.updated_at }); setData(conflict.serverData); setSavedData(conflict.serverData); setConflict(null); setError(""); setFieldErrors({}); setStatusMessage("Učitana je novija spremljena verzija"); completionKey.current = crypto.randomUUID(); };
  return <section className="journey-panel clinical-activity-form">
    <header><div><span className="eyebrow">Aktivnost {activity.sequence}</span><h2>{serviceName}</h2><p>{activityClockTime(activity.planned_start)}–{activityClockTime(activity.planned_end)}</p></div><span className={`activity-status ${activity.status}`}>{activity.status === "in_progress" ? "U tijeku" : activity.status === "completed" ? "Završeno" : "Planirano"}</span></header>
    {error && <p className="inline-error" role="alert">{error}</p>}
    {conflict && <aside className="clinical-form-conflict" role="alert"><strong>Drugi korisnik je izmijenio ovaj nalaz</strong><p>Vaš lokalni unos ostaje vidljiv i nije automatski spojen sa spremljenom verzijom.</p>{conflictRows.length > 0 && <details><summary>Usporedi verzije</summary>{conflictRows.map(row => <div key={row.label}><b>{row.label}</b><span>Lokalno: {row.local || "—"}</span><span>Na serveru: {row.server || "—"}</span></div>)}</details>}<button type="button" onClick={reloadServerVersion}>Učitaj verziju sa servera</button></aside>}
    {loadingForm && <div className="clinical-form-empty"><p>Učitavanje kliničkog obrasca…</p></div>}
    {!loadingForm && !form && <div className="clinical-form-empty"><p>Za ovu aktivnost još nije otvoren klinički obrazac.</p><button type="button" className="primary" disabled={busy} onClick={resolve}>Otvori obrazac</button></div>}
    {form && <><div className="clinical-form-meta"><span>Verzija {form.form_version.version}</span><span>{formStatusLabels[form.status] ?? "Nepoznato stanje"}</span>{dirty && <span className="clinical-form-dirty" role="status">Nespremljene promjene</span>}{statusMessage && <span className="clinical-form-saved" role="status">{statusMessage}</span>}</div>{form.form_version.sections_json.map(section => <fieldset key={section.section_key} disabled={busy || locked}><legend>{section.title ?? "Klinički nalaz"}</legend><div className="clinical-form-grid">{section.fields.map(field => <FormField key={field.field_key} field={field} value={data[field.field_key]} disabled={busy || locked} error={fieldErrors[field.field_key]} onChange={value => changeField(field.field_key, value)}/>)}</div></fieldset>)}<div className="clinical-form-actions">{!locked && <button type="button" disabled={busy || !dirty} onClick={save}><Save size={15}/>{busy ? "Spremanje…" : "Spremi skicu"}</button>}{primary && <button type="button" className="primary" disabled={busy || primary.disabled} onClick={primary.action}>{primary.icon}{busy ? "Spremanje…" : primary.label}</button>}</div></>}
    {pendingRoute && <div className="modal-backdrop"><section className="modal-panel clinical-draft-navigation" role="dialog" aria-modal="true" aria-labelledby="route-draft-title"><header><div><span className="eyebrow">Nespremljena skica</span><h2 id="route-draft-title">Napustiti klinički obrazac?</h2></div></header><p>Prije odlaska odaberite što želite učiniti s lokalnim promjenama.</p><footer><button type="button" onClick={() => setPendingRoute(null)}>Ostani</button><button type="button" onClick={() => { discardLocalChanges(); const target = pendingRoute; setPendingRoute(null); navigate(target); }}>Odbaci i nastavi</button><button type="button" className="primary" onClick={async () => { if (await save()) { const target = pendingRoute; setPendingRoute(null); navigate(target); } }}>Spremi skicu i nastavi</button></footer></section></div>}
    {confirmation && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && setConfirmation(null)}><section className="modal-panel clinical-confirmation" role="dialog" aria-modal="true" aria-labelledby="clinical-confirm-title"><header><div><span className="eyebrow">Klinička potvrda</span><h2 id="clinical-confirm-title">{confirmation.title}</h2></div></header><p>{confirmation.text}</p><footer><button type="button" onClick={() => setConfirmation(null)}>Odustani</button><button type="button" className="primary" onClick={async () => { const action = confirmation.action; setConfirmation(null); await action(); }}>Potvrdi</button></footer></section></div>}
  </section>;
});
