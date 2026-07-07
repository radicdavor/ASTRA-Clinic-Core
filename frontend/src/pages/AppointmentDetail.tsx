import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, getClinicalReadinessSnapshotHistory, notifyUser } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { AuditTimeline } from "../components/AuditTimeline";
import { DataTable } from "../components/DataTable";
import { StatusBadge } from "../components/StatusBadge";
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader";
import { WorkspaceLayout } from "../components/workspace/WorkspaceLayout";
import { WorkspaceSection } from "../components/workspace/WorkspaceSection";
import { useApi } from "../hooks/useApi";
import { Appointment, AuditLog, ClinicalReadinessPreview, ClinicalReadinessSnapshotHistoryResponse, Invoice, StockMovement } from "../types";
import { formatDate, formatDateTime } from "../utils/date";
import { formatPatientIdentity, formatPatientName } from "../utils/patientIdentity";

export function AppointmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const appointment = useApi<Appointment | null>(`/api/appointments/${id}`, null);
  const invoices = useApi<Invoice[]>("/api/invoices", []);
  const movements = useApi<StockMovement[]>("/api/inventory/stock-movements", []);
  const audit = useApi<AuditLog[]>(`/api/audit-log?entity_type=Appointment&entity_id=${id}`, []);
  const clinicalReadiness = useApi<ClinicalReadinessPreview | null>(`/api/appointments/${id}/clinical-readiness-preview`, null);
  const [materials, setMaterials] = useState<any[]>([]);
  const [quantities, setQuantities] = useState<Record<number, string>>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [snapshotHistory, setSnapshotHistory] = useState<ClinicalReadinessSnapshotHistoryResponse | null>(null);
  const [snapshotHistoryLoading, setSnapshotHistoryLoading] = useState(true);
  const [snapshotHistoryError, setSnapshotHistoryError] = useState(false);

  const relatedInvoice = useMemo(() => invoices.data.find((invoice) => invoice.appointment_id === Number(id)), [invoices.data, id]);
  const relatedMovements = useMemo(() => movements.data.filter((movement) => movement.related_appointment_id === Number(id)), [movements.data, id]);
  const terminalStatus = appointment.data ? ["completed", "cancelled"].includes(appointment.data.status) : false;
  const snapshotHistoryItems = useMemo(
    () => [...(snapshotHistory?.snapshots ?? [])].sort((left, right) => right.created_at.localeCompare(left.created_at)),
    [snapshotHistory]
  );

  useEffect(() => {
    const appointmentId = Number(id);
    if (!appointmentId) return;
    let active = true;
    setSnapshotHistoryLoading(true);
    setSnapshotHistoryError(false);
    getClinicalReadinessSnapshotHistory(appointmentId)
      .then((response) => {
        if (active) setSnapshotHistory(response);
      })
      .catch(() => {
        if (active) {
          setSnapshotHistory(null);
          setSnapshotHistoryError(true);
        }
      })
      .finally(() => {
        if (active) setSnapshotHistoryLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id]);

  async function loadMaterials() {
    if (!appointment.data) return;
    const suggestions = await api<any[]>(`/api/appointments/${appointment.data.id}/suggest-material-consumption`);
    const next: Record<number, string> = {};
    suggestions.forEach((entry) => {
      next[entry.item.id] = entry.auto_consumable ? String(entry.quantity) : "";
    });
    setMaterials(suggestions);
    setQuantities(next);
  }

  const missingRequiredVariable = materials.some((entry) => entry.requires_user_quantity && (!quantities[entry.item.id] || Number(quantities[entry.item.id]) <= 0));
  const exceedsStock = materials.some((entry) => Number(quantities[entry.item.id] || 0) > Number(entry.available_stock || 0));
  const belowReorderAfterUse = materials.some((entry) => {
    const requested = Number(quantities[entry.item.id] || 0);
    const remaining = Number(entry.available_stock || 0) - requested;
    return requested > 0 && entry.item.reorder_point && remaining <= Number(entry.item.reorder_point);
  });

  function materialLabel(entry: any) {
    if (!entry.required) return "opcionalno";
    return entry.requires_user_quantity ? "obavezno varijabilno" : "obavezno fiksno";
  }

  function snapshotSafetyText(text?: string | null) {
    if (!text) return "Snapshot history prikazuje spremljene preview zapise. Snapshot nije odluka da se postupak smije provesti.";
    return text
      .replace(new RegExp(["Outcome", "Evidence"].join(" "), "g"), "formalni dokaz ishoda")
      .replace(new RegExp(["clinical", "approval"].join(" "), "g"), "klinicka odluka")
      .replace(new RegExp(["readiness", "clearance"].join(" "), "g"), "klinicka odluka");
  }

  async function completeWithMaterials() {
    if (!appointment.data) return;
    if (missingRequiredVariable || exceedsStock || terminalStatus) {
      const message = missingRequiredVariable
        ? "Obavezni varijabilni materijal mora imati kolicinu."
        : exceedsStock
          ? "Kolicina prelazi dostupnu zalihu."
          : "Termin je vec zavrsen ili otkazan.";
      setError(message);
      notifyUser(message, "error");
      return;
    }
    setError("");
    try {
      const lines = materials
        .map((entry) => ({ inventory_item_id: entry.item.id, quantity: quantities[entry.item.id], reason: "Potrosnja po terminu" }))
        .filter((line) => line.quantity && Number(line.quantity) > 0);
      const updated = await api<Appointment>(`/api/appointments/${appointment.data.id}/complete-with-consumption`, { method: "POST", body: JSON.stringify({ lines }) });
      appointment.setData(updated);
      movements.setData(await api<StockMovement[]>("/api/inventory/stock-movements"));
      audit.setData(await api<AuditLog[]>(`/api/audit-log?entity_type=Appointment&entity_id=${appointment.data.id}`));
      setMessage("Termin je zavrsen.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Greska kod potrosnje materijala");
    }
  }

  async function createInvoice() {
    if (!appointment.data) return;
    const invoice = await api<Invoice>(`/api/appointments/${appointment.data.id}/draft-invoice`, { method: "POST" });
    navigate(`/invoices?invoice=${invoice.id}`);
  }

  if (!appointment.data) return <WorkspaceLayout><p>Ucitavanje termina...</p></WorkspaceLayout>;

  return (
    <WorkspaceLayout>
      <WorkspaceHeader
        title={appointment.data.patient ? <Link to={`/patients/${appointment.data.patient.id}`}>{formatPatientName(appointment.data.patient)}</Link> : `Pacijent ${appointment.data.patient_id}`}
        subtitle={<>{appointment.data.patient ? formatPatientIdentity(appointment.data.patient) : "Nema detalja pacijenta"} / {formatDate(appointment.data.date)} {appointment.data.start_time.slice(0, 5)} - {appointment.data.end_time.slice(0, 5)}</>}
        badge={<StatusBadge status={appointment.data.status} />}
      />
      {message && <p className="success-message">{message}</p>}
      {error && <p className="form-error">{error}</p>}

      <div className="detail-list">
        <p><span>Usluga</span><strong>{appointment.data.service?.name ?? appointment.data.service_id}</strong></p>
        <p><span>Lijecnik</span><strong>{appointment.data.provider?.full_name ?? appointment.data.provider_id}</strong></p>
        <p><span>Soba</span><strong>{appointment.data.room?.name ?? appointment.data.room_id}</strong></p>
        <p>
          <span>Klinicka epizoda</span>
          <strong>
            {appointment.data.episode ? <Link to={`/episodes/${appointment.data.episode.id}`}>{appointment.data.episode.title}</Link> : "Termin nije povezan s klinickom epizodom."}
          </strong>
        </p>
        <p><span>Napomena</span><strong>{appointment.data.notes ?? "-"}</strong></p>
      </div>
      {!appointment.data.episode && (
        <div className="duplicate-warning">
          <strong>Termin nije povezan s klinickom epizodom.</strong>
          <p>To nije blokada za v0.1-pilot, ali za klinicko pracenje preporucuje se povezati termin s epizodom pacijenta.</p>
        </div>
      )}

      <WorkspaceSection title="Klinicka spremnost - preview">
        <p className="helper-text">Read-only prikaz mogucih uvjeta za ovaj planirani klinicki cin. Ne donosi odluke i ne blokira postupak.</p>
        {clinicalReadiness.error && <p className="form-error">Clinical readiness preview trenutno nije dostupan.</p>}
        {clinicalReadiness.data ? (
          <div className="readiness-detail">
            <p><strong>PREVIEW</strong> / status: <StatusBadge status={clinicalReadiness.data.status} /></p>
            <p>{clinicalReadiness.data.summary}</p>
            <div className="detail-list">
              <p><span>Template</span><strong>{clinicalReadiness.data.template_label ?? "Nije vezan"}</strong></p>
              <p><span>Verzija</span><strong>{clinicalReadiness.data.template_version ?? "-"}</strong></p>
              <p><span>Binding</span><strong>{clinicalReadiness.data.template_binding_status.replace("_", " ")}</strong></p>
              <p><span>Snapshot</span><strong>{clinicalReadiness.data.snapshot_supported ? clinicalReadiness.data.snapshot_status : "nije implementiran"}</strong></p>
            </div>
            {clinicalReadiness.data.snapshot_warning && (
              <p className="helper-text">{clinicalReadiness.data.snapshot_warning}</p>
            )}
            {clinicalReadiness.data.template_version_warning && (
              <p className="helper-text">{clinicalReadiness.data.template_version_warning}</p>
            )}
            {clinicalReadiness.data.template_binding_warning && (
              <p className="helper-text">{clinicalReadiness.data.template_binding_warning} Ovo nije produkcijsko pravilo.</p>
            )}
            {clinicalReadiness.data.limitations.length > 0 && (
              <div>
                <strong>Ogranicenja</strong>
                <ul>
                  {clinicalReadiness.data.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
                </ul>
              </div>
            )}
            {clinicalReadiness.data.source_warnings.length > 0 && (
              <div>
                <strong>Upozorenja o izvorima</strong>
                <ul>
                  {clinicalReadiness.data.source_warnings.map((warning) => <li key={warning}>{warning}</li>)}
                </ul>
              </div>
            )}
            {clinicalReadiness.data.items.length === 0 ? (
              <p>Nema prikazanih stavki u ovom previewu.</p>
            ) : (
              <div className="timeline-list">
                {clinicalReadiness.data.items.map((item) => (
                  <article className="timeline-item" key={item.key}>
                    <strong>{item.label}</strong>
                    <small>{item.category} / {item.status} / {item.severity} / uloga: {item.responsible_role ?? "-"}</small>
                    <p>Izvor: {item.source_label ? `${item.source_label} (${item.source_type})` : item.source_type}</p>
                    {item.suggested_action && <p>{item.suggested_action}</p>}
                  </article>
                ))}
              </div>
            )}
          </div>
        ) : !clinicalReadiness.error ? (
          <p>Ucitavanje clinical readiness previewa...</p>
        ) : null}
      </WorkspaceSection>

      <WorkspaceSection title="Povijest snapshotova klinicke spremnosti">
        <p className="helper-text">Read-only prikaz spremljenih preview zapisa. Snapshot nije odluka da se postupak smije provesti.</p>
        {snapshotHistory?.warning && <p className="helper-text">{snapshotSafetyText(snapshotHistory.warning)}</p>}
        {snapshotHistoryError && <p className="form-error">Povijest snapshotova trenutno nije dostupna.</p>}
        {snapshotHistoryLoading ? (
          <p>Ucitavanje povijesti snapshotova...</p>
        ) : !snapshotHistoryError && snapshotHistoryItems.length === 0 ? (
          <p>Nema spremljenih snapshotova za ovaj termin.</p>
        ) : (
          <div className="timeline-list">
            {snapshotHistoryItems.map((snapshot) => (
              <article className="timeline-item" key={snapshot.id}>
                <strong>{formatDateTime(snapshot.created_at)}</strong>
                <small>
                  Korisnik {snapshot.created_by_user_id} / status: {snapshot.preview_status} / stavke: {snapshot.item_count} / ogranicenja: {snapshot.limitation_count} / upozorenja izvora: {snapshot.source_warning_count}
                </small>
                <div className="detail-list">
                  <p><span>Template</span><strong>{snapshot.template_label ?? snapshot.template_key ?? "Nije vezan"}</strong></p>
                  <p><span>Verzija</span><strong>{snapshot.template_version ?? "-"}</strong></p>
                  <p><span>Binding</span><strong>{snapshot.template_binding_status?.replace("_", " ") ?? "-"}</strong></p>
                  <p><span>Razlog</span><strong>{snapshot.snapshot_reason}</strong></p>
                  <p><span>Preview generiran</span><strong>{formatDateTime(snapshot.preview_generated_at)}</strong></p>
                  <p><span>Schema</span><strong>{snapshot.schema_version}</strong></p>
                  <p><span>Preview zapis</span><strong>{snapshot.is_preview_snapshot ? "da" : "ne"}</strong></p>
                  <p><span>Stanje zapisa</span><strong>{snapshot.superseded_by_snapshot_id ? `Zamijenjen snapshotom ${snapshot.superseded_by_snapshot_id}` : "Aktivan zapis povijesti"}</strong></p>
                </div>
                {snapshot.superseded_at && <p className="helper-text">Zamijenjen: {formatDateTime(snapshot.superseded_at)}. Razlog: {snapshot.superseded_reason ?? "-"}</p>}
                {snapshot.disclaimer && <p className="helper-text">{snapshotSafetyText(snapshot.disclaimer)}</p>}
              </article>
            ))}
          </div>
        )}
      </WorkspaceSection>

      <WorkspaceSection title="Materijali" actions={<button onClick={loadMaterials}>Ucitaj prijedlog</button>}>
        {materials.map((entry) => (
          <label className="material-row" key={entry.template_id}>
            <span>
              <strong>{entry.item.name}</strong>
              <small>{materialLabel(entry)} / jedinica {entry.item.unit_of_measure ?? "-"} / zadano {entry.quantity} / dostupno {entry.available_stock} / reorder {entry.item.reorder_point ?? "-"}</small>
            </span>
            <input type="number" min="0" step="0.01" value={quantities[entry.item.id] ?? ""} onChange={(event) => setQuantities({ ...quantities, [entry.item.id]: event.target.value })} />
          </label>
        ))}
        {missingRequiredVariable && <p className="form-error">Obavezni varijabilni materijal mora imati kolicinu.</p>}
        {exceedsStock && <p className="form-error">Kolicina prelazi dostupnu zalihu.</p>}
        {belowReorderAfterUse && <p className="form-error">Upozorenje: nakon potrosnje zaliha pada na ili ispod reorder razine.</p>}
        {terminalStatus && <p className="form-error">Termin je vec zavrsen ili otkazan, potrosnja se ne moze ponovno potvrditi.</p>}
        <ActionButton
          className="primary"
          variant="danger"
          disabled={missingRequiredVariable || exceedsStock || terminalStatus || materials.length === 0}
          onClick={completeWithMaterials}
          requiresConfirm
          confirmMessage="Potvrditi zavrsetak termina i skidanje materijala sa zalihe?"
          helpTitle="Zavrsi uz potrosnju"
          help="Zavrsava termin i skida odabrane materijale sa zalihe. Provjerite kolicine prije potvrde."
        >
          Zavrsi uz potrosnju
        </ActionButton>
      </WorkspaceSection>

      <WorkspaceSection title="Racun" actions={relatedInvoice ? <Link className="primary link-button" to={`/invoices?invoice=${relatedInvoice.id}`}>Otvori racun</Link> : <ActionButton className="primary" variant="workflow" onClick={createInvoice} helpTitle="Kreiraj nacrt racuna" help="Stvara draft racun iz termina. Racun se jos mora pregledati i izdati.">Kreiraj nacrt racuna</ActionButton>}>
        <p>{relatedInvoice ? "Racun je povezan s ovim terminom." : "Nacrt racuna jos nije kreiran."}</p>
      </WorkspaceSection>

      <WorkspaceSection title="Kretanja zalihe">
        <DataTable rows={relatedMovements} columns={[
          { header: "Tip", render: (row) => row.movement_type },
          { header: "Artikl", render: (row) => row.item?.name ?? row.inventory_item_id },
          { header: "Kolicina", render: (row) => row.quantity },
          { header: "Vrijeme", render: (row) => formatDateTime(row.created_at) }
        ]} />
      </WorkspaceSection>

      <WorkspaceSection title="Audit timeline">
        <AuditTimeline logs={audit.data} />
      </WorkspaceSection>
    </WorkspaceLayout>
  );
}
