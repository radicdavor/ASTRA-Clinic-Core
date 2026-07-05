import { FormEvent, useState } from "react";
import { api } from "../api/client";
import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { Service } from "../types";

export function Services() {
  const services = useApi<Service[]>("/api/services", []);
  const [name, setName] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    const created = await api<Service>("/api/services", { method: "POST", body: JSON.stringify({ name, duration_minutes: 30, price: 0 }) });
    services.setData([...services.data, created]);
    setName("");
  }
  return (
    <section className="page">
      <div className="page-header"><h1>Usluge</h1></div>
      <form className="inline-form" onSubmit={submit}><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Naziv nove usluge" /><button className="primary">Dodaj</button></form>
      <DataTable rows={services.data} columns={[
        { header: "Naziv", render: (row) => row.name },
        { header: "Šifra", render: (row) => row.code ?? "-" },
        { header: "Trajanje", render: (row) => `${row.duration_minutes} min` },
        { header: "Cijena", render: (row) => `${row.price} EUR` }
      ]} />
    </section>
  );
}
