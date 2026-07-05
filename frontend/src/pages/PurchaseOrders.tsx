import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";

type PurchaseOrder = { id: number; status: string; order_date: string; expected_delivery_date?: string; total_amount: string; supplier?: { name: string } };

export function PurchaseOrders() {
  const { data } = useApi<PurchaseOrder[]>("/api/purchase-orders", []);
  const suggestions = useApi<any[]>("/api/procurement/reorder-suggestions", []);
  return (
    <section className="page">
      <div className="page-header"><h1>Narudžbenice</h1><p>Prijedlozi nabave: {suggestions.data.length}</p></div>
      <DataTable rows={data} columns={[
        { header: "Broj", render: (row) => `PO-${row.id}` },
        { header: "Dobavljač", render: (row) => row.supplier?.name ?? "-" },
        { header: "Status", render: (row) => row.status },
        { header: "Datum", render: (row) => row.order_date },
        { header: "Iznos", render: (row) => `${row.total_amount} EUR` }
      ]} />
    </section>
  );
}
