import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { HelpHint } from "../components/HelpHint";
import { DateInput } from "../components/DateInput";
import { useApi } from "../hooks/useApi";
import { Patient, Provider, WorkflowTask, WorkflowTemplate } from "../types";
import { formatDate } from "../utils/date";

const statusColumns = [
  ["open", "Otvoreno"], ["in_progress", "U tijeku"], ["waiting", "Ceka"], ["completed", "Dovrseno"]
] as const;

function dueLabel(task: WorkflowTask) {
  if (!task.due_date) return "Bez roka";
  const today = new Date().toISOString().slice(0, 10);
  if (task.status !== "completed" && task.due_date < today) return `Kasni · ${formatDate(task.due_date)}`;
  return formatDate(task.due_date);
}

export function WorkflowTasks() {
  const tasks = useApi<WorkflowTask[]>("/api/workflow-tasks", []);
  const templates = useApi<WorkflowTemplate[]>("/api/workflow-templates", []);
  const patients = useApi<Patient[]>("/api/patients", []);
  const providers = useApi<Provider[]>("/api/providers", []);
  const [showCreate, setShowCreate] = useState(false);
  const [filter, setFilter] = useState("");
  const [draft, setDraft] = useState({ title: "", description: "", patient_id: "", template_id: "", assignee_provider_id: "", responsible_role: "", priority: "routine", due_date: "" });

  const visible = useMemo(() => tasks.data.filter((task) => !filter || `${task.title} ${task.patient?.first_name} ${task.patient?.last_name}`.toLowerCase().includes(filter.toLowerCase())), [tasks.data, filter]);

  async function create(event: FormEvent) {
    event.preventDefault();
    const created = await api<WorkflowTask>("/api/workflow-tasks", { method: "POST", body: JSON.stringify({ ...draft, patient_id: Number(draft.patient_id), template_id: draft.template_id ? Number(draft.template_id) : null, assignee_provider_id: draft.assignee_provider_id ? Number(draft.assignee_provider_id) : null, due_date: draft.due_date || null }) });
    tasks.setData([created, ...tasks.data]);
    setDraft({ title: "", description: "", patient_id: "", template_id: "", assignee_provider_id: "", responsible_role: "", priority: "routine", due_date: "" });
    setShowCreate(false);
  }

  return (
    <div className="page workflow-page">
      <header className="page-header workflow-header">
        <div><span className="eyebrow">Operativni radni tok</span><h1>Zadaci</h1><p>Jasan pregled sljedeceg koraka, odgovornosti i roka. Zadatak nije klinicka odluka.</p></div>
        <ActionButton variant="create" onClick={() => setShowCreate(!showCreate)} helpTitle="Novi zadatak" help="Stvara operativni zadatak povezan s pacijentom. Vazne promjene ostaju u auditu.">Novi zadatak</ActionButton>
      </header>
      <div className="workflow-toolbar"><input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Pretrazi zadatak ili pacijenta" /><span>{visible.filter((task) => !["completed", "cancelled"].includes(task.status)).length} aktivnih</span></div>
      {showCreate && <form className="panel form-grid workflow-create" onSubmit={create}>
        <h2>Novi zadatak <HelpHint title="Operativni zadatak">Zadatak organizira rad. Ne postavlja dijagnozu, terapiju ni klinicki prioritet.</HelpHint></h2>
        <label>Naslov<input required value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} /></label>
        <label>Pacijent<select required value={draft.patient_id} onChange={(event) => setDraft({ ...draft, patient_id: event.target.value })}><option value="">Odaberi pacijenta</option>{patients.data.map((patient) => <option key={patient.id} value={patient.id}>{patient.first_name} {patient.last_name}</option>)}</select></label>
        <label>Predlozak<select value={draft.template_id} onChange={(event) => { const template = templates.data.find((item) => item.id === Number(event.target.value)); setDraft({ ...draft, template_id: event.target.value, priority: template?.default_priority ?? draft.priority }); }}><option value="">Bez predloska</option>{templates.data.map((template) => <option key={template.id} value={template.id}>{template.name}</option>)}</select></label>
        <label>Odgovorna osoba<select value={draft.assignee_provider_id} onChange={(event) => setDraft({ ...draft, assignee_provider_id: event.target.value })}><option value="">Nije dodijeljeno</option>{providers.data.map((provider) => <option key={provider.id} value={provider.id}>{provider.full_name}</option>)}</select></label>
        <label>Odgovorna uloga<input value={draft.responsible_role} onChange={(event) => setDraft({ ...draft, responsible_role: event.target.value })} placeholder="npr. nurse" /></label>
        <label>Prioritet<select value={draft.priority} onChange={(event) => setDraft({ ...draft, priority: event.target.value })}><option value="routine">Rutinski</option><option value="important">Vazno</option><option value="urgent">Hitno operativno</option></select></label>
        <label>Rok<DateInput value={draft.due_date} onChange={(value) => setDraft({ ...draft, due_date: value })} /></label>
        <label className="wide-field">Opis<textarea rows={3} value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} /></label>
        <ActionButton type="submit" variant="create" helpTitle="Spremi zadatak" help="Sprema zadatak i auditira stvaranje.">Spremi zadatak</ActionButton>
      </form>}
      <section className="workflow-board" aria-label="Radna traka zadataka">
        {statusColumns.map(([status, label]) => <div className={`workflow-lane lane-${status}`} key={status}><header><h2>{label}</h2><span>{visible.filter((task) => task.status === status).length}</span></header><div>
          {visible.filter((task) => task.status === status).map((task) => <Link className={`workflow-card priority-${task.priority}`} to={`/workflow/${task.id}`} key={task.id}>
            <span className="workflow-card-priority">{task.priority === "urgent" ? "Hitno" : task.priority === "important" ? "Vazno" : "Rutinski"}</span>
            <strong>{task.title}</strong><p>{task.patient ? `${task.patient.first_name} ${task.patient.last_name}` : `Pacijent #${task.patient_id}`}</p>
            <footer><span>{task.provider?.full_name ?? task.responsible_role ?? "Nije dodijeljeno"}</span><span className={dueLabel(task).startsWith("Kasni") ? "overdue" : ""}>{dueLabel(task)}</span></footer>
          </Link>)}
          {visible.every((task) => task.status !== status) && <p className="workflow-empty">Nema zadataka.</p>}
        </div></div>)}
      </section>
    </div>
  );
}
