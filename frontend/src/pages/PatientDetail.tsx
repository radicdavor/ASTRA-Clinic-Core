import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { AuditTimeline } from "../components/AuditTimeline";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { SourceBadge } from "../components/SourceBadge";
import { StatusBadge } from "../components/StatusBadge";
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader";
import { WorkspaceLayout } from "../components/workspace/WorkspaceLayout";
import { WorkspaceSection } from "../components/workspace/WorkspaceSection";
import { WorkspaceTabs } from "../components/workspace/WorkspaceTabs";
import { useApi } from "../hooks/useApi";
import { Appointment, AuditLog, ClinicalDocument, ClinicalEvidenceTimelineEventPreview, ClinicalEvidenceTimelineListResponse, ClinicalFindingListResponse, ClinicalFindingReadItem, Invoice, Patient, PatientClinicalSummary, PatientClinicalSummaryRecord, PatientKnowledgeItem } from "../types";
import { formatDate, formatDateTime } from "../utils/date";
import { formatPatientIdentity, formatPatientName } from "../utils/patientIdentity";
import { aiExtractionStatusLabel, documentTypeLabel, reviewStatusLabel, sourceTypeLabel } from "./ClinicalDocuments";

function KnowledgeCard({ title, items, help, emphasizeAttention = false }: { title: string; items: PatientKnowledgeItem[]; help?: string; emphasizeAttention?: boolean }) {
  return (
    <article className={`knowledge-card ${emphasizeAttention ? "ai-suggestion" : ""}`}>
      <h3>{title}</h3>
      {help && <p>{help}</p>}
      {items.length === 0 ? <p>Nema pregledanih stavki.</p> : (
        <ul>
          {items.map((item, index) => (
            <li key={`${title}-${index}`}>
              {item.requires_attention && <strong>{item.severity === "warning" ? "Zahtijeva paznju: " : ""}</strong>}
              {item.text}
              <small>{item.sources.map((source) => <SourceBadge key={`${source.document_id}-${item.text}`} source={source} />)}</small>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function KnowledgeList({ title, items }: { title: string; items: string[] }) {
  return (
    <article className="knowledge-card">
      <h3>{title}</h3>
      {items.length === 0 ? <p>Nema stavki.</p> : <ul>{items.map((item) => <li key={`${title}-${item}`}>{item}</li>)}</ul>}
    </article>
  );
}

function summaryStatusLabel(status?: PatientClinicalSummaryRecord["status"]) {
  const labels: Record<PatientClinicalSummaryRecord["status"], string> = {
    draft_ai: "AI draft",
    needs_review: "Ceka pregled",
    reviewed: "Pregledano",
    stale: "Zastarjelo",
    rejected: "Odbijeno",
    superseded: "Zamijenjeno"
  };
  return status ? labels[status] : "Nema sazetka";
}

function findingLifecycleStatusLabel(status: ClinicalFindingReadItem["lifecycle_status"]) {
  const labels: Record<string, string> = {
    received: "Zaprimljeno",
    linked_to_patient: "Povezano s pacijentom",
    awaiting_review: "Ceka pregled",
    review_in_progress: "Pregled u tijeku",
    reviewed: "Pregledano",
    needs_clinician_decision: "Potrebna odluka lijecnika",
    decision_documented: "Odluka dokumentirana",
    follow_up_recommended: "Preporuceno pracenje",
    external_referral_recommended: "Preporucena vanjska obrada",
    closed_for_now: "Zatvoreno za sada"
  };
  return labels[status] ?? status;
}

function FindingsReadOnlyPanel({ findings, loading, error }: { findings: ClinicalFindingListResponse; loading: boolean; error: string | null }) {
  const permissionDenied = error?.toLowerCase().includes("dozvola") || error?.includes("403");

  return (
    <WorkspaceSection title="Nalazi povezani s izvorom">
      <section aria-label="Nalazi povezani s izvorom" aria-live="polite" className="clinical-plan-card">
        <p>Ovo su source-linked zapisi za pregled.</p>
        <p>Nalaz nije dijagnoza bez lijecnicke potvrde.</p>
        <p>Ovaj prikaz ne stvara zadatak i ne salje poruku pacijentu.</p>
        <p>Za klinicku interpretaciju odgovoran je lijecnik.</p>
        {loading && <p role="status">Ucitavanje nalaza povezanih s izvorom...</p>}
        {error && (
          <p role="status">
            {permissionDenied
              ? "Nemate dozvolu za prikaz source-linked nalaza. Ovo ne mijenja status pacijenta ili termina. Ostali podaci ostaju dostupni prema vasim dozvolama."
              : "Nalazi trenutno nisu dostupni. To ne znaci da nema otvorenih klinickih pitanja. Pokusajte ponovno ili provjerite izvorne dokumente."}
          </p>
        )}
        {!loading && !error && findings.findings.length === 0 && (
          <p>Nema prikazanih source-linked finding zapisa. To ne znaci da nema klinickih rizika, da su svi dokumenti pregledani, da je pacijent klinicki rijesen ili da je plan skrbi dovrsen.</p>
        )}
        {!loading && !error && findings.findings.length > 0 && (
          <ul aria-label="Source-linked findings zapisi">
            {findings.findings.map((finding: ClinicalFindingReadItem) => {
              const sourceReference = finding.source_reference.trim() || "Izvor nije dovoljno specificiran - provjeriti originalni dokument.";
              return (
                <li key={finding.id}>
                  <strong>{finding.label}</strong>
                  <small>{finding.category} / {findingLifecycleStatusLabel(finding.lifecycle_status)} / {finding.requires_review ? "Za ljudski pregled" : "Pregled nije oznacen kao obavezan"}</small>
                  <small>Status nije automatska dijagnoza, obavijest pacijentu ili zadatak.</small>
                  <dl>
                    <dt>Tip izvora</dt>
                    <dd>{finding.source_type || "Izvor nije dovoljno specificiran - provjeriti originalni dokument."}</dd>
                    <dt>Oznaka izvora</dt>
                    <dd>{finding.source_label || "Izvor nije dovoljno specificiran - provjeriti originalni dokument."}</dd>
                    <dt>Referenca izvora</dt>
                    <dd>{sourceReference}</dd>
                    <dt>Ogranicenja</dt>
                    <dd>{finding.limitations.length > 0 ? finding.limitations.join(" ") : "Ogranicenja nisu navedena - provjeriti originalni dokument."}</dd>
                  </dl>
                  <small>{finding.safe_disclaimer}</small>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </WorkspaceSection>
  );
}

function timelineEventTypeLabel(eventType: string) {
  const labels: Record<string, string> = {
    clinical_document_received: "Dokument zaprimljen",
    clinical_document_review_pending: "Dokument ceka pregled",
    finding_recorded: "Nalaz zabiljezen",
    finding_requires_review: "Nalaz ceka pregled",
    open_question_suggested: "Otvoreno pitanje predlozeno",
    open_question_awaiting_review: "Otvoreno pitanje ceka pregled",
    extraction_candidate_generated: "Extraction candidate generiran",
    review_pending: "Pregled ceka",
    review_completed: "Pregled evidentiran",
    readiness_snapshot_captured: "Snapshot spremnosti spremljen",
    readiness_snapshot_superseded: "Snapshot spremnosti zamijenjen novijim zapisom",
    acknowledgment_recorded: "Ljudski pregled signala evidentiran",
    access_audit_recorded: "Access audit evidentiran"
  };
  return labels[eventType] ?? eventType;
}

function TimelineReadOnlyPanel({ timeline, loading, error }: { timeline: ClinicalEvidenceTimelineListResponse; loading: boolean; error: string | null }) {
  const permissionDenied = error?.toLowerCase().includes("dozvola") || error?.includes("403");

  return (
    <WorkspaceSection title="Klinicka vremenska crta">
      <section aria-label="Klinicka vremenska crta" aria-live="polite" className="clinical-plan-card">
        <p>Source-linked prikaz klinickih dogadjaja.</p>
        <p>Nije klinicka odluka, ne stvara zadatak i ne salje poruku pacijentu.</p>
        <p>Ne mijenja status termina.</p>
        {loading && <p role="status">Ucitavanje klinicke vremenske crte...</p>}
        {error && (
          <p role="status">
            {permissionDenied
              ? "Nemate dozvolu za prikaz klinicke vremenske crte. To ne mijenja status pacijenta ili termina."
              : "Klinicka vremenska crta trenutno nije dostupna. To ne znaci da je klinicka spremnost potvrdjena ili odbijena."}
          </p>
        )}
        {!loading && !error && timeline.events.length === 0 && (
          <p>Nema prikazanih source-linked timeline dogadjaja. To ne znaci da nema klinickih rizika, da su svi dokumenti pregledani ili da je pacijent klinicki rijesen.</p>
        )}
        {!loading && !error && timeline.events.length > 0 && (
          <ul aria-label="Source-linked timeline dogadjaji">
            {timeline.events.map((event: ClinicalEvidenceTimelineEventPreview) => {
              const source = event.source_reference;
              const sourceReference = source.source_object_reference?.trim() || "Izvor nije dovoljno specificiran - provjeriti originalni zapis.";
              const sourceLabel = source.source_label?.trim() || "Izvor nije dovoljno specificiran - provjeriti originalni zapis.";
              const limitations = [...event.limitations, ...source.limitations].filter(Boolean);
              return (
                <li key={event.event_key}>
                  <strong>{event.label}</strong>
                  <small>{timelineEventTypeLabel(event.event_type)} / {event.requires_review ? "Ceka pregled" : "Read-only zapis"}</small>
                  <small>{formatDateTime(event.display_timestamp)}</small>
                  <dl>
                    <dt>Tip izvora</dt>
                    <dd>{source.source_object_type || "Izvor nije dovoljno specificiran - provjeriti originalni zapis."}</dd>
                    <dt>Oznaka izvora</dt>
                    <dd>{sourceLabel}</dd>
                    <dt>Referenca izvora</dt>
                    <dd>{sourceReference}</dd>
                    <dt>Provenance</dt>
                    <dd>{source.provenance_label || "Povezano s izvorom"}</dd>
                    <dt>Ogranicenja</dt>
                    <dd>{limitations.length > 0 ? limitations.join(" ") : "Ogranicenja nisu navedena - provjeriti originalni zapis."}</dd>
                  </dl>
                  <small>{event.no_decision_disclaimer}</small>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </WorkspaceSection>
  );
}

export function PatientDetail() {
  const { id } = useParams();
  const patient = useApi<Patient | null>(`/api/patients/${id}`, null);
  const documents = useApi<ClinicalDocument[]>(`/api/patients/${id}/clinical-documents`, []);
  const clinicalSummary = useApi<PatientClinicalSummary | null>(`/api/patients/${id}/clinical-summary`, null);
  const clinicalFindings = useApi<ClinicalFindingListResponse>(`/api/patients/${id}/clinical-findings`, { patient_id: Number(id), findings: [], count: 0, is_read_only: true, warning: "" });
  const clinicalTimeline = useApi<ClinicalEvidenceTimelineListResponse>(`/api/patients/${id}/clinical-evidence-timeline`, { patient_id: Number(id), events: [], count: 0, is_read_only: true, warning: "" });
  const appointments = useApi<Appointment[]>(`/api/patients/${id}/appointments`, []);
  const invoices = useApi<Invoice[]>(`/api/patients/${id}/invoices`, []);
  const audit = useApi<AuditLog[]>(`/api/audit-log?entity_type=Patient&entity_id=${id}`, []);
  const duplicatePath = patient.data?.first_name && patient.data?.last_name
    ? `/api/patients/possible-duplicates?first_name=${encodeURIComponent(patient.data.first_name)}&last_name=${encodeURIComponent(patient.data.last_name)}${patient.data.date_of_birth ? `&date_of_birth=${patient.data.date_of_birth}` : ""}${patient.data.oib ? `&oib=${patient.data.oib}` : ""}`
    : "/api/patients/possible-duplicates";
  const duplicates = useApi<Patient[]>(duplicatePath, []);
  const duplicateCandidates = duplicates.data.filter((candidate) => candidate.id !== patient.data?.id);
  const sortedAppointments = [...appointments.data].sort((a, b) => `${a.date}T${a.start_time}`.localeCompare(`${b.date}T${b.start_time}`));
  const today = new Date().toISOString().slice(0, 10);
  const lastAppointment = [...sortedAppointments].reverse().find((appointment) => appointment.date <= today);
  const nextAppointment = sortedAppointments.find((appointment) => appointment.date >= today && !["completed", "cancelled", "no_show"].includes(appointment.status));
  const reviewedDocuments = documents.data.filter((document) => document.physician_reviewed && document.review_status === "reviewed");
  const awaitingReview = documents.data.filter((document) => ["extracted", "needs_physician_review"].includes(document.review_status));
  const internalDocuments = documents.data.filter((document) => document.source_type === "internal");
  const externalDocuments = documents.data.filter((document) => ["external", "uploaded", "scanned"].includes(document.source_type));
  const procedures = documents.data.filter((document) => ["gastroscopy", "colonoscopy"].includes(document.document_type));
  const pathology = documents.data.filter((document) => document.document_type === "pathology");
  const laboratory = documents.data.filter((document) => document.document_type === "laboratory");
  const imaging = documents.data.filter((document) => document.document_type === "radiology");
  const openInvoices = invoices.data.filter((invoice) => invoice.payment_status !== "paid");
  const unpaidTotal = openInvoices.reduce((sum, invoice) => sum + Number(invoice.total_amount || 0), 0);
  const knownItemCount = clinicalSummary.data
    ? clinicalSummary.data.known_problems.length
      + clinicalSummary.data.completed_procedures.length
      + clinicalSummary.data.pathology.length
      + clinicalSummary.data.laboratory.length
      + clinicalSummary.data.imaging.length
      + clinicalSummary.data.current_therapy.length
      + clinicalSummary.data.latest_recommendations.length
    : 0;
  const openQuestionCount = clinicalSummary.data?.open_questions.length ?? 0;
  const hasReviewedKnowledge = (clinicalSummary.data?.generated_from_reviewed_documents ?? 0) > 0;
  const activeSummary = clinicalSummary.data?.reviewed_summary ?? clinicalSummary.data?.draft_summary ?? null;
  const activeSummaryIsReviewed = Boolean(clinicalSummary.data?.reviewed_summary);
  const activeSummaryIsStale = activeSummaryIsReviewed ? clinicalSummary.data?.reviewed_summary_is_stale : clinicalSummary.data?.draft_summary_is_stale;
  const activeSummaryTitle = activeSummaryIsReviewed ? "Pregledani sazetak pacijenta" : "AI draft sazetka";
  const sourceDocuments = documents.data.filter((document) => activeSummary?.source_document_ids?.includes(document.id));
  const openQuestions = clinicalSummary.data?.open_questions ?? [];

  async function refreshClinicalSummary() {
    clinicalSummary.setData(await api<PatientClinicalSummary>(`/api/patients/${id}/clinical-summary`));
  }

  async function generateSummaryDraft() {
    await api(`/api/patients/${id}/clinical-summary/generate-draft`, { method: "POST" });
    await refreshClinicalSummary();
  }

  async function confirmSummary() {
    await api(`/api/patients/${id}/clinical-summary/review`, { method: "POST" });
    await refreshClinicalSummary();
  }

  const documentColumns = [
    { header: "Dokument", render: (row: ClinicalDocument) => <Link to={`/clinical-documents/${row.id}`}>{row.title}</Link> },
    { header: "Datum", render: (row: ClinicalDocument) => formatDate(row.document_date) },
    { header: "Tip", render: (row: ClinicalDocument) => documentTypeLabel(row.document_type) },
    { header: "Izvor", render: (row: ClinicalDocument) => sourceTypeLabel(row.source_type) },
    { header: "Pregled", render: (row: ClinicalDocument) => reviewStatusLabel(row.review_status) },
    { header: "AI", render: (row: ClinicalDocument) => aiExtractionStatusLabel(row.ai_extraction_status) }
  ];

  if (patient.loading || !patient.data) {
    return <WorkspaceLayout><p>Ucitavanje pacijenta...</p></WorkspaceLayout>;
  }

  return (
    <WorkspaceLayout>
      <WorkspaceHeader
        title={formatPatientName(patient.data)}
        subtitle={formatPatientIdentity(patient.data)}
        badge={<span className="readiness-badge readiness-check-ok">Patient Workspace</span>}
        actions={
          <>
            <ActionButton
              variant="create"
              className="primary"
              onClick={() => { window.location.href = `/clinical-documents?patient_id=${patient.data?.id}`; }}
              helpTitle="Dodaj dokument"
              help="Dodaje interni ili vanjski dokument u pacijentov sloj klinickog znanja. AI sazetak mora biti pregledan prije ulaska u sazetak."
            >
              Dodaj dokument
            </ActionButton>
            <ActionButton
              variant="create"
              onClick={() => { window.location.href = `/appointments/new?patient_id=${patient.data?.id}`; }}
              helpTitle="Novi termin"
              help="Otvara unos termina iz konteksta odabranog pacijenta. Termin se i dalje sprema samo s razrijesenim patient_id."
            >
              Novi termin
            </ActionButton>
          </>
        }
      />

      {duplicateCandidates.length > 0 && (
        <div className="duplicate-warning">
          <strong>Moguci duplikati pacijenta</strong>
          <p>Provjerite identitet prije novog narucivanja ili izmjene podataka.</p>
          {duplicateCandidates.map((candidate) => (
            <span key={candidate.id}>
              <Link to={`/patients/${candidate.id}`}>{formatPatientName(candidate)}</Link>
              <small>{formatPatientIdentity(candidate)}</small>
            </span>
          ))}
        </div>
      )}

      <div className="summary-strip">
        <div><span>Pregledani dokumenti</span><strong>{reviewedDocuments.length}</strong></div>
        <div><span>Ceka pregled</span><strong>{awaitingReview.length}</strong></div>
        <div><span>Zadnji termin</span><strong>{lastAppointment ? `${formatDate(lastAppointment.date)} / ${lastAppointment.status}` : "-"}</strong></div>
        <div><span>Sljedeci termin</span><strong>{nextAppointment ? `${formatDate(nextAppointment.date)} / ${nextAppointment.status}` : "-"}</strong></div>
        <div><span>Otvoreni racuni</span><strong>{openInvoices.length ? `${openInvoices.length} / ${unpaidTotal.toFixed(2)} EUR` : "Nema"}</strong></div>
      </div>

      <div className="metrics">
        <div><span>Klinicki dokumenti</span><strong>{documents.data.length}</strong></div>
        <div><span>Termini</span><strong>{appointments.data.length}</strong></div>
        <div><span>Racuni</span><strong>{invoices.data.length}</strong></div>
        <div><span>Audit zapisi</span><strong>{audit.data.length}</strong></div>
      </div>

      <WorkspaceSection
        title={
          <>
            Identitet <HelpHint title="Identitet pacijenta">Pacijent se razlikuje po imenu, prezimenu, datumu rodenja, OIB-u, telefonu i e-posti.</HelpHint>
          </>
        }
      >
        <div className="detail-list">
          <p><span>Datum rodenja</span><strong>{formatDate(patient.data.date_of_birth)}</strong></p>
          <p><span>OIB</span><strong>{patient.data.oib ?? "-"}</strong></p>
          <p><span>Telefon</span><strong>{patient.data.phone ?? "-"}</strong></p>
          <p><span>E-posta</span><strong>{patient.data.email ?? "-"}</strong></p>
          <p><span>Napomene</span><strong>{patient.data.notes ?? "-"}</strong></p>
        </div>
      </WorkspaceSection>

      <div className="patient-knowledge-layout">
        <div>
          <WorkspaceSection title={<>{activeSummaryTitle} <HelpHint title="Sazetak pacijenta">Sazetak je pomocni prikaz i nije izvor istine. Izvor istine su pregledani, source-linked klinicki dokumenti.</HelpHint></>}>
            <div className={`clinical-plan-card ${activeSummary?.status === "reviewed" && !activeSummaryIsStale ? "" : "ai-suggestion"}`}>
              <div><span>Status</span><strong>{summaryStatusLabel(activeSummary?.status)}</strong></div>
              {activeSummaryIsStale && <p><strong>Sazetak je zastario. Generirajte novi draft iz najnovijih pregledanih dokumenata.</strong></p>}
              {clinicalSummary.data?.summary_warning && <p>{clinicalSummary.data.summary_warning}</p>}
              {activeSummary?.status !== "reviewed" && <p><strong>AI draft - potreban je lijecnicki pregled.</strong></p>}
              <p>Sazetak je pomocni prikaz. Izvor istine su pregledani, source-linked klinicki dokumenti.</p>
              <p>{activeSummary?.summary_text ?? "Nema potvrdjenog sazetka pacijenta. Generirajte draft iz pregledanih dokumenata."}</p>
              <div className="knowledge-grid">
                <KnowledgeList title="Poznata stanja" items={activeSummary?.known_conditions ?? []} />
                <KnowledgeList title="Kljucni nalazi" items={activeSummary?.key_findings ?? []} />
                <KnowledgeList title="Otvorene stavke" items={activeSummary?.open_items ?? []} />
                <KnowledgeList title="Rizici" items={activeSummary?.risks ?? []} />
                <KnowledgeList title="Zadnje preporuke" items={activeSummary?.last_recommendations ?? []} />
              </div>
              {activeSummary?.reviewed_at && <p><span>Pregledano</span><strong>{formatDateTime(activeSummary.reviewed_at)}</strong></p>}
              {clinicalSummary.data?.latest_reviewed_document_updated_at && <p><span>Zadnji pregledani izvor</span><strong>{formatDateTime(clinicalSummary.data.latest_reviewed_document_updated_at)}</strong></p>}
              {sourceDocuments.length > 0 && (
                <p>
                  <span>Izvori</span>
                  <strong className="source-link-list">{sourceDocuments.map((document) => <Link key={document.id} to={`/clinical-documents/${document.id}`}>{document.title}</Link>)}</strong>
                </p>
              )}
              <div className="quick-actions">
                <ActionButton variant="ai" onClick={generateSummaryDraft} helpTitle="Generiraj draft" help="Stvara AI placeholder draft iz pregledanih dokumenata. Ne postaje sluzben bez lijecnicke potvrde.">
                  Generiraj draft
                </ActionButton>
                <ActionButton variant="update" onClick={confirmSummary} helpTitle="Potvrdi sazetak" help="Potvrdjuje zadnji draft sazetka kao lijecnicki pregledan. Izvori ostaju vidljivi.">
                  Potvrdi sazetak
                </ActionButton>
              </div>
            </div>
          </WorkspaceSection>
          <FindingsReadOnlyPanel findings={clinicalFindings.data} loading={clinicalFindings.loading} error={clinicalFindings.error} />
          <TimelineReadOnlyPanel timeline={clinicalTimeline.data} loading={clinicalTimeline.loading} error={clinicalTimeline.error} />
          <WorkspaceTabs
            tabs={[
              {
                id: "summary",
                label: "Sazetak",
                content: (
                  <>
                    <p><strong>Sluzbeno source-linked znanje</strong> dolazi iz pregledanih dokumenata i uvijek ima izvore.</p>
                    <div className="knowledge-grid">
                      <KnowledgeCard title="Poznati problemi" items={clinicalSummary.data?.known_problems ?? []} />
                      <KnowledgeCard title="Zavrseni postupci" items={clinicalSummary.data?.completed_procedures ?? []} />
                      <KnowledgeCard title="Patologija" items={clinicalSummary.data?.pathology ?? []} />
                      <KnowledgeCard title="Laboratorij" items={clinicalSummary.data?.laboratory ?? []} />
                      <KnowledgeCard title="Radiologija" items={clinicalSummary.data?.imaging ?? []} />
                      <KnowledgeCard title="Terapija" items={clinicalSummary.data?.current_therapy ?? []} />
                      <KnowledgeCard title="Zadnje preporuke" items={clinicalSummary.data?.latest_recommendations ?? []} />
                    </div>
                    <WorkspaceSection title={<>{`Otvorena pitanja`} <HelpHint title="Otvorena pitanja">Ovo su pregledane, source-linked stavke koje zahtijevaju klinicku paznju. Nisu automatske odluke niti zadaci.</HelpHint></>}>
                      <KnowledgeCard
                        title="Otvorena pitanja"
                        items={openQuestions}
                        emphasizeAttention
                        help="Ovo su pregledane, source-linked stavke koje zahtijevaju klinicku paznju. Nisu automatske odluke niti zadaci."
                      />
                    </WorkspaceSection>
                  </>
                )
              },
              { id: "internal-documents", label: "Interni dokumenti", content: <DataTable rows={internalDocuments} columns={documentColumns} /> },
              { id: "external-documents", label: "Vanjski dokumenti", content: <DataTable rows={externalDocuments} columns={documentColumns} /> },
              { id: "procedures", label: "Postupci", content: <DataTable rows={procedures} columns={documentColumns} /> },
              { id: "pathology", label: "Patologija", content: <DataTable rows={pathology} columns={documentColumns} /> },
              { id: "laboratory", label: "Laboratorij", content: <DataTable rows={laboratory} columns={documentColumns} /> },
              { id: "imaging", label: "Slikovna obrada", content: <DataTable rows={imaging} columns={documentColumns} /> },
              {
                id: "appointments",
                label: "Termini",
                content: (
                  <DataTable rows={appointments.data} columns={[
                    { header: "Datum", render: (row) => formatDate(row.date) },
                    { header: "Vrijeme", render: (row) => `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}` },
                    { header: "Usluga", render: (row) => row.service?.name ?? row.service_id },
                    { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
                    { header: "Detalj", render: (row) => <Link to={`/appointments/${row.id}`}>Otvori</Link> }
                  ]} />
                )
              },
              {
                id: "invoices",
                label: "Racuni",
                content: (
                  <DataTable rows={invoices.data} columns={[
                    { header: "Broj", render: (row) => <Link to={`/invoices?invoice=${row.id}`}>{row.invoice_number}</Link> },
                    { header: "Datum", render: (row) => formatDate(row.invoice_date) },
                    { header: "Status", render: (row) => row.status },
                    { header: "Placanje", render: (row) => row.payment_status },
                    { header: "Iznos", render: (row) => `${row.total_amount} EUR` }
                  ]} />
                )
              },
              {
                id: "audit",
                label: "Audit",
                content: <AuditTimeline logs={audit.data} />
              }
            ]}
          />
        </div>
        <aside className="knowledge-sidebar">
          <h2>Klinicko znanje</h2>
          <div><span>Pregledani izvori</span><strong>{clinicalSummary.data?.generated_from_reviewed_documents ?? 0}</strong></div>
          <div><span>Strukturirane stavke</span><strong>{knownItemCount}</strong></div>
          <div><span>Otvorena pitanja</span><strong>{openQuestionCount}</strong></div>
          <div><span>Dokumenti cekaju lijecnicki pregled</span><strong>{clinicalSummary.data?.awaiting_review_count ?? awaitingReview.length}</strong></div>
          {!hasReviewedKnowledge && (
            <section>
              <h3>Nema pregledanih dokumenata</h3>
              <p>Sluzbeni sazetak nastaje tek nakon lijecnickog pregleda dokumenta.</p>
              {awaitingReview.length > 0 && <p>Postoje dokumenti koji cekaju lijecnicki pregled.</p>}
              <Link to={`/clinical-documents?patient_id=${patient.data.id}`}>Dodaj dokument</Link>
            </section>
          )}
          {awaitingReview.length > 0 && (
            <section>
              <h3>Dokumenti cekaju lijecnicki pregled</h3>
              {awaitingReview.slice(0, 4).map((document) => (
                <Link key={document.id} to={`/clinical-documents/${document.id}`}>{document.title}</Link>
              ))}
            </section>
          )}
          {openQuestions.length > 0 && (
            <section>
              <h3>Otvorena pitanja</h3>
              <p>Nisu zadaci niti odluke; potrebno je pregledati izvore.</p>
              {openQuestions.slice(0, 3).map((item, index) => (
                <p key={index}>
                  {item.requires_attention && <strong>Upozorenje: </strong>}
                  {item.text}
                  <small>{item.sources.map((source) => <SourceBadge key={`${source.document_id}-${item.text}`} source={source} />)}</small>
                </p>
              ))}
            </section>
          )}
        </aside>
      </div>
    </WorkspaceLayout>
  );
}
