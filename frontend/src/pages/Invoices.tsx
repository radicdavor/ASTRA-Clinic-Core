import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, notifyUser } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import {
  EmptyState,
  ListFilterBar,
  ListPageHeader,
  ProgressiveDetailPanel,
  RowMoreMenu,
  StatusSummary,
} from "../components/OperationalList";
import { useApi } from "../hooks/useApi";
import { Invoice, InvoiceOperationalListItem } from "../types";
import { formatDate, formatDateTime } from "../utils/date";

function money(value: string | number) {
  return new Intl.NumberFormat("hr-HR", { style: "currency", currency: "EUR" }).format(Number(value));
}

export function invoiceOperationalStatus(invoice: InvoiceOperationalListItem) {
  if (invoice.status === "cancelled") return { label: "Storniran", tone: "danger" as const };
  if (invoice.status === "refunded" || invoice.payment_status === "refunded") return { label: "Refundiran", tone: "neutral" as const };
  if (invoice.payment_status === "paid" || invoice.status === "paid") return { label: "Plaćen", tone: "success" as const };
  if (invoice.payment_status === "partially_paid" || invoice.status === "partially_paid") {
    return { label: "Djelomično plaćen", detail: `Otvoreno ${money(invoice.outstanding_amount)}`, tone: "warning" as const };
  }
  if (invoice.payment_status === "deferred") return { label: "Odgođeno", tone: "warning" as const };
  if (invoice.status === "draft") return { label: "Nacrt", tone: "neutral" as const };
  if (invoice.status === "ready") return { label: "Spreman za izdavanje", tone: "in-progress" as const };
  return { label: "Otvoren", detail: `Otvoreno ${money(invoice.outstanding_amount)}`, tone: "warning" as const };
}

function primaryActionLabel(invoice: InvoiceOperationalListItem) {
  if (invoice.status === "draft" && invoice.can_issue) return "Izdaj račun";
  if (Number(invoice.outstanding_amount) > 0 && invoice.can_record_payment && !["draft", "cancelled"].includes(invoice.status)) {
    return invoice.payment_status === "partially_paid" ? "Nastavi naplatu" : "Evidentiraj uplatu";
  }
  return "Otvori račun";
}

function detailProjection(invoice: Invoice, paid: number, remaining: number): InvoiceOperationalListItem {
  return {
    id: invoice.id,
    patient_id: invoice.patient_id ?? 0,
    patient_name: "",
    invoice_number: invoice.invoice_number,
    invoice_date: invoice.invoice_date,
    status: invoice.status,
    payment_status: invoice.payment_status,
    total_amount: invoice.total_amount,
    paid_amount: paid.toFixed(2),
    outstanding_amount: remaining.toFixed(2),
    payment_count: invoice.payments?.length ?? 0,
    can_issue: false,
    can_record_payment: false,
  };
}

export function Invoices() {
  const [params] = useSearchParams();
  const invoiceList = useApi<InvoiceOperationalListItem[]>("/api/invoices/operational-list", []);
  const [selectedId, setSelectedId] = useState<number | null>(params.get("invoice") ? Number(params.get("invoice")) : null);
  const selected = useApi<Invoice | null>(selectedId ? `/api/invoices/${selectedId}` : null, null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [lineDraft, setLineDraft] = useState({ description: "", quantity: "1", unit_price: "0", vat_rate: "25" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const visibleInvoices = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("hr");
    return invoiceList.data.filter((invoice) => {
      const matchesQuery = !normalized || `${invoice.patient_name} ${invoice.invoice_number}`.toLocaleLowerCase("hr").includes(normalized);
      return matchesQuery && (!statusFilter || invoiceOperationalStatus(invoice).label === statusFilter);
    });
  }, [invoiceList.data, query, statusFilter]);
  const paid = selected.data?.payments?.reduce((sum, payment) => sum + Number(payment.amount), 0) ?? 0;
  const remaining = Math.max(0, Number(selected.data?.total_amount ?? 0) - paid);
  const paymentBlocked = !selected.data || ["draft", "cancelled"].includes(selected.data.status) || remaining <= 0 || Number(paymentAmount || 0) <= 0 || Number(paymentAmount || 0) > remaining;

  function updateInvoice(updated: Invoice) {
    selected.setData(updated);
    const paidAmount = updated.payments?.reduce((sum, payment) => sum + Number(payment.amount), 0) ?? 0;
    invoiceList.setData(invoiceList.data.map((invoice) => invoice.id === updated.id ? {
      ...invoice,
      invoice_number: updated.invoice_number,
      invoice_date: updated.invoice_date,
      status: updated.status,
      payment_status: updated.payment_status,
      total_amount: updated.total_amount,
      paid_amount: paidAmount.toFixed(2),
      outstanding_amount: Math.max(0, Number(updated.total_amount) - paidAmount).toFixed(2),
      payment_count: updated.payments?.length ?? 0,
    } : invoice));
  }

  async function issueInvoice(invoice: Invoice) {
    setError("");
    if (!invoice.lines?.length || Number(invoice.total_amount) <= 0) {
      setError("Račun mora imati stavke i pozitivan iznos prije izdavanja.");
      notifyUser("Račun mora imati stavke i pozitivan iznos prije izdavanja.", "error");
      return;
    }
    try {
      updateInvoice(await api<Invoice>(`/api/invoices/${invoice.id}/issue`, { method: "POST" }));
      setMessage("Račun je izdan.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Greška kod izdavanja računa");
    }
  }

  async function addPayment(invoice: Invoice) {
    setError("");
    if (["draft", "cancelled"].includes(invoice.status)) {
      setError("Uplata se može evidentirati samo za izdani račun.");
      notifyUser("Uplata se može evidentirati samo za izdani račun.", "error");
      return;
    }
    if (Number(paymentAmount) > remaining) {
      setError("Uplata ne smije biti veća od preostalog iznosa.");
      notifyUser("Uplata ne smije biti veća od preostalog iznosa.", "error");
      return;
    }
    try {
      await api(`/api/invoices/${invoice.id}/payments`, { method: "POST", body: JSON.stringify({ amount: paymentAmount, method: paymentMethod }) });
      updateInvoice(await api<Invoice>(`/api/invoices/${invoice.id}`));
      setPaymentAmount("");
      setMessage("Uplata je evidentirana.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Greška kod uplate");
    }
  }

  async function addLine(invoice: Invoice) {
    setError("");
    try {
      await api(`/api/invoices/${invoice.id}/lines`, { method: "POST", body: JSON.stringify(lineDraft) });
      updateInvoice(await api<Invoice>(`/api/invoices/${invoice.id}`));
      setLineDraft({ description: "", quantity: "1", unit_price: "0", vat_rate: "25" });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Greška kod stavke");
    }
  }

  function closeDetail() {
    setSelectedId(null);
    selected.setData(null);
    setError("");
    setMessage("");
  }

  return (
    <section className="page operational-list-page">
      <ListPageHeader eyebrow="Financije" title="Računi i plaćanja" description="Pronađite račun, provjerite otvoreni iznos i izvršite jednu sljedeću radnju." />
      <ListFilterBar showClear={Boolean(query || statusFilter)} onClear={() => { setQuery(""); setStatusFilter(""); }}>
        <input aria-label="Pretraži račune" placeholder="Pacijent ili broj računa" value={query} onChange={(event) => setQuery(event.target.value)} />
        <select aria-label="Status računa" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="">Svi statusi</option>
          <option>Nacrt</option><option>Spreman za izdavanje</option><option>Otvoren</option>
          <option>Djelomično plaćen</option><option>Plaćen</option><option>Odgođeno</option>
          <option>Storniran</option><option>Refundiran</option>
        </select>
      </ListFilterBar>

      <div aria-live="polite">
        {invoiceList.loading ? (
          <p className="operational-list-loading">Učitavanje računa…</p>
        ) : invoiceList.status === 403 ? (
          <EmptyState kind="forbidden" description="Vaša uloga nema pristup računima u aktivnoj klinici." />
        ) : invoiceList.error ? (
          <EmptyState kind="unavailable" description={invoiceList.error} />
        ) : visibleInvoices.length === 0 ? (
          <EmptyState kind={query || statusFilter ? "filtered" : "empty"} title={query || statusFilter ? undefined : "Nema računa"} />
        ) : (
          <DataTable ariaLabel="Računi i plaćanja" rows={visibleInvoices} columns={[
            { header: "Pacijent", render: (row) => <span className="invoice-patient"><Link to={`/patients/${row.patient_id}`}>{row.patient_name}</Link><small>{row.invoice_number}</small></span> },
            { header: "Datum", render: (row) => formatDate(row.invoice_date) },
            { header: "Iznos", render: (row) => money(row.total_amount) },
            { header: "Otvoreno", render: (row) => Number(row.outstanding_amount) === 0 ? <strong className="paid-copy">Plaćeno</strong> : money(row.outstanding_amount) },
            { header: "Status", render: (row) => <StatusSummary {...invoiceOperationalStatus(row)} /> },
            { header: "Radnja", render: (row) => <span className="invoice-row-actions">
              <button type="button" className="action-button" onClick={() => setSelectedId(row.id)}>{primaryActionLabel(row)}</button>
              <RowMoreMenu label={`Dodatne radnje za račun ${row.invoice_number}`}>
                <Link role="menuitem" to={`/patients/${row.patient_id}`}>Otvori karton pacijenta</Link>
                <button role="menuitem" type="button" onClick={() => setSelectedId(row.id)}>Stavke i povijest uplata</button>
              </RowMoreMenu>
            </span> },
          ]} />
        )}
      </div>

      <ProgressiveDetailPanel open={selectedId !== null} title={selected.data?.invoice_number ?? "Detalj računa"} onClose={closeDetail} loading={selected.loading} error={selected.error ?? undefined}>
        {selected.data && <div className="invoice-detail">
          <header>
            <StatusSummary {...invoiceOperationalStatus(detailProjection(selected.data, paid, remaining))} />
            {selected.data.status === "draft" && <ActionButton className="primary" variant="danger" disabled={!selected.data.lines?.length || Number(selected.data.total_amount) <= 0} onClick={() => issueInvoice(selected.data!)} requiresConfirm confirmMessage="Potvrditi izdavanje računa?" helpTitle="Izdaj račun" help="Izdavanje zaključava nacrt računa. Fiskalizacija je demo/noop.">Izdaj račun</ActionButton>}
          </header>
          {message && <p className="success-message" role="status">{message}</p>}
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="metrics">
            <div><span>Ukupno</span><strong>{money(selected.data.total_amount)}</strong></div>
            <div><span>Otvoreno</span><strong>{remaining === 0 ? "Plaćeno" : money(remaining)}</strong></div>
            <div><span>Uplate</span><strong>{selected.data.payments?.length ?? 0}</strong></div>
          </div>

          {selected.data.status === "draft" && <div className="inline-form">
            <input aria-label="Opis stavke" placeholder="Opis stavke" value={lineDraft.description} onChange={(event) => setLineDraft({ ...lineDraft, description: event.target.value })} />
            <input aria-label="Količina stavke" type="number" min="0.01" step="0.01" value={lineDraft.quantity} onChange={(event) => setLineDraft({ ...lineDraft, quantity: event.target.value })} />
            <input aria-label="Cijena stavke" type="number" min="0" step="0.01" value={lineDraft.unit_price} onChange={(event) => setLineDraft({ ...lineDraft, unit_price: event.target.value })} />
            <ActionButton variant="update" onClick={() => addLine(selected.data!)} helpTitle="Dodaj stavku" help="Dodaje stavku na nacrt računa prije izdavanja.">Dodaj stavku</ActionButton>
          </div>}

          <h3>Stavke računa</h3>
          <DataTable ariaLabel="Stavke računa" rows={selected.data.lines ?? []} columns={[
            { header: "Opis", render: (line) => line.description },
            { header: "Količina", render: (line) => line.quantity },
            { header: "Cijena", render: (line) => money(line.unit_price) },
            { header: "Ukupno", render: (line) => money(line.total) },
          ]} />

          <h3>Povijest uplata</h3>
          <DataTable ariaLabel="Povijest uplata" rows={selected.data.payments ?? []} columns={[
            { header: "Iznos", render: (payment) => money(payment.amount) },
            { header: "Metoda", render: (payment) => payment.method },
            { header: "Referenca", render: (payment) => payment.reference ?? "—" },
            { header: "Vrijeme", render: (payment) => payment.paid_at ? formatDateTime(payment.paid_at) : "—" },
          ]} />

          {!["draft", "cancelled"].includes(selected.data.status) && remaining > 0 && <div className="inline-form">
            <input aria-label="Iznos uplate" type="number" min="0.01" max={remaining} step="0.01" placeholder={`Preostalo ${remaining.toFixed(2)}`} value={paymentAmount} onFocus={() => !paymentAmount && setPaymentAmount(remaining.toFixed(2))} onChange={(event) => setPaymentAmount(event.target.value)} />
            <select aria-label="Način plaćanja" value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}><option value="cash">Gotovina</option><option value="card">Kartica</option><option value="bank">Transakcija</option></select>
            <ActionButton className="primary" variant="danger" disabled={paymentBlocked} onClick={() => addPayment(selected.data!)} requiresConfirm confirmMessage="Potvrditi evidentiranje uplate?" helpTitle="Evidentiraj uplatu" help="Sprema uplatu na izdani račun i ažurira status plaćanja.">Evidentiraj uplatu</ActionButton>
          </div>}
        </div>}
      </ProgressiveDetailPanel>
    </section>
  );
}
