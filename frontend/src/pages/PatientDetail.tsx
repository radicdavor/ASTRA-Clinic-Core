import { Link, useParams } from "react-router-dom";
import { ActionButton } from "../components/ActionButton";
import { AuditTimeline } from "../components/AuditTimeline";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { StatusBadge } from "../components/StatusBadge";
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader";
import { WorkspaceLayout } from "../components/workspace/WorkspaceLayout";
import { WorkspaceSection } from "../components/workspace/WorkspaceSection";
import { WorkspaceTabs } from "../components/workspace/WorkspaceTabs";
import { useApi } from "../hooks/useApi";
import { Appointment, AuditLog, ClinicalEpisode, Invoice, Patient } from "../types";
import { formatDate } from "../utils/date";
import { formatPatientIdentity, formatPatientName } from "../utils/patientIdentity";
import { episodeTypeLabel } from "./Episodes";

export function PatientDetail() {
  const { id } = useParams();
  const patient = useApi<Patient | null>(`/api/patients/${id}`, null);
  const episodes = useApi<ClinicalEpisode[]>(`/api/patients/${id}/episodes`, []);
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
  const activeEpisodes = episodes.data.filter((episode) => ["open", "active", "waiting"].includes(episode.status));
  const sortedEpisodes = [...episodes.data].sort((a, b) => {
    const rank = (episode: ClinicalEpisode) => (["open", "active", "waiting"].includes(episode.status) ? 0 : 1);
    return rank(a) - rank(b) || b.start_date.localeCompare(a.start_date);
  });
  const openInvoices = invoices.data.filter((invoice) => invoice.payment_status !== "paid");
  const unpaidTotal = openInvoices.reduce((sum, invoice) => sum + Number(invoice.total_amount || 0), 0);

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
              onClick={() => { window.location.href = `/episodes/new?patient_id=${patient.data?.id}`; }}
              helpTitle="Nova epizoda"
              help="Otvara klinicki kontekst za odabranog pacijenta. Epizoda nije dijagnoza ni medicinska odluka."
            >
              Nova epizoda
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
        <div><span>Aktivne epizode</span><strong>{activeEpisodes.length}</strong></div>
        <div><span>Zadnji termin</span><strong>{lastAppointment ? `${formatDate(lastAppointment.date)} / ${lastAppointment.status}` : "-"}</strong></div>
        <div><span>Sljedeci termin</span><strong>{nextAppointment ? `${formatDate(nextAppointment.date)} / ${nextAppointment.status}` : "-"}</strong></div>
        <div><span>Otvoreni racuni</span><strong>{openInvoices.length ? `${openInvoices.length} / ${unpaidTotal.toFixed(2)} EUR` : "Nema"}</strong></div>
        <div><span>Moguci duplikati</span><strong>{duplicateCandidates.length}</strong></div>
      </div>

      <div className="metrics">
        <div><span>Epizode</span><strong>{episodes.data.length}</strong></div>
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

      <WorkspaceTabs
        tabs={[
          {
            id: "episodes",
            label: "Epizode",
            content: (
              <>
                <div className="filters">
                  <Link className="primary link-button" to={`/episodes/new?patient_id=${patient.data.id}`}>Nova epizoda</Link>
                </div>
                <DataTable rows={sortedEpisodes} columns={[
                  { header: "Naziv", render: (row) => <Link to={`/episodes/${row.id}`}>{row.title}</Link> },
                  { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
                  { header: "Tip", render: (row) => episodeTypeLabel(row.episode_type) },
                  { header: "Prioritet", render: (row) => row.priority ?? "-" },
                  { header: "Pocetak", render: (row) => formatDate(row.start_date) },
                  { header: "Kraj", render: (row) => formatDate(row.end_date) },
                  { header: "Termini", render: (row) => row.appointment_count ?? 0 },
                  { header: "Sazetak", render: (row) => row.summary ?? "-" }
                ]} />
              </>
            )
          },
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
    </WorkspaceLayout>
  );
}
