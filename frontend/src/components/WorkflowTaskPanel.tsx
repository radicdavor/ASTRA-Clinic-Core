import { Link } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { WorkflowTask } from "../types";

export function WorkflowTaskPanel({ patientId, episodeId }: { patientId?: number; episodeId?: number }) {
  const path = episodeId ? `/api/episodes/${episodeId}/workflow-tasks` : `/api/patients/${patientId}/workflow-tasks`;
  const tasks = useApi<WorkflowTask[]>(path, []);
  const active = tasks.data.filter((task) => !["completed", "cancelled"].includes(task.status));
  return <section className="panel workflow-context-panel">
    <header><div><span className="eyebrow">Sto slijedi</span><h2>Operativni zadaci</h2></div><Link to="/workflow">Otvori radnu traku</Link></header>
    {active.map((task) => <Link to={`/workflow/${task.id}`} key={task.id} className="workflow-context-row"><span className={`priority-dot priority-${task.priority}`} /><strong>{task.title}</strong><span>{task.provider?.full_name ?? task.responsible_role ?? "Nije dodijeljeno"}</span><time>{task.due_date ?? "Bez roka"}</time></Link>)}
    {active.length === 0 && <p>Nema otvorenih operativnih zadataka.</p>}
  </section>;
}
