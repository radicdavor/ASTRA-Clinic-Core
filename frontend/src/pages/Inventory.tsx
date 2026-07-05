import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { InventoryItem } from "../types";

export function Inventory() {
  const items = useApi<InventoryItem[]>("/api/inventory/items", []);
  const low = useApi<InventoryItem[]>("/api/inventory/low-stock", []);
  const expiring = useApi<any[]>("/api/inventory/expiring", []);
  const stockValue = items.data.reduce((sum, item) => sum + Number(item.current_stock) * Number(item.purchase_price), 0);
  return (
    <section className="page">
      <div className="page-header"><h1>Inventar</h1><p>Pregled zaliha, rokova i vrijednosti skladišta.</p></div>
      <div className="metrics">
        <div><span>Vrijednost zalihe</span><strong>{stockValue.toFixed(2)} EUR</strong></div>
        <div><span>Niska zaliha</span><strong>{low.data.length}</strong></div>
        <div><span>Rok uskoro istječe</span><strong>{expiring.data.length}</strong></div>
        <div><span>Artikli</span><strong>{items.data.length}</strong></div>
      </div>
      <DataTable rows={items.data} columns={[
        { header: "SKU", render: (row) => row.sku },
        { header: "Artikl", render: (row) => row.name },
        { header: "Kategorija", render: (row) => row.category ?? "-" },
        { header: "Trenutno", render: (row) => `${row.current_stock} ${row.unit_of_measure}` },
        { header: "Narudžba ispod", render: (row) => row.reorder_point }
      ]} />
    </section>
  );
}
