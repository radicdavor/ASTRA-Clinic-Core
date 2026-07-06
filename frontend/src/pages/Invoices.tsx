import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, notifyUser } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { Invoice } from "../types";
import { formatDate, formatDateTime } from "../utils/date";

export function Invoices() {
  const [params] = useSearchParams();
  const invoices = useApi<Invoice[]>("/api/invoices", []);
  const [selectedId, setSelectedId] = useState<number | null>(params.get("invoice") ? Number(params.get("invoice")) : null);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [lineDraft, setLineDraft] = useState({ description: "", quantity: "1", unit_price: "0", vat_rate: "25" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const selected = useMemo(() => invoices.data.find((invoice) => invoice.id === selectedId) ?? invoices.data[0], [invoices.data, selectedId]);
  const paid = selected?.payments?.reduce((sum, payment) => sum + Number(payment.amount), 0) ?? 0;
  const remaining = Math.max(0, Number(selected?.total_amount ?? 0) - paid);
  const paymentBlocked = !selected || ["draft", "cancelled"].includes(selected.status) || remaining <= 0 || Number(paymentAmount || 0) <= 0 || Number(paymentAmount || 0) > remaining;

  function updateInvoice(updated: Invoice) {
    invoices.setData(invoices.data.map((invoice) => (invoice.id === updated.id ? updated : invoice)));
    setSelectedId(updated.id);
  }

  async function issueInvoice(invoice: Invoice) {
    setError("");
    if (!invoice.lines?.length || Number(invoice.total_amount) <= 0) {
      setError("Racun mora imati stavke i pozitivan iznos prije izdavanja.");
      notifyUser("Racun mora imati stavke i pozitivan iznos prije izdavanja.", "error");
      return;
    }
    try {
      updateInvoice(await api<Invoice>(`/api/invoices/${invoice.id}/issue`, { method: "POST" }));
      setMessage("Racun je izdan.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Greska kod izdavanja racuna");
    }
  }

  async function addPayment(invoice: Invoice) {
    setError("");
    if (["draft", "cancelled"].includes(invoice.status)) {
      setError("Uplata se moze evidentirati samo za izdan racun.");
      notifyUser("Uplata se moze evidentirati samo za izdan racun.", "error");
      return;
    }
    if (Number(paymentAmount) > remaining) {
      setError("Uplata ne smije biti veca od preostalog iznosa.");
      notifyUser("Uplata ne smije biti veca od preostalog iznosa.", "error");
      return;
    }
    try {
      await api(`/api/invoices/${invoice.id}/payments`, { method: "POST", body: JSON.stringify({ amount: paymentAmount, method: paymentMethod }) });
      updateInvoice(await api<Invoice>(`/api/invoices/${invoice.id}`));
      setPaymentAmount("");
      setMessage("Uplata je evidentirana.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Greska kod uplate");
    }
  }

  async function addLine(invoice: Invoice) {
    setError("");
    try {
      await api(`/api/invoices/${invoice.id}/lines`, { method: "POST", body: JSON.stringify(lineDraft) });
      updateInvoice(await api<Invoice>(`/api/invoices/${invoice.id}`));
      setLineDraft({ description: "", quantity: "1", unit_price: "0", vat_rate: "25" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Greska kod stavke");
    }
  }

  return (
    <section className="page">
      <div className="page-header"><h1>Racuni</h1><p>Izdavanje racuna, fiskalizacijski status i evidentiranje uplata.</p></div>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="form-error">{error}</p>}
      <DataTable rows={invoices.data} columns={[
        { header: "Broj racuna", render: (row) => <button onClick={() => setSelectedId(row.id)}>{row.invoice_number}</button> },
        { header: "Datum", render: (row) => formatDate(row.invoice_date) },
        { header: "Status", render: (row) => row.status },
        { header: "Placanje", render: (row) => row.payment_status },
        { header: "Iznos", render: (row) => `${row.total_amount} EUR` }
      ]} />

      {selected && (
        <section className="workflow-panel">
          <div className="page-header">
            <div>
              <h2>{selected.invoice_number}</h2>
              <p>{selected.status} / {selected.payment_status}</p>
            </div>
            {selected.status === "draft" && (
              <ActionButton
                className="primary"
                variant="danger"
                disabled={!selected.lines?.length || Number(selected.total_amount) <= 0}
                onClick={() => issueInvoice(selected)}
                requiresConfirm
                confirmMessage="Potvrditi izdavanje racuna?"
                helpTitle="Izdaj racun"
                help="Izdavanje zakljucava draft racun i dodjeljuje sluzbeni broj. Fiskalizacija je demo/noop, nije stvarna hrvatska fiskalizacija."
              >
                Izdaj racun
              </ActionButton>
            )}
          </div>
          <div className="metrics">
            <div><span>Ukupno</span><strong>{selected.total_amount}</strong></div>
            <div><span>Preostalo</span><strong>{remaining.toFixed(2)}</strong></div>
            <div><span>Fiskalizacija</span><strong>{selected.fiscalization_status ?? "-"}</strong></div>
            <div><span>Provider</span><strong>{selected.fiscalization_provider ?? "-"}</strong></div>
          </div>
          <p>Fiskalizacija: {selected.fiscalization_message ?? "-"}</p>
          {selected.fiscalization_provider === "noop" && <p className="form-error">Demo fiskalizacija - nije stvarna fiskalizacija.</p>}

          {selected.status === "draft" && (
            <div className="inline-form">
              <input placeholder="Opis stavke" value={lineDraft.description} onChange={(event) => setLineDraft({ ...lineDraft, description: event.target.value })} />
              <input type="number" min="0.01" step="0.01" value={lineDraft.quantity} onChange={(event) => setLineDraft({ ...lineDraft, quantity: event.target.value })} />
              <input type="number" min="0" step="0.01" value={lineDraft.unit_price} onChange={(event) => setLineDraft({ ...lineDraft, unit_price: event.target.value })} />
              <ActionButton variant="update" onClick={() => addLine(selected)} helpTitle="Dodaj stavku" help="Dodaje stavku na draft racun prije izdavanja.">
                Dodaj stavku
              </ActionButton>
            </div>
          )}

          <DataTable rows={selected.lines ?? []} columns={[
            { header: "Opis", render: (line) => line.description },
            { header: "Kolicina", render: (line) => line.quantity },
            { header: "Cijena", render: (line) => line.unit_price },
            { header: "Ukupno", render: (line) => line.total }
          ]} />

          <h3>Uplate</h3>
          <DataTable rows={selected.payments ?? []} columns={[
            { header: "Iznos", render: (payment) => payment.amount },
            { header: "Metoda", render: (payment) => payment.method },
            { header: "Referenca", render: (payment) => payment.reference ?? "-" },
            { header: "Vrijeme", render: (payment) => formatDateTime(payment.paid_at) }
          ]} />

          <div className="inline-form">
            <input type="number" min="0.01" max={remaining} step="0.01" placeholder={`Preostalo ${remaining.toFixed(2)}`} value={paymentAmount} onFocus={() => !paymentAmount && setPaymentAmount(remaining.toFixed(2))} onChange={(event) => setPaymentAmount(event.target.value)} />
            <select value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}><option value="cash">Gotovina</option><option value="card">Kartica</option><option value="bank">Transakcija</option></select>
            <ActionButton
              className="primary"
              variant="danger"
              disabled={paymentBlocked}
              onClick={() => addPayment(selected)}
              requiresConfirm
              confirmMessage="Potvrditi evidentiranje uplate?"
              helpTitle="Evidentiraj uplatu"
              help="Sprema uplatu na izdani racun i azurira status placanja."
            >
              Evidentiraj uplatu
            </ActionButton>
          </div>
        </section>
      )}
    </section>
  );
}
