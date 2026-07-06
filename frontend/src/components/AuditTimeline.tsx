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
  complete_with_consumption: "Zavrsetak s potrosnjom",
  close: "Zatvoreno",
  link_episode: "Povezano s epizodom",
  unlink_episode: "Odvojeno od epizode",
  ai_plan_generated: "AI prijedlog plana",
  ai_plan_edited: "Plan uredjen",
  ai_plan_rejected: "AI prijedlog odbijen",
  ai_plan_confirmed: "Plan potvrdjen",
  clinical_plan_archived: "Plan arhiviran",
  upload: "Dokument uploadan",
  ai_document_extracted: "AI prijedlog izdvojen",
  ai_document_extraction_edited: "AI prijedlog uredjen",
  clinical_document_reviewed: "Dokument pregledan",
  ai_document_summary_rejected: "AI sazetak odbijen",
  patient_summary_draft_generated: "AI draft sazetka",
  patient_summary_edited: "Sazetak uredjen",
  patient_summary_reviewed: "Sazetak potvrdjen",
  mark_arrived: "Pacijent pristigao",
  identity_verified: "Identitet provjeren",
  reception_patient_updated: "Podaci dopunjeni na prijemu"
};

const entityLabels: Record<string, string> = {
  Patient: "Pacijent",
  Appointment: "Termin",
  Invoice: "Racun",
  Service: "Usluga",
  InventoryItem: "Artikl",
  StockMovement: "Kretanje zalihe",
  PurchaseOrder: "Narudzbenica",
  ApiKey: "API kljuc",
  ClinicalEpisode: "Klinicka epizoda",
  ClinicalPlan: "Klinicki plan",
  ClinicalDocument: "Klinicki dokument",
  PatientClinicalSummary: "Sazetak pacijenta"
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
  if (log.entity_type === "ClinicalEpisode") return `/episodes/${log.entity_id}`;
  if (log.entity_type === "ClinicalDocument") return `/clinical-documents/${log.entity_id}`;
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
