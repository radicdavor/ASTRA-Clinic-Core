import { FormEvent, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import { DateInput } from "../components/DateInput";
import { HelpHint } from "../components/HelpHint";
import { useApi } from "../hooks/useApi";
import { ClinicalDocument } from "../types";
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

export function ClinicalDocuments() {
  const [params] = useSearchParams();
  const initialPatientId = params.get("patient_id") ?? "";
  const [showUpload, setShowUpload] = useState(Boolean(initialPatientId));
  const [filter, setFilter] = useState({ q: "", patient_id: initialPatientId, document_type: "", review: "" });
  const [draft, setDraft] = useState({
    patient_id: initialPatientId,
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

  const query = useMemo(() => {
    const next = new URLSearchParams();
    if (filter.q.trim()) next.set("q", filter.q.trim());
    if (filter.patient_id.trim()) next.set("patient_id", filter.patient_id.trim());
    if (filter.document_type) next.set("document_type", filter.document_type);
    if (filter.review) next.set("physician_reviewed", filter.review);
    return `/api/clinical-documents${next.toString() ? `?${next.toString()}` : ""}`;
  }, [filter]);
  const documents = useApi<ClinicalDocument[]>(query, []);

  async function upload(event: FormEvent) {
    event.preventDefault();
    const created = await api<ClinicalDocument>("/api/clinical-documents/upload", {
      method: "POST",
      body: JSON.stringify({
        ...draft,
        patient_id: Number(draft.patient_id),
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
        <select value={filter.review} onChange={(event) => setFilter({ ...filter, review: event.target.value })}><option value="">Svi statusi</option><option value="false">Ceka pregled</option><option value="true">Pregledano</option></select>
      </div>

      {showUpload && (
        <form className="form-grid" onSubmit={upload}>
          <label>Patient ID<input required value={draft.patient_id} onChange={(event) => setDraft({ ...draft, patient_id: event.target.value })} /></label>
          <label className="wide-field">Naslov<input required value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} /></label>
          <label>Izvor<select value={draft.source_type} onChange={(event) => setDraft({ ...draft, source_type: event.target.value })}>{sourceTypes.map((type) => <option key={type} value={type}>{sourceTypeLabel(type)}</option>)}</select></label>
          <label>Tip<select value={draft.document_type} onChange={(event) => setDraft({ ...draft, document_type: event.target.value })}>{documentTypes.map((type) => <option key={type} value={type}>{documentTypeLabel(type)}</option>)}</select></label>
          <label>Datum dokumenta<DateInput value={draft.document_date} onChange={(value) => setDraft({ ...draft, document_date: value })} /></label>
          <label>Ustanova<input value={draft.institution} onChange={(event) => setDraft({ ...draft, institution: event.target.value })} /></label>
          <label>Autor<input value={draft.author} onChange={(event) => setDraft({ ...draft, author: event.target.value })} /></label>
          <label>Datoteka placeholder<input value={draft.attachment_name} onChange={(event) => setDraft({ ...draft, attachment_name: event.target.value })} placeholder="nalaz.pdf" /></label>
          <label className="wide-field">OCR / tekst dokumenta<textarea rows={6} value={draft.raw_text} onChange={(event) => setDraft({ ...draft, raw_text: event.target.value })} /></label>
          <ActionButton type="submit" className="primary" variant="create" helpTitle="Spremi dokument" help="Sprema metapodatke i tekst. OCR engine jos nije implementiran; ovo je placeholder arhitektura.">
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
        { header: "Pregled", render: (row) => row.physician_reviewed ? "Pregledano" : "Ceka pregled" }
      ]} />
    </section>
  );
}
