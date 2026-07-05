import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { StatusBadge } from "../components/StatusBadge";
import { useApi } from "../hooks/useApi";
import { Appointment } from "../types";

export function Appointments() {
  const { data } = useApi<Appointment[]>("/api/appointments", []);
  return (
    <section className="page">
      <div className="page-header"><h1>Termini</h1><Link className="primary link-button" to="/appointments/new">Novi termin</Link></div>
      <DataTable rows={data} columns={[
        { header: "Datum", render: (row) => row.date },
        { header: "Vrijeme", render: (row) => `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}` },
        { header: "Pacijent", render: (row) => `${row.patient?.first_name ?? ""} ${row.patient?.last_name ?? ""}` },
        { header: "Usluga", render: (row) => row.service?.name ?? row.service_id },
        { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
        { header: "Detalj", render: (row) => <Link to={`/appointments/${row.id}`}>Otvori</Link> }
      ]} />
    </section>
  );
}
