import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { useApi } from "../hooks/useApi";
import { Patient } from "../types";
import { formatDate } from "../utils/date";

export function Patients() {
  const { data } = useApi<Patient[]>("/api/patients", []);
  return (
    <section className="page">
      <div className="page-header">
        <h1>Pacijenti</h1>
        <span className="action-with-help">
          <Link className="primary link-button" to="/patients/new">Novi pacijent</Link>
          <HelpHint title="Novi pacijent">Otvara unos novog pacijenta. U demo nacinu ne unosite stvarne osobne podatke.</HelpHint>
        </span>
      </div>
      <DataTable rows={data} columns={[
        { header: "Ime i prezime", render: (row) => <Link to={`/patients/${row.id}`}>{row.first_name} {row.last_name}</Link> },
        { header: "Datum rodenja", render: (row) => formatDate(row.date_of_birth) },
        { header: "OIB", render: (row) => row.oib ?? "-" },
        { header: "Telefon", render: (row) => row.phone ?? "-" },
        { header: "E-posta", render: (row) => row.email ?? "-" }
      ]} />
    </section>
  );
}
