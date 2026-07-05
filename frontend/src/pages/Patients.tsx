import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { Patient } from "../types";
import { formatDate } from "../utils/date";

export function Patients() {
  const { data } = useApi<Patient[]>("/api/patients", []);
  return (
    <section className="page">
      <div className="page-header"><h1>Pacijenti</h1><Link className="primary link-button" to="/patients/new">Novi pacijent</Link></div>
      <DataTable rows={data} columns={[
        { header: "Ime i prezime", render: (row) => <Link to={`/patients/${row.id}`}>{row.first_name} {row.last_name}</Link> },
        { header: "Datum rođenja", render: (row) => formatDate(row.date_of_birth) },
        { header: "Telefon", render: (row) => row.phone ?? "-" },
        { header: "E-pošta", render: (row) => row.email ?? "-" }
      ]} />
    </section>
  );
}
