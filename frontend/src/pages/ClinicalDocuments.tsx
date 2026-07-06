import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import { DateInput } from "../components/DateInput";
import { HelpHint } from "../components/HelpHint";
import { useApi } from "../hooks/useApi";
import { ClinicalDocument, Patient } from "../types";
import { formatDate } from "../utils/date";
import { formatPatientName } from "../utils/patientIdentity";

const documentTypes = ["consultation", "gastroscopy", "colonoscopy", "pathology", "laboratory", "radiology", "discharge", "referral", "other"];
const sourceTypes = ["internal", "external", "scanned", "uploaded"];

export function documentTypeLabel(value: string) {
  const labels: Record<string, string> = {
    consultation: "Konzultacija",
    gastroscopy: "Gastroskopija",
    colonoscopy: "Kolonoskopija",
    pathology: "Patologija",
    laboratory: "Laboratorij",
    radiology: "Radiologija",
    discharge: "Otpusno pismo",
    referral: "Uputnica",
    other: "Ostalo"
  };
  return labels[value] ?? value;
}

export function sourceTypeLabel(value: string) {
  const labels: Record<string, string> = { internal: "Interno", external: "Vanjski", scanned: "Skenirano", uploaded: "Upload" };
  return labels[value] ?? value;
}

export function reviewStatusLabel(value: ClinicalDocument["review_status"]) {
  const labels: Record<ClinicalDocument["review_status"], string> = {
    draft: "Draft / izvor zaprimljen",
    extracted: "AI ekstrakcija izradena",
    needs_physician_review: "Ceka lijecnicki pregled",
    reviewed: "Lijecnicki pregledano",
    rejected: "Odbijeno",
    superseded: "Zamijenjeno"
  };
  return labels[value] ?? value;
}

export function ClinicalDocuments() {
  const [params] = useSearchParams();
  const initialPatientId = params.get("patient_id") ?? "";
  const initialReviewStatus = params.get("review_status") ?? "";
  const initialReview = params.get("physician_reviewed") ?? "";
  const [showUpload, setShowUpload] = useState(Boolean(initialPatientId));
  const [filter, setFilter] = useState({ q: "", patient_id: initialPatientId, document_type: "", review: initialReview, review_status: initialReviewStatus });
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [draft, setDraft] = useState({
    title: "",
    source_type: "uploaded",
    document_type: "other",
    origin: "Uploaded by patient",
    document_date: "",
    institution: "",
    author: "",
    attachment_name: "",
    raw_text: ""
  });
  const patientResults = useApi<Patient[]>(patientSearch.trim().length >= 2 ? `/api/patients?q=${encodeURIComponent(patientSearch.trim())}` : "/api/patients?q=__no_patient__", []);

  useEffect(() => {
    async function loadInitialPatient() {
      if (!initialPatientId) return;
      const patient = await api<Patient>(`/api/patients/${initialPatientId}`);
      setSelectedPatient(patient);
      setPatientSearch(formatPatientName(patient));
    }
    loadInitialPatient();
  }, [initialPatientId]);

  const query = useMemo(() => {
    const next = new URLSearchParams();
    if (filter.q.trim()) next.set("q", filter.q.trim());
    if (filter.patient_id.trim()) next.set("patient_id", filter.patient_id.trim());
    if (filter.document_type) next.set("document_type", filter.document_type);
    if (filter.review) next.set("physician_reviewed", filter.review);
    if (filter.review_status) next.set("review_status", filter.review_status);
    return `/api/clinical-documents${next.toString() ? `?${next.toString()}` : ""}`;
  }, [filter]);
  const documents = useApi<ClinicalDocument[]>(query, []);

  async function upload(event: FormEvent) {
    event.preventDefault();
    const created = await api<ClinicalDocument>("/api/clinical-documents/upload", {
      method: "POST",
      body: JSON.stringify({
        ...draft,
        patient_id: selectedPatient?.id,
        document_date: draft.document_date || null,
        institution: draft.institution || null,
        author: draft.author || null,
        attachment_name: draft.attachment_name || null,
        raw_text: draft.raw_text || null
      })
    });
    documents.setData([created, ...documents.data]);
    setShowUpload(false);
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>
            Klinicki dokumenti <HelpHint title="Klinicki dokumenti">Dokumenti su temelj pacijentova klinickog znanja. AI sazetak postaje vidljiv u sazetku pacijenta tek nakon lijecnickog pregleda.</HelpHint>
          </h1>
          <p>Interni i vanjski nalazi, postupci, patologija, laboratorij, radiologija i upload dokumenti.</p>
        </div>
        <ActionButton variant="create" className="primary" onClick={() => setShowUpload(true)} helpTitle="Dodaj dokument" help="Dodaje dokument ili OCR placeholder. Ne unosite stvarne pacijentove podatke u demo okruzenju.">
          Dodaj dokument
        </ActionButton>
      </div>

      <div className="filters">
        <input placeholder="Pretrazi dokumente" value={filter.q} onChange={(event) => setFilter({ ...filter, q: event.target.value })} />
        <input placeholder="Patient ID" value={filter.patient_id} onChange={(event) => setFilter({ ...filter, patient_id: event.target.value })} />
        <select value={filter.document_type} onChange={(event) => setFilter({ ...filter, document_type: event.target.value })}><option value="">Svi tipovi</option>{documentTypes.map((type) => <option key={type} value={type}>{documentTypeLabel(type)}</option>)}</select>
        <select value={filter.review_status} onChange={(event) => setFilter({ ...filter, review_status: event.target.value, review: "" })}>
          <option value="">Svi statusi pregleda</option>
          <option value="draft">Draft / izvor zaprimljen</option>
          <option value="needs_physician_review">Ceka lijecnicki pregled</option>
          <option value="reviewed">Lijecnicki pregledano</option>
          <option value="rejected">Odbijeno</option>
          <option value="superseded">Zamijenjeno</option>
        </select>
      </div>

      {showUpload && (
        <form className="form-grid" onSubmit={upload}>
          <label className="wide-field">Pacijent
            <input placeholder="Pretraga po imenu, OIB-u, telefonu ili e-posti" value={patientSearch} onChange={(event) => { setPatientSearch(event.target.value); setSelectedPatient(null); }} />
          </label>
          {selectedPatient ? (
            <div className="selected-patient-card wide-field">
              <strong>{formatPatientName(selectedPatient)}</strong>
              <span>{[selectedPatient.date_of_birth ? formatDate(selectedPatient.date_of_birth) : null, selectedPatient.oib, selectedPatient.phone, selectedPatient.email].filter(Boolean).join(" / ") || "Identitet bez dodatnih podataka"}</span>
            </div>
          ) : (
            <div className="patient-search-results wide-field">
              {patientResults.data.slice(0, 5).map((patient) => (
                <button type="button" key={patient.id} onClick={() => { setSelectedPatient(patient); setPatientSearch(formatPatientName(patient)); }}>
                  <strong>{formatPatientName(patient)}</strong>
                  <span>{[patient.date_of_birth ? formatDate(patient.date_of_birth) : null, patient.oib, patient.phone, patient.email].filter(Boolean).join(" / ") || "Identitet bez dodatnih podataka"}</span>
                </button>
              ))}
              {patientSearch.trim().length >= 2 && patientResults.data.length === 0 && <p>Nema pronadenih pacijenata.</p>}
            </div>
          )}
          <label className="wide-field">Naslov<input required value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} /></label>
          <label>Izvor<select value={draft.source_type} onChange={(event) => setDraft({ ...draft, source_type: event.target.value })}>{sourceTypes.map((type) => <option key={type} value={type}>{sourceTypeLabel(type)}</option>)}</select></label>
          <label>Tip<select value={draft.document_type} onChange={(event) => setDraft({ ...draft, document_type: event.target.value })}>{documentTypes.map((type) => <option key={type} value={type}>{documentTypeLabel(type)}</option>)}</select></label>
          <label>Datum dokumenta<DateInput value={draft.document_date} onChange={(value) => setDraft({ ...draft, document_date: value })} /></label>
          <label>Ustanova<input value={draft.institution} onChange={(event) => setDraft({ ...draft, institution: event.target.value })} /></label>
          <label>Autor<input value={draft.author} onChange={(event) => setDraft({ ...draft, author: event.target.value })} /></label>
          <label>Datoteka placeholder<input value={draft.attachment_name} onChange={(event) => setDraft({ ...draft, attachment_name: event.target.value })} placeholder="nalaz.pdf" /></label>
          <label className="wide-field">OCR / tekst dokumenta<textarea rows={6} value={draft.raw_text} onChange={(event) => setDraft({ ...draft, raw_text: event.target.value })} /></label>
          <ActionButton type="submit" className="primary" variant="create" disabled={!selectedPatient} helpTitle="Spremi dokument" help="Sprema metapodatke i tekst. OCR engine jos nije implementiran; ovo je placeholder arhitektura.">
            Spremi dokument
          </ActionButton>
        </form>
      )}

      <DataTable rows={documents.data} columns={[
        { header: "Dokument", render: (row) => <Link to={`/clinical-documents/${row.id}`}>{row.title}</Link> },
        { header: "Pacijent", render: (row) => row.patient ? <Link to={`/patients/${row.patient_id}`}>{formatPatientName(row.patient)}</Link> : row.patient_id },
        { header: "Datum", render: (row) => formatDate(row.document_date) },
        { header: "Tip", render: (row) => documentTypeLabel(row.document_type) },
        { header: "Izvor", render: (row) => sourceTypeLabel(row.source_type) },
        { header: "Status", render: (row) => reviewStatusLabel(row.review_status) }
      ]} />
    </section>
  );
}
