import { useState } from "react";
import { api } from "../api/client";
import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { InventoryItem, PurchaseOrder, StockLocation } from "../types";

type ReceiveDraft = Record<number, { quantity_received: string; lot_number: string; expiration_date: string; location_id: string }>;

export function PurchaseOrders() {
  const orders = useApi<PurchaseOrder[]>("/api/purchase-orders", []);
  const suggestions = useApi<any[]>("/api/procurement/reorder-suggestions", []);
  const locations = useApi<StockLocation[]>("/api/inventory/stock-locations", []);
  const items = useApi<InventoryItem[]>("/api/inventory/items", []);
  const [selected, setSelected] = useState<PurchaseOrder | null>(null);
  const [draft, setDraft] = useState<ReceiveDraft>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function item(itemId: number) {
    return items.data.find((entry) => entry.id === itemId);
  }

  function selectOrder(order: PurchaseOrder) {
    const next: ReceiveDraft = {};
    order.lines.forEach((line) => {
      const remaining = Math.max(0, Number(line.quantity_ordered) - Number(line.quantity_received));
      next[line.id] = { quantity_received: remaining ? String(remaining) : "", lot_number: "", expiration_date: "", location_id: locations.data[0] ? String(locations.data[0].id) : "" };
    });
    setSelected(order);
    setDraft(next);
    setMessage("");
    setError("");
  }

  async function receiveSelected() {
    if (!selected) return;
    setError("");
    try {
      const lines = selected.lines
        .filter((line) => draft[line.id]?.quantity_received && Number(draft[line.id].quantity_received) > 0)
        .map((line) => ({
          purchase_order_line_id: line.id,
          quantity_received: draft[line.id].quantity_received,
          lot_number: draft[line.id].lot_number || null,
          expiration_date: draft[line.id].expiration_date || null,
          location_id: Number(draft[line.id].location_id),
          purchase_price: line.unit_price
        }));
      const updated = await api<PurchaseOrder>(`/api/purchase-orders/${selected.id}/receive`, { method: "POST", body: JSON.stringify({ lines }) });
      orders.setData(orders.data.map((order) => (order.id === updated.id ? updated : order)));
      setSelected(updated);
      setMessage("Zaprimanje je spremljeno.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Greska kod zaprimanja");
    }
  }

  return (
    <section className="page">
      <div className="page-header"><h1>Narudzbenice</h1><p>Prijedlozi nabave: {suggestions.data.length}</p></div>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="form-error">{error}</p>}
      <DataTable rows={orders.data} columns={[
        { header: "Broj", render: (row) => `PO-${row.id}` },
        { header: "Dobavljac", render: (row) => row.supplier?.name ?? "-" },
        { header: "Status", render: (row) => row.status },
        { header: "Datum", render: (row) => row.order_date },
        { header: "Iznos", render: (row) => `${row.total_amount} EUR` },
        { header: "Radnja", render: (row) => <button onClick={() => selectOrder(row)}>Zaprimanje</button> }
      ]} />

      {selected && (
        <section className="workflow-panel">
          <div className="page-header"><h2>Zaprimanje PO-{selected.id}</h2><p>Status: {selected.status}</p></div>
          <DataTable rows={selected.lines} columns={[
            { header: "Artikl", render: (line) => item(line.inventory_item_id)?.name ?? `Artikl ${line.inventory_item_id}` },
            { header: "Naruceno", render: (line) => line.quantity_ordered },
            { header: "Zaprimljeno", render: (line) => line.quantity_received },
            { header: "Preostalo", render: (line) => String(Math.max(0, Number(line.quantity_ordered) - Number(line.quantity_received))) },
            { header: "Kolicina", render: (line) => <input type="number" min="0" step="0.01" value={draft[line.id]?.quantity_received ?? ""} onChange={(event) => setDraft({ ...draft, [line.id]: { ...draft[line.id], quantity_received: event.target.value } })} /> },
            { header: "LOT", render: (line) => <input value={draft[line.id]?.lot_number ?? ""} onChange={(event) => setDraft({ ...draft, [line.id]: { ...draft[line.id], lot_number: event.target.value } })} placeholder={item(line.inventory_item_id)?.lot_tracking_enabled ? "Obavezno" : ""} /> },
            { header: "Rok", render: (line) => <input type="date" value={draft[line.id]?.expiration_date ?? ""} onChange={(event) => setDraft({ ...draft, [line.id]: { ...draft[line.id], expiration_date: event.target.value } })} /> },
            { header: "Lokacija", render: (line) => <select value={draft[line.id]?.location_id ?? ""} onChange={(event) => setDraft({ ...draft, [line.id]: { ...draft[line.id], location_id: event.target.value } })}>{locations.data.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}</select> }
          ]} />
          <button className="primary" onClick={receiveSelected}>Potvrdi zaprimanje</button>
        </section>
      )}
    </section>
  );
}
