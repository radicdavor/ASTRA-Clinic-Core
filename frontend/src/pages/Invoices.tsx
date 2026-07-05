import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";

type Invoice = { id: number; invoice_number: string; invoice_date: string; status: string; payment_status: string; total_amount: string };

export function Invoices() {
  const { data } = useApi<Invoice[]>("/api/invoices", []);
  return (
    <section className="page">
      <h1>Računi</h1>
      <DataTable rows={data} columns={[
        { header: "Broj računa", render: (row) => row.invoice_number },
        { header: "Datum", render: (row) => row.invoice_date },
        { header: "Status", render: (row) => row.status },
        { header: "Plaćanje", render: (row) => row.payment_status },
        { header: "Iznos", render: (row) => `${row.total_amount} EUR` }
      ]} />
    </section>
  );
}
