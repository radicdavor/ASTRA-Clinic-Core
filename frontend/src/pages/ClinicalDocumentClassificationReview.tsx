import { FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { useApi } from "../hooks/useApi";
import type { ClinicalDocument, UnclassifiedDocumentReview } from "../types";
import { formatDate } from "../utils/date";
import { formatPatientName } from "../utils/patientIdentity";
import { documentTypeLabel, sourceTypeLabel } from "./ClinicalDocuments";

type Classification = "clinical" | "administrative" | "financial";

export function ClinicalDocumentClassificationReview() {
  const { id } = useParams();
  const navigate = useNavigate();
  const document = useApi<UnclassifiedDocumentReview | null>(
    id ? `/api/document-classification-queue/${id}` : null,
    null
  );
  const [classification, setClassification] = useState<Classification>("clinical");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!document.data || submitting) return;
    setSubmitting(true);
    try {
      const reviewed = await api<ClinicalDocument>(
        `/api/clinical-documents/${document.data.id}/classification/review`,
        {
          method: "POST",
          body: JSON.stringify({ record_classification: classification, note: note.trim() || null })
        }
      );
      navigate(reviewed.record_classification === "clinical" ? `/clinical-documents/${reviewed.id}` : "/clinical-documents");
    } finally {
      setSubmitting(false);
    }
  }

  if (document.loading) return <section className="page"><p aria-live="polite">Učitavanje dokumenta…</p></section>;
  if (document.error || !document.data) {
    return (
      <section className="page">
        <h1>Dokument nije dostupan za klasifikaciju</h1>
        <p role="alert">Dokument ne postoji, već je klasificiran ili nije u vašem dopuštenom opsegu.</p>
        <Link to="/clinical-documents">Povratak na dokumente</Link>
      </section>
    );
  }

  const current = document.data;
  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Ljudski pregled izvora</p>
          <h1>Klasificiraj dokument</h1>
          <p>Dok klasifikacija nije potvrđena, dokument nije dio kliničkog kartona.</p>
        </div>
        <Link to="/clinical-documents">Odustani</Link>
      </div>

      <div className="detail-list" aria-label="Podaci dokumenta za klasifikaciju">
        <p><span>Dokument</span><strong>{current.title}</strong></p>
        <p><span>Pacijent</span><strong>{formatPatientName(current.patient)}</strong></p>
        <p><span>Datum</span><strong>{formatDate(current.document_date)}</strong></p>
        <p><span>Tip</span><strong>{documentTypeLabel(current.document_type)}</strong></p>
        <p><span>Izvor</span><strong>{sourceTypeLabel(current.source_type)}</strong></p>
        <p><span>Trenutačno stanje</span><strong>Čeka klasifikaciju</strong></p>
      </div>

      <p>
        <a href={`/api/clinical-documents/${current.id}/source`} target="_blank" rel="noreferrer">
          Otvori izvorni dokument
        </a>
      </p>

      <form className="form-grid" onSubmit={submit}>
        <label>
          Potvrđena klasifikacija
          <select
            aria-label="Potvrđena klasifikacija"
            value={classification}
            onChange={(event) => setClassification(event.target.value as Classification)}
          >
            <option value="clinical">Klinički dokument</option>
            <option value="administrative">Administrativni dokument</option>
            <option value="financial">Financijski dokument</option>
          </select>
        </label>
        <label className="wide-field">
          Napomena pregledavatelja
          <textarea
            rows={4}
            maxLength={1000}
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Kratko obrazloženje klasifikacije"
          />
        </label>
        <ActionButton type="submit" className="primary" variant="update" disabled={submitting}>
          {submitting ? "Spremanje…" : "Potvrdi klasifikaciju"}
        </ActionButton>
      </form>
    </section>
  );
}
