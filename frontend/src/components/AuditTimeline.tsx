import { Link } from "react-router-dom";
import { AuditLog } from "../types";
import { formatDateTime } from "../utils/date";

const actionLabels: Record<string, string> = {
  create: "Kreirano",
  update: "Azurirano",
  delete: "Obrisano",
  login: "Prijava",
  issue: "Izdano",
  payment: "Uplata",
  stock_movement: "Kretanje zalihe",
  complete_with_consumption: "Zavrsetak s potrosnjom"
};

const entityLabels: Record<string, string> = {
  Patient: "Pacijent",
  Appointment: "Termin",
  Invoice: "Racun",
  Service: "Usluga",
  InventoryItem: "Artikl",
  StockMovement: "Kretanje zalihe",
  PurchaseOrder: "Narudzbenica",
  ApiKey: "API kljuc"
};

function actorLabel(log: AuditLog) {
  if (log.actor_type === "api_key") return `API kljuc${log.actor_api_key_id ? ` #${log.actor_api_key_id}` : ""}`;
  if (log.actor_user_id) return `Korisnik #${log.actor_user_id}`;
  return log.actor_type ?? "Sustav";
}

function entityRoute(log: AuditLog) {
  if (!log.entity_id) return "";
  if (log.entity_type === "Patient") return `/patients/${log.entity_id}`;
  if (log.entity_type === "Appointment") return `/appointments/${log.entity_id}`;
  if (log.entity_type === "Invoice") return `/invoices?invoice=${log.entity_id}`;
  return "";
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
          <strong>
            {actionLabels[log.action] ?? log.action} {entityRoute(log) ? <Link to={entityRoute(log)}>{entityLabels[log.entity_type] ?? log.entity_type}{log.entity_id ? ` #${log.entity_id}` : ""}</Link> : `${entityLabels[log.entity_type] ?? log.entity_type}${log.entity_id ? ` #${log.entity_id}` : ""}`}
          </strong>
          <span>{formatDateTime(log.created_at)} / {actorLabel(log)}</span>
          <p>{log.summary ?? "-"}{log.request_id ? <> <code>{log.request_id}</code></> : null}</p>
          <JsonDetails title="Prije" value={log.before_json} />
          <JsonDetails title="Poslije" value={log.after_json} />
        </article>
      ))}
      {logs.length === 0 && <p>Nema audit zapisa.</p>}
    </div>
  );
}
