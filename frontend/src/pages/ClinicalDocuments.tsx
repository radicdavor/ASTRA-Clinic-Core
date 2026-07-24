import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import { DateInput } from "../components/DateInput";
import { HelpHint } from "../components/HelpHint";
import {
  EmptyState,
  ListFilterBar,
  ListPageHeader,
  StatusSummary,
} from "../components/OperationalList";
import { QuickPatientModal } from "../components/QuickPatientModal";
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
    other: "Ostalo",
  };
  return labels[value] ?? value;
}

export function sourceTypeLabel(value: string) {
  const labels: Record<string, string> = { internal: "Interno", external: "Vanjski", scanned: "Skenirano", uploaded: "Preneseno" };
  return labels[value] ?? value;
}

export function reviewStatusLabel(value: ClinicalDocument["review_status"]) {
  const labels: Record<ClinicalDocument["review_status"], string> = {
    draft: "Izvor zaprimljen",
    extracted: "Čeka liječnički pregled",
    needs_physician_review: "Čeka liječnički pregled",
    reviewed: "Pregledano",
    rejected: "Odbijeno",
    superseded: "Zamijenjeno",
    signed: "Potpisano",
  };
  return labels[value] ?? value;
}

export function recordClassificationLabel(value?: ClinicalDocument["record_classification"]) {
  const labels: Record<string, string> = {
    clinical: "Klinički karton",
    administrative: "Administrativno",
    financial: "Financijsko",
    unclassified: "Čeka klasifikaciju",
  };
  return labels[value ?? "clinical"] ?? value;
}

export function aiExtractionStatusLabel(value: ClinicalDocument["ai_extraction_status"]) {
  const labels: Record<ClinicalDocument["ai_extraction_status"], string> = {
    not_run: "AI ekstrakcija nije pokrenuta",
    generated: "AI prijedlog generiran",
    edited: "AI prijedlog ručno uređen",
    accepted: "AI prijedlog prihvaćen kroz liječnički pregled",
    rejected: "AI prijedlog odbijen",
    superseded: "AI prijedlog zamijenjen",
  };
  return labels[value] ?? value;
}

export function documentOperationalStatus(document: ClinicalDocument) {
  if (document.review_status === "rejected") return { label: "Odbijeno", tone: "danger" as const };
  if (document.record_classification === "unclassified") return { label: "Čeka klasifikaciju", tone: "warning" as const };
  if (["extracted", "needs_physician_review"].includes(document.review_status)) {
    return {
      label: "Čeka liječnički pregled",
      detail: document.ai_extraction_status === "rejected" ? "AI prijedlog je odbijen." : undefined,
      tone: "warning" as const,
    };
  }
  if (document.review_status === "signed") return { label: "Potpisano", tone: "success" as const };
  if (document.review_status === "reviewed") return { label: "Pregledano", tone: "success" as const };
  if (document.review_status === "superseded") return { label: "Zamijenjeno", tone: "neutral" as const };
  return { label: "Izvor zaprimljen", tone: "in-progress" as const };
}

function documentPrimaryAction(document: ClinicalDocument) {
  if (document.record_classification === "unclassified") return "Dovrši klasifikaciju";
  if (["extracted", "needs_physician_review"].includes(document.review_status)) return "Pregledaj";
  return "Otvori";
}

function useDebouncedValue(value: string, delay = 250) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [delay, value]);
  return debounced;
}

export function ClinicalDocuments() {
  const [params] = useSearchParams();
  const initialPatientId = params.get("patient_id") ?? "";
  const initialReviewStatus = params.get("review_status") ?? "";
  const initialReview = params.get("physician_reviewed") ?? "";
  const [showUpload, setShowUpload] = useState(Boolean(initialPatientId));
  const [filter, setFilter] = useState({
    q: "",
    patient_id: initialPatientId,
    document_type: "",
    source_type: "",
    review: initialReview,
    review_status: initialReviewStatus,
  });
  const [filterPatientSearch, setFilterPatientSearch] = useState("");
  const [filterPatient, setFilterPatient] = useState<Patient | null>(null);
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [showQuickPatient, setShowQuickPatient] = useState(false);
  const [draft, setDraft] = useState({
    title: "",
    source_type: "uploaded",
    document_type: "other",
    origin: "Uploaded by patient",
    document_date: "",
    institution: "",
    author: "",
    attachment_name: "",
    raw_text: "",
  });

  const debouncedQuery = useDebouncedValue(filter.q);
  const filterPatientResults = useApi<Patient[]>(
    filterPatientSearch.trim().length >= 2 && !filterPatient
      ? `/api/patients?q=${encodeURIComponent(filterPatientSearch.trim())}`
      : null,
    [],
  );
  const patientResults = useApi<Patient[]>(
    patientSearch.trim().length >= 2 && !selectedPatient
      ? `/api/patients?q=${encodeURIComponent(patientSearch.trim())}`
      : null,
    [],
  );

  useEffect(() => {
    async function loadInitialPatient() {
      if (!initialPatientId) return;
      const patient = await api<Patient>(`/api/patients/${initialPatientId}`);
      setFilterPatient(patient);
      setFilterPatientSearch(formatPatientName(patient));
      setSelectedPatient(patient);
      setPatientSearch(formatPatientName(patient));
    }
    loadInitialPatient();
  }, [initialPatientId]);

  const query = useMemo(() => {
    const next = new URLSearchParams();
    if (debouncedQuery.trim()) next.set("q", debouncedQuery.trim());
    if (filter.patient_id.trim()) next.set("patient_id", filter.patient_id.trim());
    if (filter.document_type) next.set("document_type", filter.document_type);
    if (filter.source_type) next.set("source_type", filter.source_type);
    if (filter.review) next.set("physician_reviewed", filter.review);
    if (filter.review_status) next.set("review_status", filter.review_status);
    return `/api/clinical-documents${next.toString() ? `?${next.toString()}` : ""}`;
  }, [debouncedQuery, filter.document_type, filter.patient_id, filter.review, filter.review_status, filter.source_type]);
  const documents = useApi<ClinicalDocument[]>(query, []);

  const activeFilters = [
    filter.q && `Pretraga: ${filter.q}`,
    filterPatient && `Pacijent: ${formatPatientName(filterPatient)}`,
    filter.document_type && `Tip: ${documentTypeLabel(filter.document_type)}`,
    filter.review_status && `Status: ${reviewStatusLabel(filter.review_status as ClinicalDocument["review_status"])}`,
    filter.review && `Liječnički pregled: ${filter.review === "true" ? "da" : "ne"}`,
    filter.source_type && `Izvor: ${sourceTypeLabel(filter.source_type)}`,
  ].filter(Boolean) as string[];

  function clearFilters() {
    setFilter({ q: "", patient_id: "", document_type: "", source_type: "", review: "", review_status: "" });
    setFilterPatient(null);
    setFilterPatientSearch("");
  }

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
        raw_text: draft.raw_text || null,
      }),
    });
    documents.setData([created, ...documents.data]);
    setShowUpload(false);
  }

  return (
    <section className="page operational-list-page">
      <ListPageHeader
        eyebrow="Klinička dokumentacija"
        title="Klinički dokumenti"
        description="Pronađite dokument, provjerite njegov status i otvorite samo detalj koji trebate."
        action={(
          <ActionButton variant="create" className="primary" onClick={() => setShowUpload(true)} helpTitle="Dodaj dokument" help="Dodaje dokument ili OCR placeholder. Ne unosite stvarne pacijentove podatke u demo okruženju.">
            Dodaj dokument
          </ActionButton>
        )}
      />
      <div className="operational-list-help">
        <HelpHint title="Izvor ostaje izvor istine">AI sažetak ne zamjenjuje izvorni dokument i zahtijeva liječnički pregled.</HelpHint>
      </div>

      <ListFilterBar
        activeFilterCount={filter.source_type ? 1 : 0}
        showClear={activeFilters.length > 0}
        onClear={clearFilters}
        advanced={(
          <label>
            Izvor
            <select aria-label="Izvor dokumenta" value={filter.source_type} onChange={(event) => setFilter({ ...filter, source_type: event.target.value })}>
              <option value="">Svi izvori</option>
              {sourceTypes.map((type) => <option key={type} value={type}>{sourceTypeLabel(type)}</option>)}
            </select>
          </label>
        )}
      >
        <input aria-label="Pretraži dokumente" placeholder="Pretraži dokumente" value={filter.q} onChange={(event) => setFilter({ ...filter, q: event.target.value })} />
        <div className="operational-patient-filter">
          <input
            aria-label="Pacijent"
            placeholder="Pacijent"
            value={filterPatientSearch}
            onChange={(event) => {
              setFilterPatientSearch(event.target.value);
              setFilterPatient(null);
              setFilter({ ...filter, patient_id: "" });
            }}
          />
          {!filterPatient && filterPatientSearch.trim().length >= 2 && (
            <div className="operational-patient-results" role="listbox" aria-label="Rezultati pretrage pacijenata">
              {filterPatientResults.data.slice(0, 5).map((patient) => (
                <button
                  type="button"
                  role="option"
                  aria-selected="false"
                  key={patient.id}
                  onClick={() => {
                    setFilterPatient(patient);
                    setFilterPatientSearch(formatPatientName(patient));
                    setFilter({ ...filter, patient_id: String(patient.id) });
                  }}
                >
                  {formatPatientName(patient)}
                </button>
              ))}
              {!filterPatientResults.loading && filterPatientResults.data.length === 0 && <span>Nema pronađenih pacijenata.</span>}
            </div>
          )}
        </div>
        <select aria-label="Tip dokumenta" value={filter.document_type} onChange={(event) => setFilter({ ...filter, document_type: event.target.value })}>
          <option value="">Svi tipovi</option>
          {documentTypes.map((type) => <option key={type} value={type}>{documentTypeLabel(type)}</option>)}
        </select>
        <select aria-label="Status pregleda" value={filter.review_status} onChange={(event) => setFilter({ ...filter, review_status: event.target.value, review: "" })}>
          <option value="">Svi statusi</option>
          <option value="draft">Izvor zaprimljen</option>
          <option value="needs_physician_review">Čeka liječnički pregled</option>
          <option value="reviewed">Pregledano</option>
          <option value="signed">Potpisano</option>
          <option value="rejected">Odbijeno</option>
          <option value="superseded">Zamijenjeno</option>
        </select>
      </ListFilterBar>

      {activeFilters.length > 0 && (
        <div className="active-filter-chips" aria-label="Aktivni filtri">
          {activeFilters.map((label) => <span key={label}>{label}</span>)}
        </div>
      )}

      {showUpload && (
        <form className="form-grid" onSubmit={upload}>
          <label className="wide-field">Pacijent
            <input placeholder="Pretraga po imenu, OIB-u, telefonu ili e-pošti" value={patientSearch} onChange={(event) => { setPatientSearch(event.target.value); setSelectedPatient(null); }} />
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
              {patientSearch.trim().length >= 2 && !patientResults.loading && patientResults.data.length === 0 && (
                <div className="patient-not-found">
                  <p>Nema pronađenih pacijenata.</p>
                  <button type="button" className="primary" onClick={() => setShowQuickPatient(true)}>Dodaj pacijenta</button>
                </div>
              )}
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
          <ActionButton type="submit" className="primary" variant="create" disabled={!selectedPatient} helpTitle="Spremi dokument" help="Sprema metapodatke i tekst. OCR engine još nije implementiran; ovo je placeholder arhitektura.">
            Spremi dokument
          </ActionButton>
        </form>
      )}
      {showQuickPatient && <QuickPatientModal initialQuery={patientSearch} onClose={() => setShowQuickPatient(false)} onCreated={(patient) => { setSelectedPatient(patient); setPatientSearch(formatPatientName(patient)); patientResults.setData([patient]); setShowQuickPatient(false); }} />}

      <div aria-live="polite">
        {documents.loading ? (
          <p className="operational-list-loading">Učitavanje dokumenata…</p>
        ) : documents.status === 403 ? (
          <EmptyState kind="forbidden" description="Vaša uloga nema pristup kliničkim dokumentima u aktivnom opsegu." />
        ) : documents.error ? (
          <EmptyState kind="unavailable" description={documents.error} />
        ) : documents.data.length === 0 ? (
          <EmptyState kind={activeFilters.length > 0 ? "filtered" : "empty"} title={activeFilters.length > 0 ? undefined : "Nema dokumenata"} />
        ) : (
          <DataTable ariaLabel="Klinički dokumenti" rows={documents.data} columns={[
            {
              header: "Pacijent",
              render: (row) => row.patient
                ? <Link to={`/patients/${row.patient_id}`}>{formatPatientName(row.patient)}</Link>
                : <span className="missing-operational-identity">Pacijent nije dostupan</span>,
            },
            {
              header: "Dokument",
              render: (row) => (
                <span className="document-list-title">
                  <strong>{row.title}</strong>
                  {row.origin && <small>{row.origin}</small>}
                </span>
              ),
            },
            { header: "Datum", render: (row) => formatDate(row.document_date) },
            { header: "Tip", render: (row) => documentTypeLabel(row.document_type) },
            {
              header: "Status",
              render: (row) => {
                const status = documentOperationalStatus(row);
                return <StatusSummary {...status} />;
              },
            },
            {
              header: "Radnja",
              render: (row) => <Link className="action-button" to={`/clinical-documents/${row.id}`}>{documentPrimaryAction(row)}</Link>,
            },
          ]} />
        )}
      </div>
    </section>
  );
}
