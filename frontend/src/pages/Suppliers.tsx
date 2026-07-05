import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { Supplier } from "../types";

export function Suppliers() {
  const { data } = useApi<Supplier[]>("/api/suppliers", []);
  return (
    <section className="page">
      <h1>Dobavljači</h1>
      <DataTable rows={data} columns={[
        { header: "Naziv", render: (row) => row.name },
        { header: "Kontakt", render: (row) => row.contact_person ?? "-" },
        { header: "E-pošta", render: (row) => row.email ?? "-" },
        { header: "Telefon", render: (row) => row.phone ?? "-" }
      ]} />
    </section>
  );
}
