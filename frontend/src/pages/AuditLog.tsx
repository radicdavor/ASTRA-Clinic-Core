import { useMemo, useState } from "react";
import { DataTable } from "../components/DataTable";
import { DateInput } from "../components/DateInput";
import {
  EmptyState,
  ListFilterBar,
  ListPageHeader,
  ProgressiveDetailPanel,
  StatusSummary,
} from "../components/OperationalList";
import { useApi } from "../hooks/useApi";
import { AuditLog as AuditLogType } from "../types";
import { formatDateTime } from "../utils/date";

const actionLabels: Record<string, string> = {
  patient_viewed: "Otvoren karton pacijenta",
  clinical_document_viewed: "Dokument otvoren",
  clinical_document_reviewed: "Dokument pregledan",
  invoice_issued: "Račun izdan",
  payment_recorded: "Uplata evidentirana",
  session_revoked: "Sesija opozvana",
  access_denied: "Pristup odbijen",
  "audit_log.viewed": "Otvorena evidencija aktivnosti",
  create: "Zapis kreiran",
  update: "Zapis izmijenjen",
  delete: "Zapis obrisan",
  issue: "Račun izdan",
  payment: "Uplata evidentirana",
  login: "Korisnik prijavljen",
};

const entityLabels: Record<string, string> = {
  Patient: "Pacijent",
  Appointment: "Termin",
  ClinicalDocument: "Klinički dokument",
  ClinicalEpisode: "Klinička epizoda",
  PatientJourney: "Tijek pacijenta",
  Invoice: "Račun",
  PaymentTransaction: "Uplata",
  AuditLog: "Evidencija aktivnosti",
  UserSession: "Korisnička sesija",
  user_session: "Korisnička sesija",
};

function readableIdentifier(value: string) {
  return value
    .replace(/[._-]+/g, " ")
    .replace(/\b\p{L}/gu, (letter) => letter.toLocaleUpperCase("hr"));
}

export function auditActionLabel(value: string) {
  return actionLabels[value] ?? readableIdentifier(value);
}

export function auditEntityLabel(value: string) {
  return entityLabels[value] ?? readableIdentifier(value);
}

export function auditCategory(event: AuditLogType) {
  const value = `${event.action} ${event.entity_type}`.toLocaleLowerCase("en");
  if (/(invoice|payment|billing|fiscal)/.test(value)) return "Financije";
  if (/(auth|session|access|api.?key)/.test(value)) return "Sigurnost i pristup";
  if (/(clinical|document|report|encounter|patient|episode|journey)/.test(value)) return "Klinički rad";
  return "Operativni rad";
}

function actorLabel(event: AuditLogType) {
  if (event.actor_name) return event.actor_name;
  if (event.actor_type === "api_key") return "API servis";
  if (event.actor_type === "system") return "Sustav";
  return "Korisnik";
}

function resultStatus(event: AuditLogType) {
  return event.result === "denied"
    ? { label: "Odbijeno", tone: "danger" as const }
    : { label: "Uspjelo", tone: "success" as const };
}

export function AuditLog() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [actorId, setActorId] = useState("");
  const [category, setCategory] = useState("");
  const [result, setResult] = useState("");
  const [entityType, setEntityType] = useState("");
  const [requestId, setRequestId] = useState("");
  const [selected, setSelected] = useState<AuditLogType | null>(null);

  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    if (actorId) params.set("actor_user_id", actorId);
    return `/api/audit-log${params.size ? `?${params.toString()}` : ""}`;
  }, [actorId, dateFrom, dateTo]);
  const events = useApi<AuditLogType[]>(query, []);
  const actors = useMemo(() => {
    const values = new Map<number, string>();
    events.data.forEach((event) => {
      if (event.actor_user_id && event.actor_name) values.set(event.actor_user_id, event.actor_name);
    });
    return [...values.entries()].sort((left, right) => left[1].localeCompare(right[1], "hr"));
  }, [events.data]);
  const entityTypes = useMemo(() => [...new Set(events.data.map((event) => event.entity_type))].sort(), [events.data]);
  const visibleEvents = useMemo(() => events.data.filter((event) => (
    (!category || auditCategory(event) === category)
    && (!result || event.result === result)
    && (!entityType || event.entity_type === entityType)
    && (!requestId.trim() || event.request_id?.toLocaleLowerCase("en").includes(requestId.trim().toLocaleLowerCase("en")))
  )), [category, entityType, events.data, requestId, result]);
  const hasFilters = Boolean(dateFrom || dateTo || actorId || category || result || entityType || requestId);
  const advancedFilterCount = [entityType, requestId].filter(Boolean).length;

  function clearFilters() {
    setDateFrom("");
    setDateTo("");
    setActorId("");
    setCategory("");
    setResult("");
    setEntityType("");
    setRequestId("");
  }

  return (
    <section className="page operational-list-page">
      <ListPageHeader
        eyebrow="Operativni audit"
        title="Evidencija aktivnosti"
        description="Pregled radnji u aktivnoj klinici bez prikazivanja kliničkog sadržaja ili tehničkih tajni."
      />
      <p className="audit-scope-label">Prikaz: <strong>{events.data[0]?.scope_label ?? "aktivna klinika"}</strong></p>
      <ListFilterBar
        activeFilterCount={advancedFilterCount}
        showClear={hasFilters}
        onClear={clearFilters}
        advanced={(
          <>
            <label>Objekt
              <select value={entityType} onChange={(event) => setEntityType(event.target.value)}>
                <option value="">Svi objekti</option>
                {entityTypes.map((value) => <option key={value} value={value}>{auditEntityLabel(value)}</option>)}
              </select>
            </label>
            <label>Request ID<input value={requestId} onChange={(event) => setRequestId(event.target.value)} /></label>
          </>
        )}
      >
        <label>Od datuma<DateInput value={dateFrom} onChange={setDateFrom} /></label>
        <label>Do datuma<DateInput value={dateTo} onChange={setDateTo} /></label>
        <label>Korisnik
          <select value={actorId} onChange={(event) => setActorId(event.target.value)}>
            <option value="">Svi korisnici</option>
            {actors.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
          </select>
        </label>
        <label>Kategorija
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">Sve kategorije</option>
            <option>Klinički rad</option><option>Financije</option><option>Operativni rad</option><option>Sigurnost i pristup</option>
          </select>
        </label>
        <label>Rezultat
          <select value={result} onChange={(event) => setResult(event.target.value)}>
            <option value="">Svi rezultati</option>
            <option value="success">Uspjelo</option>
            <option value="denied">Odbijeno</option>
          </select>
        </label>
      </ListFilterBar>

      <div aria-live="polite">
        {events.loading ? (
          <p className="operational-list-loading">Učitavanje evidencije…</p>
        ) : events.status === 403 ? (
          <EmptyState kind="forbidden" description="Vaša uloga nema pristup ovoj evidenciji aktivnosti." />
        ) : events.error ? (
          <EmptyState kind="unavailable" description={events.error} />
        ) : visibleEvents.length === 0 ? (
          <EmptyState kind={hasFilters ? "filtered" : "empty"} title={hasFilters ? undefined : "Nema događaja"} />
        ) : (
          <DataTable ariaLabel="Evidencija aktivnosti" rows={visibleEvents} columns={[
            { header: "Vrijeme", render: (event) => formatDateTime(event.created_at) },
            { header: "Korisnik", render: (event) => actorLabel(event) },
            { header: "Radnja", render: (event) => auditActionLabel(event.action) },
            { header: "Objekt", render: (event) => <button type="button" className="audit-object-action" onClick={() => setSelected(event)}>{auditEntityLabel(event.entity_type)}<small>Detalji</small></button> },
            { header: "Scope", render: (event) => event.scope_label ?? "Aktivna klinika" },
            { header: "Rezultat", render: (event) => <StatusSummary {...resultStatus(event)} /> },
          ]} />
        )}
      </div>

      <ProgressiveDetailPanel open={selected !== null} title="Tehnički detalj događaja" onClose={() => setSelected(null)}>
        {selected && <dl className="audit-detail-list">
          <div><dt>Tehnički tip događaja</dt><dd>{selected.action}</dd></div>
          <div><dt>Objekt</dt><dd>{selected.entity_type}{selected.entity_id ? ` #${selected.entity_id}` : ""}</dd></div>
          <div><dt>Request ID</dt><dd>{selected.request_id ?? "Nije zabilježen"}</dd></div>
          <div><dt>Reason code</dt><dd>{selected.reason_code ?? "Nije zabilježen"}</dd></div>
          <div><dt>Promijenjena polja</dt><dd>{selected.changed_fields?.join(", ") || "Nema zabilježenih naziva polja"}</dd></div>
          <div><dt>Clinic provenance</dt><dd>{selected.scope_label ?? "Aktivna klinika"}{selected.clinic_id ? ` (#${selected.clinic_id})` : ""}</dd></div>
          <div><dt>Institution provenance</dt><dd>{selected.institution_id ? `#${selected.institution_id}` : "Nije zabilježeno"}</dd></div>
          <div><dt>Sigurnosna klasifikacija</dt><dd>{auditCategory(selected)}</dd></div>
        </dl>}
      </ProgressiveDetailPanel>
    </section>
  );
}
