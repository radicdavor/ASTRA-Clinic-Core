import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import type { PatientIdentityReconciliationStatus as Status } from "../types";

const labels: Record<Status["status"], string> = {
  pending_review: "Čeka kontrolirani pregled identiteta",
  approved_link: "Povezivanje s klinikom je odobreno",
  confirmed_distinct: "Potvrđena je druga osoba i stvoren je novi zapis",
  rejected_insufficient_evidence: "Nedovoljno dokaza — pacijent nije stvoren ni povezan",
  cancelled: "Zahtjev je otkazan",
};

export function PatientIdentityReconciliationStatus() {
  const { id = "" } = useParams();
  const [item, setItem] = useState<Status | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function refresh() {
    setLoading(true); setError("");
    try { setItem(await api<Status>(`/api/patient-identity-reconciliations/${id}`)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Status nije dostupan."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, [id]);
  return <section className="page narrow" aria-live="polite">
    <h1>Kontrolirani pregled identiteta</h1>
    <p>Pacijent nije stvoren niti povezan automatski. Strani identitet i razlog podudaranja nisu dostupni klinici koja je poslala zahtjev.</p>
    {error && <p className="form-error">{error}</p>}
    {item && <div className="card"><strong>{labels[item.status]}</strong><p>Zahtjev: <code>{item.request_id}</code></p>{item.result_patient_id && <Link to={`/patients/${item.result_patient_id}`}>Otvori pacijenta</Link>}</div>}
    <ActionButton type="button" variant="info" onClick={refresh} disabled={loading}>{loading ? "Provjera…" : "Osvježi status"}</ActionButton>
  </section>;
}
