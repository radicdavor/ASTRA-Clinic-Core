import { useMemo, useState } from "react";
import { api } from "../api/client";
import { DataTable } from "../components/DataTable";
import { StatusBadge, statusLabel } from "../components/StatusBadge";
import { useApi } from "../hooks/useApi";
import { Appointment, InventoryItem, Module, Provider, Room, Service } from "../types";

const today = new Date().toISOString().slice(0, 10);
const quickStatuses = ["arrived", "in_progress", "completed", "cancelled"];

export function Dashboard() {
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

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Današnji raspored</h1>
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
        <select value={provider} onChange={(event) => setProvider(event.target.value)}><option value="">Svi liječnici</option>{providers.data.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}</select>
        <select value={room} onChange={(event) => setRoom(event.target.value)}><option value="">Sve sobe</option>{rooms.data.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
        <select value={service} onChange={(event) => setService(event.target.value)}><option value="">Sve usluge</option>{services.data.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
        <select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Svi statusi</option>{["scheduled", "confirmed", "arrived", "in_progress", "completed", "cancelled"].map((s) => <option key={s} value={s}>{statusLabel(s)}</option>)}</select>
      </div>

      <div className="dashboard-grid">
        <DataTable
          rows={filtered}
          columns={[
            { header: "Vrijeme", render: (row) => `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}` },
            { header: "Pacijent", render: (row) => `${row.patient?.first_name ?? ""} ${row.patient?.last_name ?? ""}` },
            { header: "Usluga", render: (row) => row.service?.name ?? row.service_id },
            { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
            { header: "Brze radnje", render: (row) => <div className="quick-actions">{quickStatuses.map((s) => <button key={s} onClick={() => setAppointmentStatus(row, s)}>{statusLabel(s)}</button>)}</div> }
          ]}
        />
        <aside className="side-panel">
          <h2>Operativna upozorenja</h2>
          <h3>Niska zaliha</h3>
          {lowStock.data.slice(0, 5).map((item) => <p key={item.id}>{item.name}: {item.current_stock} {item.unit_of_measure}</p>)}
          <h3>Rokovi trajanja</h3>
          {expiring.data.slice(0, 5).map((batch) => <p key={batch.id}>{batch.item?.name ?? "Artikl"}: {batch.expiration_date}</p>)}
        </aside>
      </div>
    </section>
  );
}
