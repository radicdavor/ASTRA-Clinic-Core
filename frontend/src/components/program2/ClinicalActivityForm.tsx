import { useEffect, useState } from "react";
import { Check, FileSignature, Play, Save } from "lucide-react";
import { api } from "../../api/client";
import type { ClinicalFormField, ClinicalFormInstance, JourneyActivity } from "../../types/program2";
import { activityClockTime } from "./journeyStatus";


function valueForInput(value: unknown) {
  if (Array.isArray(value)) return value.join(", ");
  return value == null ? "" : String(value);
}

function FormField({ field, value, disabled, onChange }: { field: ClinicalFormField; value: unknown; disabled: boolean; onChange: (value: unknown) => void }) {
  const id = `clinical-field-${field.field_key}`;
  if (field.type === "checkbox") return <label className="clinical-form-check" htmlFor={id}><input id={id} type="checkbox" checked={Boolean(value)} disabled={disabled} onChange={event => onChange(event.target.checked)}/><span>{field.label}{field.required && " *"}</span></label>;
  if (field.type === "select") return <label className="encounter-field" htmlFor={id}>{field.label}{field.required && " *"}<select id={id} value={valueForInput(value)} disabled={disabled} onChange={event => onChange(event.target.value)}><option value="">Odaberite</option>{(field.options ?? []).map(option => { const item = typeof option === "string" ? { value: option, label: option } : option; return <option key={item.value} value={item.value}>{item.label}</option>; })}</select>{field.help_text && <small>{field.help_text}</small>}</label>;
  if (["short_text", "integer", "decimal", "date", "time"].includes(field.type)) return <label className="encounter-field" htmlFor={id}>{field.label}{field.required && " *"}<input id={id} type={field.type === "integer" || field.type === "decimal" ? "number" : field.type === "date" || field.type === "time" ? field.type : "text"} value={valueForInput(value)} disabled={disabled} onChange={event => onChange(field.type === "integer" || field.type === "decimal" ? event.target.value : event.target.value)}/>{field.help_text && <small>{field.help_text}</small>}</label>;
  const listValue = ["multi_select", "diagnosis_list", "medication_list", "procedure_intervention_list", "specimen_list", "anatomical_site"].includes(field.type);
  return <label className="encounter-field" htmlFor={id}>{field.label}{field.required && " *"}<textarea id={id} rows={field.type === "long_text" || field.type === "rich_text_limited" ? 4 : 2} value={valueForInput(value)} disabled={disabled} onChange={event => onChange(listValue ? event.target.value.split(",").map(item => item.trim()).filter(Boolean) : event.target.value)}/>{listValue && <small>Vrijednosti odvojite zarezom.</small>}{field.help_text && <small>{field.help_text}</small>}</label>;
}


export function ClinicalActivityForm({ journeyId, activity, serviceName, onChanged }: { journeyId: number; activity: JourneyActivity; serviceName: string; onChanged: () => Promise<void> }) {
  const [form, setForm] = useState<ClinicalFormInstance | null>(null);
  const [data, setData] = useState<Record<string, unknown>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const base = `/api/patient-journeys/${journeyId}/activities/${activity.id}`;
  useEffect(() => { setForm(null); setData({}); setError(""); }, [activity.id]);

  async function run(action: () => Promise<void>) {
    setBusy(true); setError("");
    try { await action(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Radnja nije spremljena."); }
    finally { setBusy(false); }
  }
  async function resolve() { await run(async () => { const item = await api<ClinicalFormInstance>(`${base}/form/resolve`, { method: "POST" }); setForm(item); setData(item.data_json); await onChanged(); }); }
  async function save() { await run(async () => { const item = await api<ClinicalFormInstance>(`${base}/form`, { method: "PATCH", body: JSON.stringify({ data }) }); setForm(item); }); }
  async function completeForm() { if (!window.confirm("Dovršiti klinički obrazac?")) return; await run(async () => { const item = await api<ClinicalFormInstance>(`${base}/form/complete`, { method: "POST" }); setForm(item); }); }
  async function sign() { if (!window.confirm("Potpisati klinički nalaz? Nakon potpisa izmjene zahtijevaju ispravak.")) return; await run(async () => { const item = await api<ClinicalFormInstance>(`${base}/form/sign`, { method: "POST" }); setForm(item); }); }
  async function start() { await run(async () => { if (activity.status === "planned") await api(`${base}/transition`, { method: "POST", body: JSON.stringify({ target_status: "ready" }) }); await api(`${base}/transition`, { method: "POST", body: JSON.stringify({ target_status: "in_progress" }) }); await onChanged(); }); }
  async function completeActivity() { if (!window.confirm("Dovršiti ovu aktivnost?")) return; await run(async () => { await api(`${base}/transition`, { method: "POST", body: JSON.stringify({ target_status: "completed" }) }); await onChanged(); }); }

  const locked = form ? ["completed", "signed", "amended", "void"].includes(form.status) : false;
  return <section className="journey-panel clinical-activity-form">
    <header><div><span className="eyebrow">Aktivnost {activity.sequence}</span><h2>{serviceName}</h2><p>{activityClockTime(activity.planned_start)}–{activityClockTime(activity.planned_end)}</p></div><span className={`activity-status ${activity.status}`}>{activity.status === "in_progress" ? "U tijeku" : activity.status === "completed" ? "Završeno" : "Planirano"}</span></header>
    {error && <p className="inline-error" role="alert">{error}</p>}
    {!form && <div className="clinical-form-empty"><p>Otvorite kontrolirani obrazac vezan uz ovu uslugu. Ako vezanje nije postavljeno, sustav će jasno zaustaviti rad.</p><button type="button" className="primary" disabled={busy} onClick={resolve}>Otvori obrazac</button></div>}
    {form && <><div className="clinical-form-meta"><span>Verzija {form.form_version.version}</span><span>{form.status === "in_progress" ? "Radna verzija" : form.status === "completed" ? "Dovršeno" : form.status === "signed" ? "Potpisano" : "Skica"}</span></div>{form.form_version.sections_json.map(section => <fieldset key={section.section_key} disabled={busy || locked}><legend>{section.title ?? "Klinički nalaz"}</legend><div className="clinical-form-grid">{section.fields.map(field => <FormField key={field.field_key} field={field} value={data[field.field_key]} disabled={busy || locked} onChange={value => setData(current => ({ ...current, [field.field_key]: value }))}/>)}</div></fieldset>)}<div className="clinical-form-actions">{!locked && <button type="button" disabled={busy} onClick={save}><Save size={15}/>Spremi</button>}{["draft", "in_progress"].includes(form.status) && <button type="button" className="primary" disabled={busy} onClick={completeForm}><Check size={15}/>Dovrši obrazac</button>}{form.status === "completed" && <button type="button" className="primary" disabled={busy} onClick={sign}><FileSignature size={15}/>Potpiši nalaz</button>}{["planned", "ready"].includes(activity.status) && <button type="button" disabled={busy || form.status === "draft"} onClick={start}><Play size={15}/>Započni aktivnost</button>}{activity.status === "in_progress" && ["completed", "signed"].includes(form.status) && <button type="button" className="primary" disabled={busy} onClick={completeActivity}><Check size={15}/>Dovrši aktivnost</button>}</div></>}
  </section>;
}
