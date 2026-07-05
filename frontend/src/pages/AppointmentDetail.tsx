import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { AuditTimeline } from "../components/AuditTimeline";
import { DataTable } from "../components/DataTable";
import { StatusBadge } from "../components/StatusBadge";
import { useApi } from "../hooks/useApi";
import { Appointment, AuditLog, Invoice, StockMovement } from "../types";

export function AppointmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const appointment = useApi<Appointment | null>(`/api/appointments/${id}`, null);
  const invoices = useApi<Invoice[]>("/api/invoices", []);
  const movements = useApi<StockMovement[]>("/api/inventory/stock-movements", []);
  const audit = useApi<AuditLog[]>(`/api/audit-log?entity_type=Appointment&entity_id=${id}`, []);
  const [materials, setMaterials] = useState<any[]>([]);
  const [quantities, setQuantities] = useState<Record<number, string>>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const relatedInvoice = useMemo(() => invoices.data.find((invoice) => invoice.appointment_id === Number(id)), [invoices.data, id]);
  const relatedMovements = useMemo(() => movements.data.filter((movement) => movement.related_appointment_id === Number(id)), [movements.data, id]);

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

  async function completeWithMaterials() {
    if (!appointment.data) return;
    if (missingRequiredVariable || exceedsStock) return;
    if (!window.confirm("Ovo ce skinuti materijal sa zalihe i zavrsiti termin.")) return;
    setError("");
    try {
      const lines = materials
        .map((entry) => ({ inventory_item_id: entry.item.id, quantity: quantities[entry.item.id], reason: "Potrosnja po terminu" }))
        .filter((line) => line.quantity && Number(line.quantity) > 0);
      const updated = await api<Appointment>(`/api/appointments/${appointment.data.id}/complete-with-consumption`, { method: "POST", body: JSON.stringify({ lines }) });
      appointment.setData(updated);
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

  if (!appointment.data) return <section className="page"><p>Ucitavanje termina...</p></section>;

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>{appointment.data.patient?.first_name} {appointment.data.patient?.last_name}</h1>
          <p>{appointment.data.date} {appointment.data.start_time.slice(0, 5)} - {appointment.data.end_time.slice(0, 5)}</p>
        </div>
        <StatusBadge status={appointment.data.status} />
      </div>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="form-error">{error}</p>}

      <div className="detail-list">
        <p><span>Usluga</span><strong>{appointment.data.service?.name ?? appointment.data.service_id}</strong></p>
        <p><span>Lijecnik</span><strong>{appointment.data.provider?.full_name ?? appointment.data.provider_id}</strong></p>
        <p><span>Soba</span><strong>{appointment.data.room?.name ?? appointment.data.room_id}</strong></p>
        <p><span>Napomena</span><strong>{appointment.data.notes ?? "-"}</strong></p>
      </div>

      <section className="workflow-panel">
        <div className="page-header"><h2>Materijali</h2><button onClick={loadMaterials}>Ucitaj prijedlog</button></div>
        {materials.map((entry) => (
          <label className="material-row" key={entry.template_id}>
            <span>{entry.item.name} / {entry.required ? "obavezno" : "opcionalno"} / dostupno {entry.available_stock}</span>
            <input type="number" min="0" step="0.01" value={quantities[entry.item.id] ?? ""} onChange={(event) => setQuantities({ ...quantities, [entry.item.id]: event.target.value })} />
          </label>
        ))}
        {missingRequiredVariable && <p className="form-error">Obavezni varijabilni materijal mora imati kolicinu.</p>}
        {exceedsStock && <p className="form-error">Kolicina prelazi dostupnu zalihu.</p>}
        <button className="primary" disabled={missingRequiredVariable || exceedsStock || materials.length === 0} onClick={completeWithMaterials}>Zavrsi uz potrosnju</button>
      </section>

      <section className="workflow-panel">
        <div className="page-header"><h2>Racun</h2>{relatedInvoice ? <Link className="primary link-button" to={`/invoices?invoice=${relatedInvoice.id}`}>Otvori racun</Link> : <button className="primary" onClick={createInvoice}>Kreiraj nacrt racuna</button>}</div>
      </section>

      <section className="workflow-panel">
        <h2>Kretanja zalihe</h2>
        <DataTable rows={relatedMovements} columns={[
          { header: "Tip", render: (row) => row.movement_type },
          { header: "Artikl", render: (row) => row.item?.name ?? row.inventory_item_id },
          { header: "Kolicina", render: (row) => row.quantity },
          { header: "Vrijeme", render: (row) => new Date(row.created_at).toLocaleString() }
        ]} />
      </section>

      <section className="workflow-panel">
        <h2>Audit timeline</h2>
        <AuditTimeline logs={audit.data} />
      </section>
    </section>
  );
}
