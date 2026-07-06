import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import { StatusBadge, statusLabel } from "../components/StatusBadge";
import { useApi } from "../hooks/useApi";
import { Appointment, InventoryItem, Module, Provider, Room, Service } from "../types";
import { formatDate } from "../utils/date";

const today = new Date().toISOString().slice(0, 10);
const quickStatuses = ["arrived", "in_progress", "completed", "cancelled"];

export function Dashboard() {
  const navigate = useNavigate();
  const [day, setDay] = useState(today);
  const [provider, setProvider] = useState("");
  const [room, setRoom] = useState("");
  const [service, setService] = useState("");
  const [status, setStatus] = useState("");
  const schedule = useApi<Appointment[]>(`/api/schedule/day?date=${day}`, []);
  const providers = useApi<Provider[]>("/api/providers", []);
  const rooms = useApi<Room[]>("/api/rooms", []);
  const services = useApi<Service[]>("/api/services", []);
  const modules = useApi<Module[]>("/api/modules", []);
  const lowStock = useApi<InventoryItem[]>("/api/inventory/low-stock", []);
  const expiring = useApi<any[]>("/api/inventory/expiring", []);
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [materials, setMaterials] = useState<any[]>([]);
  const [materialQuantities, setMaterialQuantities] = useState<Record<number, string>>({});
  const [workflowMessage, setWorkflowMessage] = useState("");
  const [workflowError, setWorkflowError] = useState("");

  const filtered = useMemo(() => {
    return schedule.data.filter((item) => {
      return (!provider || String(item.provider_id) === provider) && (!room || String(item.room_id) === room) && (!service || String(item.service_id) === service) && (!status || item.status === status);
    });
  }, [schedule.data, provider, room, service, status]);

  async function setAppointmentStatus(appointment: Appointment, nextStatus: string) {
    const updated = await api<Appointment>(`/api/appointments/${appointment.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: nextStatus })
    });
    schedule.setData(schedule.data.map((item) => (item.id === updated.id ? { ...item, status: updated.status } : item)));
  }

  async function openMaterialWorkflow(appointment: Appointment) {
    setWorkflowError("");
    setWorkflowMessage("");
    setSelectedAppointment(appointment);
    const suggestions = await api<any[]>(`/api/appointments/${appointment.id}/suggest-material-consumption`);
    setMaterials(suggestions);
    const next: Record<number, string> = {};
    suggestions.forEach((item) => {
      next[item.item.id] = item.auto_consumable ? String(item.quantity) : "";
    });
    setMaterialQuantities(next);
  }

  async function completeWithMaterials() {
    if (!selectedAppointment) return;
    setWorkflowError("");
    try {
      const lines = materials
        .map((item) => ({ inventory_item_id: item.item.id, quantity: materialQuantities[item.item.id], reason: "Potrosnja po terminu" }))
        .filter((line) => line.quantity && Number(line.quantity) > 0);
      const updated = await api<Appointment>(`/api/appointments/${selectedAppointment.id}/complete-with-consumption`, {
        method: "POST",
        body: JSON.stringify({ lines })
      });
      schedule.setData(schedule.data.map((item) => (item.id === updated.id ? { ...item, status: updated.status } : item)));
      setWorkflowMessage("Termin je zavrsen i materijal je skinut sa zalihe.");
      setSelectedAppointment(null);
    } catch (error) {
      setWorkflowError(error instanceof Error ? error.message : "Greska kod zavrsetka termina");
    }
  }

  async function draftInvoice(appointment: Appointment) {
    const invoice = await api<{ id: number }>(`/api/appointments/${appointment.id}/draft-invoice`, { method: "POST" });
    navigate(`/invoices?invoice=${invoice.id}`);
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Danasnji raspored</h1>
          <p>Pacijenti, statusi i operativna upozorenja za odabrani dan.</p>
        </div>
        <input type="date" value={day} onChange={(event) => setDay(event.target.value)} />
      </div>

      <div className="metrics">
        <div><span>Termini</span><strong>{filtered.length}</strong></div>
        <div><span>Niska zaliha</span><strong>{lowStock.data.length}</strong></div>
        <div><span>Rokovi</span><strong>{expiring.data.length}</strong></div>
        <div><span>Aktivni moduli</span><strong>{modules.data.filter((m) => m.enabled).length}</strong></div>
      </div>

      <div className="filters">
        <select value={provider} onChange={(event) => setProvider(event.target.value)}><option value="">Svi lijecnici</option>{providers.data.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}</select>
        <select value={room} onChange={(event) => setRoom(event.target.value)}><option value="">Sve sobe</option>{rooms.data.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
        <select value={service} onChange={(event) => setService(event.target.value)}><option value="">Sve usluge</option>{services.data.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
        <select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Svi statusi</option>{["scheduled", "confirmed", "arrived", "in_progress", "completed", "cancelled"].map((s) => <option key={s} value={s}>{statusLabel(s)}</option>)}</select>
      </div>

      <div className="dashboard-grid">
        <DataTable
          rows={filtered}
          columns={[
            { header: "Vrijeme", render: (row) => `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}` },
            { header: "Pacijent", render: (row) => <Link to={`/appointments/${row.id}`}>{row.patient?.first_name ?? ""} {row.patient?.last_name ?? ""}</Link> },
            { header: "Usluga", render: (row) => row.service?.name ?? row.service_id },
            { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
            { header: "Brze radnje", render: (row) => <div className="quick-actions">{quickStatuses.map((s) => <button key={s} onClick={() => setAppointmentStatus(row, s)}>{statusLabel(s)}</button>)}<button onClick={() => openMaterialWorkflow(row)}>Materijal</button><button onClick={() => draftInvoice(row)}>Racun</button></div> }
          ]}
        />
        <aside className="side-panel">
          <h2>Operativna upozorenja</h2>
          <h3>Niska zaliha</h3>
          {lowStock.data.slice(0, 5).map((item) => <p key={item.id}>{item.name}: {item.current_stock} {item.unit_of_measure}</p>)}
          <h3>Rokovi trajanja</h3>
          {expiring.data.slice(0, 5).map((batch) => <p key={batch.id}>{batch.item?.name ?? "Artikl"}: {formatDate(batch.expiration_date)}</p>)}
        </aside>
      </div>
      {workflowMessage && <p className="success-message">{workflowMessage}</p>}
      {selectedAppointment && (
        <div className="modal-backdrop">
          <div className="modal-panel">
            <h2>Zavrsi uz potrosnju materijala</h2>
            {workflowError && <p className="form-error">{workflowError}</p>}
            <div className="material-list">
              {materials.map((item) => (
                <label key={item.template_id}>
                  <span>{item.item.name} {item.required ? "(obavezno)" : "(opcionalno)"} {item.warning ? `- ${item.warning}` : ""}</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={materialQuantities[item.item.id] ?? ""}
                    onChange={(event) => setMaterialQuantities({ ...materialQuantities, [item.item.id]: event.target.value })}
                    placeholder={item.requires_user_quantity ? "Unesite kolicinu" : "0"}
                  />
                </label>
              ))}
            </div>
            <div className="quick-actions">
              <ActionButton
                className="primary"
                variant="danger"
                onClick={completeWithMaterials}
                requiresConfirm
                confirmMessage="Potvrditi zavrsetak termina i skidanje materijala sa zalihe?"
                helpTitle="Potvrdi zavrsetak"
                help="Zavrsava termin iz dnevnog rasporeda i skida odabrane materijale sa zalihe."
              >
                Potvrdi zavrsetak
              </ActionButton>
              <button onClick={() => setSelectedAppointment(null)}>Odustani</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
