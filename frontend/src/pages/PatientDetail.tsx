import { useState } from "react";
import { MoreHorizontal } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { AuditTimeline } from "../components/AuditTimeline";
import { ClinicalDerivedDataNotice } from "../components/ClinicalDerivedDataNotice";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { SourceBadge } from "../components/SourceBadge";
import { StatusBadge } from "../components/StatusBadge";
import { WorkflowTaskPanel } from "../components/WorkflowTaskPanel";
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader";
import { WorkspaceLayout } from "../components/workspace/WorkspaceLayout";
import { WorkspaceSection } from "../components/workspace/WorkspaceSection";
import { WorkspaceTabs } from "../components/workspace/WorkspaceTabs";
import { useApi } from "../hooks/useApi";
import {
  AuditLog,
  ClinicalDocument,
  ClinicalEvidenceTimelineListResponse,
  ClinicalFindingListResponse,
  Invoice,
  LabOrder,
  Patient,
  PatientAppointmentAvailability,
  PatientClinicalSummary,
  PatientClinicalSummaryRecord,
  PatientKnowledgeItem,
  Therapy
} from "../types";
import { getClinicToday } from "../utils/clinicTime";
import { formatDate, formatDateTime } from "../utils/date";
import { formatPatientIdentity, formatPatientName } from "../utils/patientIdentity";
import { aiExtractionStatusLabel, documentTypeLabel, reviewStatusLabel, sourceTypeLabel } from "./ClinicalDocuments";

function summaryStatusLabel(status?: PatientClinicalSummaryRecord["status"]) {
  const labels: Record<PatientClinicalSummaryRecord["status"], string> = {
    draft_ai: "AI skica",
    needs_review: "Čeka pregled",
    reviewed: "Pregledano",
    stale: "Zastarjelo",
    rejected: "Odbijeno",
    superseded: "Zamijenjeno"
  };
  return status ? labels[status] : "Nema sažetka";
}

function findingStatusLabel(status: string) {
  const labels: Record<string, string> = {
    received: "Zaprimljeno",
    linked_to_patient: "Povezano s pacijentom",
    awaiting_review: "Čeka pregled",
    review_in_progress: "Pregled u tijeku",
    reviewed: "Pregledano",
    needs_clinician_decision: "Potrebna odluka liječnika",
    decision_documented: "Odluka dokumentirana",
    follow_up_recommended: "Preporučeno praćenje",
    external_referral_recommended: "Preporučena vanjska obrada",
    closed_for_now: "Zatvoreno za sada"
  };
  return labels[status] ?? status;
}

function timelineEventLabel(eventType: string) {
  const labels: Record<string, string> = {
    clinical_document_received: "Dokument zaprimljen",
    clinical_document_review_pending: "Dokument čeka pregled",
    finding_recorded: "Nalaz zabilježen",
    finding_requires_review: "Nalaz čeka pregled",
    open_question_suggested: "Otvoreno pitanje predloženo",
    open_question_awaiting_review: "Otvoreno pitanje čeka pregled",
    extraction_candidate_generated: "Prijedlog ekstrakcije generiran",
    review_pending: "Pregled čeka",
    review_completed: "Pregled evidentiran",
    readiness_snapshot_captured: "Snimka spremnosti spremljena",
    readiness_snapshot_superseded: "Snimka spremnosti zamijenjena",
    acknowledgment_recorded: "Ljudski pregled signala evidentiran",
    access_audit_recorded: "Audit pristupa evidentiran"
  };
  return labels[eventType] ?? eventType;
}

function KnowledgeCard({ title, items, help, emphasizeAttention = false }: {
  title: string;
  items: PatientKnowledgeItem[];
  help?: string;
  emphasizeAttention?: boolean;
}) {
  return (
    <article className={`knowledge-card ${emphasizeAttention ? "ai-suggestion" : ""}`}>
      <h3>{title}</h3>
      {help && <p>{help}</p>}
      {items.length === 0 ? <p>Nema pregledanih stavki.</p> : (
        <ul>
          {items.map((item, index) => (
            <li key={`${title}-${item.text}-${index}`}>
              {item.requires_attention && <strong>{item.severity === "warning" ? "Zahtijeva pažnju: " : ""}</strong>}
              {item.text}
              <small>{item.sources.map((source) => <SourceBadge key={`${source.document_id}-${item.text}`} source={source} />)}</small>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function FindingsPanel({ state }: { state: ReturnType<typeof useApi<ClinicalFindingListResponse>> }) {
  const permissionDenied = state.error?.toLowerCase().includes("dozvola") || state.error?.includes("403");
  return (
    <WorkspaceSection title="Nalazi povezani s izvorima">
      <section aria-live="polite" className="clinical-plan-card">
        {state.loading && <p role="status">Učitavanje nalaza povezanih s izvorima...</p>}
        {state.error && <p role="status">{permissionDenied ? "Nemate dozvolu za prikaz nalaza povezanih s izvorima." : "Nalazi trenutno nisu dostupni. Provjerite izvorne dokumente."}</p>}
        {!state.loading && !state.error && state.data.findings.length === 0 && <p>Nema prikazanih nalaza povezanih s izvorima.</p>}
        {!state.loading && !state.error && state.data.findings.length > 0 && (
          <ul className="patient-source-list">
            {state.data.findings.map((finding) => (
              <li key={finding.id}>
                <strong>{finding.label}</strong>
                <span>{finding.category} · {findingStatusLabel(finding.lifecycle_status)}</span>
                <small>{finding.source_label || finding.source_reference || "Izvor nije dovoljno specificiran — provjerite originalni dokument."}</small>
                {finding.limitations.length > 0 && <small>{finding.limitations.join(" ")}</small>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </WorkspaceSection>
  );
}

function TimelinePanel({ state }: { state: ReturnType<typeof useApi<ClinicalEvidenceTimelineListResponse>> }) {
  const permissionDenied = state.error?.toLowerCase().includes("dozvola") || state.error?.includes("403");
  return (
    <WorkspaceSection title="Klinička vremenska crta">
      <section aria-live="polite" className="clinical-plan-card">
        {state.loading && <p role="status">Učitavanje kliničke vremenske crte...</p>}
        {state.error && <p role="status">{permissionDenied ? "Nemate dozvolu za prikaz kliničke vremenske crte." : "Klinička vremenska crta trenutno nije dostupna."}</p>}
        {!state.loading && !state.error && state.data.events.length === 0 && <p>Nema prikazanih događaja povezanih s izvorima.</p>}
        {!state.loading && !state.error && state.data.events.length > 0 && (
          <ul className="patient-source-list">
            {state.data.events.map((event) => (
              <li key={event.event_key}>
                <strong>{event.label}</strong>
                <span>{timelineEventLabel(event.event_type)} · {formatDateTime(event.display_timestamp)}</span>
                <small>{event.source_reference.source_label || event.source_reference.source_object_reference || "Izvor nije dovoljno specificiran — provjerite originalni zapis."}</small>
                {event.requires_review && <small>Za ljudski pregled</small>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </WorkspaceSection>
  );
}

export function PatientDetail() {
  const { id } = useParams();
  const patientId = Number(id);
  const [activeSection, setActiveSection] = useState("overview");
  const needsDocuments = ["overview", "documents", "care", "evidence"].includes(activeSection);
  const needsSummary = ["overview", "evidence"].includes(activeSection);

  const patient = useApi<Patient | null>(`/api/patients/${id}`, null);
  const documents = useApi<ClinicalDocument[]>(needsDocuments ? `/api/patients/${id}/clinical-documents` : null, []);
  const clinicalSummary = useApi<PatientClinicalSummary | null>(needsSummary ? `/api/patients/${id}/clinical-summary` : null, null);
  const clinicalFindings = useApi<ClinicalFindingListResponse>(activeSection === "evidence" ? `/api/patients/${id}/clinical-findings` : null, { patient_id: patientId, findings: [], count: 0, is_read_only: true, warning: "" });
  const clinicalTimeline = useApi<ClinicalEvidenceTimelineListResponse>(activeSection === "evidence" ? `/api/patients/${id}/clinical-evidence-timeline` : null, { patient_id: patientId, events: [], count: 0, is_read_only: true, warning: "" });
  const appointments = useApi<PatientAppointmentAvailability[]>(`/api/patients/${id}/appointments`, []);
  const invoices = useApi<Invoice[]>(activeSection === "operations" ? `/api/patients/${id}/invoices` : null, []);
  const labOrders = useApi<LabOrder[]>(activeSection === "care" ? `/api/laboratory/orders?patient_id=${id}` : null, []);
  const therapies = useApi<Therapy[]>(activeSection === "care" ? `/api/therapies?patient_id=${id}` : null, []);
  const audit = useApi<AuditLog[]>(activeSection === "evidence" ? `/api/audit-log?entity_type=Patient&entity_id=${id}` : null, []);

  const duplicatePath = patient.data?.first_name && patient.data?.last_name
    ? `/api/patients/possible-duplicates?first_name=${encodeURIComponent(patient.data.first_name)}&last_name=${encodeURIComponent(patient.data.last_name)}${patient.data.date_of_birth ? `&date_of_birth=${patient.data.date_of_birth}` : ""}${patient.data.oib ? `&oib=${patient.data.oib}` : ""}`
    : "/api/patients/possible-duplicates";
  const duplicates = useApi<Patient[]>(duplicatePath, []);
  const duplicateCandidates = duplicates.data.filter((candidate) => candidate.id !== patient.data?.id);

  const sortedAppointments = [...appointments.data].sort((a, b) => `${a.date}T${a.start_time}`.localeCompare(`${b.date}T${b.start_time}`));
  const appointmentRows = appointments.data.map((appointment) => ({ ...appointment, id: appointment.appointment_id }));
  const today = getClinicToday();
  const nextAppointment = sortedAppointments.find((appointment) => appointment.date >= today && !["completed", "cancelled", "no_show"].includes(appointment.status));
  const awaitingReview = documents.data.filter((document) => ["extracted", "needs_physician_review"].includes(document.review_status));
  const laboratoryDocuments = documents.data.filter((document) => document.document_type === "laboratory");
  const openInvoices = invoices.data.filter((invoice) => invoice.payment_status !== "paid");
  const activeSummary = clinicalSummary.data?.reviewed_summary ?? clinicalSummary.data?.draft_summary ?? null;
  const activeSummaryIsReviewed = Boolean(clinicalSummary.data?.reviewed_summary);
  const activeSummaryIsStale = activeSummaryIsReviewed ? clinicalSummary.data?.reviewed_summary_is_stale : clinicalSummary.data?.draft_summary_is_stale;
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
  const labOrderColumns = [
    { header: "Datum", render: (row: LabOrder) => formatDate(row.ordered_at) },
    { header: "Pretrage", render: (row: LabOrder) => row.results.map((result) => result.test_name).join(", ") },
    { header: "Uzorak", render: (row: LabOrder) => row.collected_at ? formatDateTime(row.collected_at) : "Čeka uzimanje" },
    { header: "Status", render: (row: LabOrder) => <StatusBadge status={row.status} /> },
    { header: "Detalj", render: (row: LabOrder) => <Link to={`/laboratory?patient_id=${patient.data?.id}&order_id=${row.id}`}>Otvori</Link> }
  ];

  if (patient.loading || !patient.data) return <WorkspaceLayout><p>Učitavanje pacijenta...</p></WorkspaceLayout>;

  const overview = (
    <div className="patient-overview">
      <section className="patient-identity-card" aria-labelledby="patient-identity-title">
        <div><span className="eyebrow">Identitet</span><h2 id="patient-identity-title">Osnovni podaci</h2></div>
        <dl>
          <div><dt>Datum rođenja</dt><dd>{formatDate(patient.data.date_of_birth)}</dd></div>
          <div><dt>OIB</dt><dd>{patient.data.oib ?? "Nije upisan"}</dd></div>
          <div><dt>Telefon</dt><dd>{patient.data.phone ?? "Nije upisan"}</dd></div>
          <div><dt>E-pošta</dt><dd>{patient.data.email ?? "Nije upisana"}</dd></div>
        </dl>
        {patient.data.notes && <p><strong>Napomena:</strong> {patient.data.notes}</p>}
      </section>

      <section className="patient-current-context" aria-labelledby="patient-current-title">
        <div><span className="eyebrow">Sada je važno</span><h2 id="patient-current-title">Otvorene stavke</h2></div>
        <div className="patient-context-items">
          {nextAppointment && (
            <article>
              <span>Sljedeći termin</span>
              <strong>{formatDate(nextAppointment.date)} u {nextAppointment.start_time.slice(0, 5)}</strong>
              <small>{nextAppointment.service_name ?? "Usluga nije navedena"} · {nextAppointment.clinic.name ?? "Klinika nije navedena"}</small>
            </article>
          )}
          {awaitingReview.length > 0 && (
            <article className="needs-attention">
              <span>Dokumenti</span><strong>{awaitingReview.length} čeka liječnički pregled</strong>
              <button type="button" onClick={() => setActiveSection("documents")}>Pregledaj dokumente</button>
            </article>
          )}
          {openQuestions.length > 0 && (
            <article className="needs-attention">
              <span>Klinički izvori</span><strong>{openQuestions.length} otvorenih pitanja</strong>
              <button type="button" onClick={() => setActiveSection("evidence")}>Otvori izvore</button>
            </article>
          )}
          {!nextAppointment && awaitingReview.length === 0 && openQuestions.length === 0 && <p className="patient-all-clear">Nema otvorenih operativnih stavki.</p>}
        </div>
      </section>

      <WorkflowTaskPanel patientId={patient.data.id} />
      <ClinicalDerivedDataNotice />
      <WorkspaceSection title={<>{activeSummaryIsReviewed ? "Pregledani sažetak pacijenta" : "AI skica sažetka"} <HelpHint title="Sažetak pacijenta">Sažetak je pomoćni prikaz. Svaka tvrdnja mora voditi do pregledanog izvornog kliničkog dokumenta.</HelpHint></>}>
        <div className={`clinical-plan-card patient-summary-card ${activeSummary?.status === "reviewed" && !activeSummaryIsStale ? "" : "ai-suggestion"}`}>
          <div className="patient-summary-status"><span>Status</span><strong>{summaryStatusLabel(activeSummary?.status)}</strong></div>
          {activeSummaryIsStale && <p><strong>Sažetak je zastario. Generirajte novu skicu iz najnovijih pregledanih dokumenata.</strong></p>}
          {clinicalSummary.data?.summary_warning && <p>{clinicalSummary.data.summary_warning}</p>}
          {activeSummary?.status !== "reviewed" && <p><strong>AI skica — potreban je liječnički pregled.</strong></p>}
          <p>{activeSummary?.summary_text ?? "Nema potvrđenog sažetka pacijenta."}</p>
          {sourceDocuments.length > 0 && (
            <div className="patient-summary-sources">
              <span>Izvori</span>
              <div className="source-link-list">{sourceDocuments.map((document) => <Link key={document.id} to={`/clinical-documents/${document.id}`}>{document.title}</Link>)}</div>
            </div>
          )}
          <div className="quick-actions">
            <ActionButton variant="ai" onClick={generateSummaryDraft} helpTitle="Generiraj AI skicu" help="Stvara AI skicu iz pregledanih dokumenata. Ne postaje pregledani sažetak bez liječničke potvrde.">Generiraj AI skicu</ActionButton>
            {activeSummary && activeSummary.status !== "reviewed" && (
              <ActionButton variant="update" onClick={confirmSummary} helpTitle="Potvrdi sažetak" help="Potvrđuje zadnju skicu kao liječnički pregledan sažetak. Izvori ostaju vidljivi.">Potvrdi sažetak</ActionButton>
            )}
          </div>
        </div>
      </WorkspaceSection>
    </div>
  );

  return (
    <WorkspaceLayout>
      <WorkspaceHeader
        title={formatPatientName(patient.data)}
        subtitle={formatPatientIdentity(patient.data)}
        badge={<span className="readiness-badge readiness-check-ok">Karton pacijenta</span>}
        actions={(
          <>
            <Link className="button-link primary patient-primary-action" to={`/appointments/new?patient_id=${patient.data.id}`}>Novi termin</Link>
            <details className="patient-action-menu">
              <summary aria-label="Dodatne radnje za pacijenta"><MoreHorizontal size={18} aria-hidden="true" /></summary>
              <div>
                <Link to={`/clinical-documents?patient_id=${patient.data.id}`}>Dodaj dokument</Link>
                <Link to={`/laboratory?patient_id=${patient.data.id}`}>Nova laboratorijska narudžba</Link>
              </div>
            </details>
          </>
        )}
      />

      {duplicateCandidates.length > 0 && (
        <div className="duplicate-warning">
          <strong>Mogući duplikati pacijenta</strong>
          <p>Provjerite identitet prije novog naručivanja ili izmjene podataka.</p>
          {duplicateCandidates.map((candidate) => (
            <span key={candidate.id}><Link to={`/patients/${candidate.id}`}>{formatPatientName(candidate)}</Link><small>{formatPatientIdentity(candidate)}</small></span>
          ))}
        </div>
      )}

      <WorkspaceTabs
        activeId={activeSection}
        onChange={setActiveSection}
        ariaLabel="Sadržaj kartona pacijenta"
        tabs={[
          { id: "overview", label: "Pregled", content: overview },
          {
            id: "documents",
            label: `Dokumenti${awaitingReview.length ? ` (${awaitingReview.length})` : ""}`,
            content: (
              <WorkspaceSection title="Dokumenti pacijenta" actions={<Link className="button-link" to={`/clinical-documents?patient_id=${patient.data.id}`}>Dodaj dokument</Link>}>
                <p className="section-intro">Svi izvori su u jednom popisu. Tip, podrijetlo i status pregleda ostaju jasno označeni.</p>
                <DataTable rows={documents.data} columns={documentColumns} />
              </WorkspaceSection>
            )
          },
          {
            id: "care",
            label: "Laboratorij i terapije",
            content: (
              <div className="patient-tab-stack">
                <WorkspaceSection title="Laboratorijske narudžbe" actions={<Link className="button-link" to={`/laboratory?patient_id=${patient.data.id}`}>Nova narudžba</Link>}>
                  <DataTable rows={labOrders.data} columns={labOrderColumns} />
                  {laboratoryDocuments.length > 0 && <><h3>Laboratorijski dokumenti</h3><DataTable rows={laboratoryDocuments} columns={documentColumns} /></>}
                </WorkspaceSection>
                <WorkspaceSection title="Terapije" actions={<Link className="button-link" to={`/therapies?patient_id=${patient.data.id}`}>Nova terapija</Link>}>
                  <DataTable rows={therapies.data} columns={[
                    { header: "Terapija", render: (row) => row.name },
                    { header: "Upute", render: (row) => row.instructions },
                    { header: "Početak", render: (row) => formatDate(row.start_date) },
                    { header: "Završetak", render: (row) => row.end_date ? formatDate(row.end_date) : "-" },
                    { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
                    { header: "Detalj", render: () => <Link to={`/therapies?patient_id=${id}`}>Otvori</Link> }
                  ]} />
                </WorkspaceSection>
              </div>
            )
          },
          {
            id: "operations",
            label: "Termini i računi",
            content: (
              <div className="patient-tab-stack">
                <WorkspaceSection title="Termini" actions={<Link className="button-link" to={`/appointments/new?patient_id=${patient.data.id}`}>Novi termin</Link>}>
                  <DataTable rows={appointmentRows} columns={[
                    { header: "Datum", render: (row) => formatDate(row.date) },
                    { header: "Vrijeme", render: (row) => `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}` },
                    { header: "Usluga", render: (row) => row.service_name ?? "-" },
                    { header: "Klinika", render: (row) => row.clinic.name ?? "-" },
                    { header: "Status", render: (row) => <StatusBadge status={row.status} /> }
                  ]} />
                </WorkspaceSection>
                <WorkspaceSection title="Računi">
                  {openInvoices.length > 0 && <p className="section-intro"><strong>{openInvoices.length}</strong> računa još nije potpuno plaćeno.</p>}
                  <DataTable rows={invoices.data} columns={[
                    { header: "Broj", render: (row) => <Link to={`/invoices?invoice=${row.id}`}>{row.invoice_number}</Link> },
                    { header: "Datum", render: (row) => formatDate(row.invoice_date) },
                    { header: "Status", render: (row) => row.status },
                    { header: "Plaćanje", render: (row) => row.payment_status },
                    { header: "Iznos", render: (row) => `${row.total_amount} EUR` }
                  ]} />
                </WorkspaceSection>
              </div>
            )
          },
          {
            id: "evidence",
            label: "Izvori i evidencija",
            content: (
              <div className="patient-tab-stack">
                <ClinicalDerivedDataNotice />
                <WorkspaceSection title="Pregledano kliničko znanje">
                  <p className="section-intro">Prikazane stavke dolaze iz pregledanih dokumenata i vode do svojih izvora.</p>
                  <div className="knowledge-grid">
                    <KnowledgeCard title="Poznati problemi" items={clinicalSummary.data?.known_problems ?? []} />
                    <KnowledgeCard title="Završeni postupci" items={clinicalSummary.data?.completed_procedures ?? []} />
                    <KnowledgeCard title="Patologija" items={clinicalSummary.data?.pathology ?? []} />
                    <KnowledgeCard title="Laboratorij" items={clinicalSummary.data?.laboratory ?? []} />
                    <KnowledgeCard title="Radiologija" items={clinicalSummary.data?.imaging ?? []} />
                    <KnowledgeCard title="Terapija" items={clinicalSummary.data?.current_therapy ?? []} />
                    <KnowledgeCard title="Zadnje preporuke" items={clinicalSummary.data?.latest_recommendations ?? []} />
                    {openQuestions.length > 0 && <KnowledgeCard title="Otvorena pitanja" items={openQuestions} emphasizeAttention help="Zahtijevaju ljudski pregled izvora; nisu automatske odluke niti zadaci." />}
                  </div>
                </WorkspaceSection>
                <FindingsPanel state={clinicalFindings} />
                <TimelinePanel state={clinicalTimeline} />
                <WorkspaceSection title="Audit"><AuditTimeline logs={audit.data} /></WorkspaceSection>
              </div>
            )
          }
        ]}
      />
    </WorkspaceLayout>
  );
}
