import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { AuditTimeline } from "../components/AuditTimeline";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { StatusBadge } from "../components/StatusBadge";
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader";
import { WorkspaceLayout } from "../components/workspace/WorkspaceLayout";
import { WorkspaceSection } from "../components/workspace/WorkspaceSection";
import { useApi } from "../hooks/useApi";
import { Appointment, AuditLog, ClinicalEpisode } from "../types";
import { formatDate } from "../utils/date";
import { formatPatientIdentity, formatPatientName } from "../utils/patientIdentity";
import { episodeTypeLabel } from "./Episodes";

export function EpisodeDetail() {
  const { id } = useParams();
  const episode = useApi<ClinicalEpisode | null>(`/api/episodes/${id}`, null);
  const appointments = useApi<Appointment[]>(`/api/episodes/${id}/appointments`, []);
  const audit = useApi<AuditLog[]>(`/api/audit-log?entity_type=ClinicalEpisode&entity_id=${id}`, []);

  async function closeEpisode() {
    if (!episode.data) return;
    const updated = await api<ClinicalEpisode>(`/api/episodes/${episode.data.id}/close`, { method: "POST" });
    episode.setData(updated);
    audit.setData(await api<AuditLog[]>(`/api/audit-log?entity_type=ClinicalEpisode&entity_id=${episode.data.id}`));
  }

  if (!episode.data) return <WorkspaceLayout><p>Ucitavanje epizode...</p></WorkspaceLayout>;

  const patient = episode.data.patient;
  const canClose = !["completed", "cancelled", "archived"].includes(episode.data.status);

  return (
    <WorkspaceLayout>
      <WorkspaceHeader
        title={episode.data.title}
        subtitle={
          <>
            {patient ? <Link to={`/patients/${patient.id}`}>{formatPatientName(patient)}</Link> : `Pacijent ${episode.data.patient_id}`}
            {" / "}
            {patient ? formatPatientIdentity(patient) : "Nema detalja pacijenta"}
          </>
        }
        badge={<StatusBadge status={episode.data.status} />}
        actions={
          <>
            <Link className="primary link-button" to={`/appointments/new?patient_id=${episode.data.patient_id}&episode_id=${episode.data.id}`}>Novi termin</Link>
            <ActionButton
              variant="workflow"
              disabled={!canClose}
              onClick={closeEpisode}
              requiresConfirm
              confirmMessage="Zatvoriti klinicku epizodu kao dovrsenu?"
              helpTitle="Zatvori epizodu"
              help="Postavlja status completed i datum zavrsetka ako jos nije upisan. Ne donosi medicinsku odluku."
            >
              Zatvori epizodu
            </ActionButton>
          </>
        }
      />

      <div className="summary-strip">
        <div><span>Tip</span><strong>{episodeTypeLabel(episode.data.episode_type)}</strong></div>
        <div><span>Prioritet</span><strong>{episode.data.priority ?? "-"}</strong></div>
        <div><span>Pocetak</span><strong>{formatDate(episode.data.start_date)}</strong></div>
        <div><span>Kraj</span><strong>{formatDate(episode.data.end_date)}</strong></div>
        <div><span>Voditelj</span><strong>{episode.data.owner_provider?.full_name ?? "-"}</strong></div>
      </div>

      <WorkspaceSection
        title={
          <>
            Klinicki kontekst <HelpHint title="Klinicki kontekst">Ovo je opis price i pracenja. ASTRA ovdje ne postavlja dijagnozu i ne odlucuje umjesto lijecnika.</HelpHint>
          </>
        }
      >
        <div className="detail-list">
          <p><span>Sazetak</span><strong>{episode.data.summary ?? "-"}</strong></p>
          <p><span>Klinicke biljeske</span><strong>{episode.data.clinical_notes ?? "-"}</strong></p>
        </div>
      </WorkspaceSection>

      <WorkspaceSection title="Povezani termini">
        <DataTable rows={appointments.data} columns={[
          { header: "Datum", render: (row) => formatDate(row.date) },
          { header: "Vrijeme", render: (row) => `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}` },
          { header: "Usluga", render: (row) => row.service?.name ?? row.service_id },
          { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
          { header: "Detalj", render: (row) => <Link to={`/appointments/${row.id}`}>Otvori</Link> }
        ]} />
      </WorkspaceSection>

      <WorkspaceSection title="Audit timeline">
        <AuditTimeline logs={audit.data} />
      </WorkspaceSection>
    </WorkspaceLayout>
  );
}
