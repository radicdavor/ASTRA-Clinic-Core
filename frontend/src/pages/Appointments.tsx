import { Link, useLocation } from "react-router-dom";
import { useMemo, useState } from "react";
import { Trash2 } from "lucide-react";
import { api } from "../api/client";
import { ConfirmActionDialog } from "../components/ConfirmActionDialog";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { StatusBadge } from "../components/StatusBadge";
import { useApi } from "../hooks/useApi";
import { Appointment } from "../types";
import { formatDate } from "../utils/date";

const inactiveAppointmentStatuses = new Set(["cancelled", "no_show"]);

export function parallelAppointmentIds(appointments: Appointment[]) {
  const ids = new Set<number>();
  for (const appointment of appointments) {
    if (inactiveAppointmentStatuses.has(appointment.status)) continue;
    for (const other of appointments) {
      if (
        other.id === appointment.id
        || inactiveAppointmentStatuses.has(other.status)
        || other.date !== appointment.date
        || other.start_time >= appointment.end_time
        || other.end_time <= appointment.start_time
      ) continue;
      if (
        other.patient_id !== appointment.patient_id
        && other.provider_id !== appointment.provider_id
        && other.room_id !== appointment.room_id
      ) {
        ids.add(appointment.id);
        ids.add(other.id);
      }
    }
  }
  return ids;
}

export function Appointments() {
  const location = useLocation();
  const { data, setData } = useApi<Appointment[]>("/api/appointments", []);
  const [deleteTarget, setDeleteTarget] = useState<Appointment | null>(null);
  const parallelIds = useMemo(() => parallelAppointmentIds(data), [data]);

  async function deleteAppointment() {
    if (!deleteTarget) return;
    await api(`/api/appointments/${deleteTarget.id}`, { method: "DELETE" });
    setData(data.filter((item) => item.id !== deleteTarget.id));
    setDeleteTarget(null);
  }
  const deletePatientName = deleteTarget ? `${deleteTarget.patient?.first_name ?? ""} ${deleteTarget.patient?.last_name ?? ""}`.trim() || `pacijenta #${deleteTarget.patient_id}` : "";
  return (
    <section className="page">
      <div className="page-header">
        <h1>Termini</h1>
        <span className="action-with-help"><Link className="link-button" to="/appointments/package">Naruči paket</Link>
          <Link className="primary link-button" to="/appointments/new" state={{ backgroundLocation: location }}>Novi termin</Link>
          <HelpHint title="Novi termin">Termin povezuje pacijenta, uslugu, lijecnika, sobu i vrijeme.</HelpHint>
        </span>
      </div>
      <DataTable ariaLabel="Naručeni termini" rows={data} columns={[
        { header: "Termin", render: (row) => <span className="appointment-time-cell"><strong>{formatDate(row.date)}</strong><span>{row.start_time.slice(0, 5)}–{row.end_time.slice(0, 5)}</span>{parallelIds.has(row.id) && <span className="appointment-parallel-badge" aria-label="Paralelni termin s drugim pacijentom, liječnikom i prostorijom">Paralelni termin</span>}</span> },
        { header: "Pacijent", render: (row) => `${row.patient?.first_name ?? ""} ${row.patient?.last_name ?? ""}` },
        { header: "Usluga", render: (row) => row.service?.name ?? row.service_id },
        { header: "Liječnik", render: (row) => <strong>{row.provider?.full_name ?? "Liječnik nije naveden"}</strong> },
        { header: "Prostorija", render: (row) => <strong>{row.room?.name ?? "Prostorija nije navedena"}</strong> },
        { header: "Status i radnja", render: (row) => <span className="appointment-row-actions"><StatusBadge status={row.status}/><Link to={`/appointments/${row.id}`} state={{ backgroundLocation: location }}>Otvori</Link><button type="button" className="icon-button delete-icon-button" aria-label={`Obriši termin ${formatDate(row.date)} u ${row.start_time.slice(0, 5)}`} title="Obriši termin" onClick={() => setDeleteTarget(row)}>
            <Trash2 size={18} aria-hidden="true" />
          </button></span> }
      ]} />
      <ConfirmActionDialog
        open={Boolean(deleteTarget)}
        title="Obrisati termin"
        message={deleteTarget ? `Obrisati termin ${formatDate(deleteTarget.date)} u ${deleteTarget.start_time.slice(0, 5)} za ${deletePatientName}? Pacijent ostaje u evidenciji.` : ""}
        confirmLabel="Obriši termin"
        onCancel={() => setDeleteTarget(null)}
        onConfirm={deleteAppointment}
      />
    </section>
  );
}
