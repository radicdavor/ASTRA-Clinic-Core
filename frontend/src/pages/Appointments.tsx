import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { Trash2 } from "lucide-react";
import { api } from "../api/client";
import { ConfirmActionDialog } from "../components/ConfirmActionDialog";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { StatusBadge } from "../components/StatusBadge";
import { useApi } from "../hooks/useApi";
import { Appointment } from "../types";
import { formatDate } from "../utils/date";

export function Appointments() {
  const location = useLocation();
  const { data, setData } = useApi<Appointment[]>("/api/appointments", []);
  const [deleteTarget, setDeleteTarget] = useState<Appointment | null>(null);

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
      <DataTable rows={data} columns={[
        { header: "Datum", render: (row) => formatDate(row.date) },
        { header: "Vrijeme", render: (row) => `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}` },
        { header: "Pacijent", render: (row) => `${row.patient?.first_name ?? ""} ${row.patient?.last_name ?? ""}` },
        { header: "Usluga", render: (row) => row.service?.name ?? row.service_id },
        { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
        { header: "Detalj", render: (row) => <Link to={`/appointments/${row.id}`} state={{ backgroundLocation: location }}>Otvori</Link> },
        { header: "Brisanje", render: (row) => (
          <button type="button" className="icon-button delete-icon-button" aria-label={`Obrisi termin ${formatDate(row.date)} u ${row.start_time.slice(0, 5)}`} title="Obrisi termin" onClick={() => setDeleteTarget(row)}>
            <Trash2 size={18} aria-hidden="true" />
          </button>
        ) }
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
