import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { Module } from "../types";

export function Modules() {
  const { data } = useApi<Module[]>("/api/modules", []);
  return (
    <section className="page">
      <h1>Moduli</h1>
      <DataTable rows={data} columns={[
        { header: "Modul", render: (row) => row.name },
        { header: "Ključ", render: (row) => row.key },
        { header: "Opis", render: (row) => row.description ?? "-" },
        { header: "Status", render: (row) => row.enabled ? "Aktivan" : "Isključen" }
      ]} />
    </section>
  );
}
