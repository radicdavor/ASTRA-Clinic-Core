import { AuditLog } from "../types";

const actionLabels: Record<string, string> = {
  create: "Kreirano",
  update: "Azurirano",
  delete: "Obrisano",
  login: "Prijava",
  issue: "Izdano"
};

function actorLabel(log: AuditLog) {
  if (log.actor_type === "api_key") return `API kljuc${log.actor_api_key_id ? ` #${log.actor_api_key_id}` : ""}`;
  if (log.actor_user_id) return `Korisnik #${log.actor_user_id}`;
  return log.actor_type ?? "Sustav";
}

function JsonDetails({ title, value }: { title: string; value?: Record<string, unknown> | null }) {
  if (!value || Object.keys(value).length === 0) return null;
  return (
    <details className="json-details">
      <summary>{title}</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}

export function AuditTimeline({ logs }: { logs: AuditLog[] }) {
  return (
    <div className="timeline">
      {logs.map((log) => (
        <article key={log.id}>
          <strong>{actionLabels[log.action] ?? log.action} {log.entity_type}{log.entity_id ? ` #${log.entity_id}` : ""}</strong>
          <span>{new Date(log.created_at).toLocaleString()} / {actorLabel(log)}</span>
          <p>{log.summary ?? "-"}{log.request_id ? ` (${log.request_id})` : ""}</p>
          <JsonDetails title="Prije" value={log.before_json} />
          <JsonDetails title="Poslije" value={log.after_json} />
        </article>
      ))}
      {logs.length === 0 && <p>Nema audit zapisa.</p>}
    </div>
  );
}
