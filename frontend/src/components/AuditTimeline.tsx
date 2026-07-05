import { AuditLog } from "../types";

export function AuditTimeline({ logs }: { logs: AuditLog[] }) {
  return (
    <div className="timeline">
      {logs.map((log) => (
        <div key={log.id}>
          <strong>{log.action} {log.entity_type}</strong>
          <span>{new Date(log.created_at).toLocaleString()} / {log.actor_type ?? "user"}</span>
          <p>{log.summary ?? "-"}{log.request_id ? ` (${log.request_id})` : ""}</p>
        </div>
      ))}
      {logs.length === 0 && <p>Nema audit zapisa.</p>}
    </div>
  );
}
