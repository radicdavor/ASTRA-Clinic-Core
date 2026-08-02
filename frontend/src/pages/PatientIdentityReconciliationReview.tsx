import { useEffect, useState } from "react";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import type { PatientIdentityReconciliationReview, PatientIdentityReconciliationStatus } from "../types";

export function PatientIdentityReconciliationReviewPage() {
  const [items, setItems] = useState<PatientIdentityReconciliationReview[]>([]);
  const [selected, setSelected] = useState<PatientIdentityReconciliationReview | null>(null);
  const [reason, setReason] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  async function load() { setItems(await api<PatientIdentityReconciliationReview[]>("/api/patient-identity-reconciliations/review/pending")); }
  useEffect(() => { void load().catch((cause) => setError(cause instanceof Error ? cause.message : "Red nije dostupan.")); }, []);
  async function decide(action: "approve-link" | "confirm-distinct" | "reject", candidatePatientId?: number) {
    if (!selected || reason.trim().length < 3 || pending) return;
    setPending(true); setError("");
    try {
      await api<PatientIdentityReconciliationStatus>(`/api/patient-identity-reconciliations/review/${selected.request_id}/${action}`, { method: "POST", body: JSON.stringify({ reason: reason.trim(), candidate_patient_id: candidatePatientId ?? null }) });
      setSelected(null); setReason(""); await load();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Odluka nije spremljena."); }
    finally { setPending(false); }
  }
  return <section className="page" aria-labelledby="identity-review-heading">
    <h1 id="identity-review-heading">Pregled identiteta pacijenta</h1>
    <p>Osjetljivi, auditirani workflow. Prikaz je ograničen na kandidate povezane s konkretnim zahtjevom; ne postoji globalna pretraga pacijenata.</p>
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="split-layout">
      <div>{items.length === 0 ? <p>Nema otvorenih zahtjeva.</p> : items.map(item => <button type="button" key={item.request_id} onClick={() => setSelected(item)}>{item.request_id} · klinika {item.requesting_clinic_id}</button>)}</div>
      {selected && <div className="card" role="region" aria-label="Minimalna usporedba identiteta">
        <h2>Minimalna usporedba</h2>
        <p>Poslani identitet: {String(selected.submitted_identity.first_name)} {String(selected.submitted_identity.last_name)} · {String(selected.submitted_identity.date_of_birth ?? "DOB nije naveden")}</p>
        {selected.candidates.map(candidate => <div key={candidate.patient_id} className="card">
          <strong>{candidate.first_name} {candidate.last_name}</strong><p>{candidate.date_of_birth} · OIB {candidate.oib_masked ?? "—"} · e-pošta {candidate.email_masked ?? "—"} · telefon {candidate.phone_masked ?? "—"}</p>
          <ActionButton type="button" variant="admin" disabled={pending || reason.trim().length < 3} onClick={() => decide("approve-link", candidate.patient_id)}>Odobri povezivanje</ActionButton>
        </div>)}
        <label>Obrazloženje odluke<textarea value={reason} onChange={event => setReason(event.target.value)} required /></label>
        <div className="button-row"><ActionButton type="button" variant="admin" disabled={pending || reason.trim().length < 3} onClick={() => decide("confirm-distinct")}>Potvrdi da je druga osoba</ActionButton><ActionButton type="button" variant="danger" disabled={pending || reason.trim().length < 3} onClick={() => decide("reject")}>Odbij — nedovoljno dokaza</ActionButton></div>
      </div>}
    </div>
  </section>;
}
