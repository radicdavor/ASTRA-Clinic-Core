import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { AuditTimeline } from "../components/AuditTimeline";
import { HelpHint } from "../components/HelpHint";
import { DateInput } from "../components/DateInput";
import { useApi } from "../hooks/useApi";
import { AuditLog, Provider, WorkflowTask } from "../types";

export function WorkflowTaskDetail() {
  const { id } = useParams();
  const task = useApi<WorkflowTask | null>(`/api/workflow-tasks/${id}`, null);
  const providers = useApi<Provider[]>("/api/providers", []);
  const audit = useApi<AuditLog[]>(`/api/audit-log?entity_type=WorkflowTask&entity_id=${id}`, []);
  const [draft, setDraft] = useState({ title: "", description: "", status: "open", priority: "routine", due_date: "", assignee_provider_id: "", responsible_role: "" });
  useEffect(() => { if (task.data) setDraft({ title: task.data.title, description: task.data.description ?? "", status: task.data.status, priority: task.data.priority, due_date: task.data.due_date ?? "", assignee_provider_id: task.data.assignee_provider_id?.toString() ?? "", responsible_role: task.data.responsible_role ?? "" }); }, [task.data]);
  if (!task.data) return <div className="page"><p>{task.loading ? "Ucitavanje..." : task.error ?? "Zadatak nije pronaden."}</p></div>;

  async function refresh(updated: WorkflowTask) { task.setData(updated); audit.setData(await api<AuditLog[]>(`/api/audit-log?entity_type=WorkflowTask&entity_id=${id}`)); }
  async function save(event: FormEvent) { event.preventDefault(); await refresh(await api<WorkflowTask>(`/api/workflow-tasks/${id}`, { method: "PATCH", body: JSON.stringify({ ...draft, due_date: draft.due_date || null, assignee_provider_id: draft.assignee_provider_id ? Number(draft.assignee_provider_id) : null }) })); }
  async function toggle(itemId: number) { await refresh(await api<WorkflowTask>(`/api/workflow-tasks/${id}/checklist/${itemId}/toggle`, { method: "POST" })); }
  const complete = task.data.checklist.filter((item) => item.completed).length;
  return <div className="page workflow-detail">
    <header className="page-header"><div><span className="eyebrow">Zadatak #{task.data.id}</span><h1>{task.data.title}</h1><p>{task.data.patient ? <Link to={`/patients/${task.data.patient.id}`}>{task.data.patient.first_name} {task.data.patient.last_name}</Link> : `Pacijent #${task.data.patient_id}`} {task.data.episode && <>· <Link to={`/episodes/${task.data.episode.id}`}>{task.data.episode.title}</Link></>}</p></div><span className={`workflow-status status-${task.data.status}`}>{task.data.status}</span></header>
    <div className="workflow-detail-grid"><main>
      <section className="panel"><h2>Checklista <HelpHint title="Uvjet zavrsetka">Sve stavke moraju biti dovrsene prije zatvaranja zadatka.</HelpHint></h2><div className="workflow-progress"><span style={{ width: `${task.data.checklist.length ? complete / task.data.checklist.length * 100 : 100}%` }} /></div><p>{complete} od {task.data.checklist.length} dovrseno</p><div className="checklist">{task.data.checklist.map((item) => <label key={item.id} className={item.completed ? "done" : ""}><input type="checkbox" checked={item.completed} onChange={() => toggle(item.id)} /> <span>{item.label}</span></label>)}{task.data.checklist.length === 0 && <p>Zadatak nema checklistu i moze se zavrsiti promjenom statusa.</p>}</div></section>
      <section className="panel"><h2>Audit timeline</h2><AuditTimeline logs={audit.data} /></section>
    </main><aside className="panel"><h2>Odgovornost i status</h2><form className="stack-form" onSubmit={save}>
      <label>Naslov<input value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} /></label>
      <label>Status<select value={draft.status} onChange={(event) => setDraft({ ...draft, status: event.target.value })}><option value="open">Otvoreno</option><option value="in_progress">U tijeku</option><option value="waiting">Ceka</option><option value="completed">Dovrseno</option><option value="cancelled">Otkazano</option></select></label>
      <label>Prioritet<select value={draft.priority} onChange={(event) => setDraft({ ...draft, priority: event.target.value })}><option value="routine">Rutinski</option><option value="important">Vazno</option><option value="urgent">Hitno operativno</option></select></label>
      <label>Odgovorna osoba<select value={draft.assignee_provider_id} onChange={(event) => setDraft({ ...draft, assignee_provider_id: event.target.value })}><option value="">Nije dodijeljeno</option>{providers.data.map((provider) => <option key={provider.id} value={provider.id}>{provider.full_name}</option>)}</select></label>
      <label>Odgovorna uloga<input value={draft.responsible_role} onChange={(event) => setDraft({ ...draft, responsible_role: event.target.value })} /></label>
      <label>Rok<DateInput value={draft.due_date} onChange={(value) => setDraft({ ...draft, due_date: value })} /></label>
      <label>Opis<textarea rows={5} value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} /></label>
      <ActionButton type="submit" variant={draft.status === "completed" ? "danger" : "update"} confirmMessage={draft.status === "completed" ? "Zavrsiti ovaj zadatak? Promjena ce biti auditirana." : undefined} helpTitle="Spremi promjene" help="Mijenja odgovornost, rok ili status i zapisuje audit.">Spremi promjene</ActionButton>
    </form></aside></div>
  </div>;
}
