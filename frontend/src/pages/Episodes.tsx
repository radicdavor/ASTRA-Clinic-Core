import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { StatusBadge } from "../components/StatusBadge";
import { useApi } from "../hooks/useApi";
import { ClinicalEpisode } from "../types";
import { formatDate } from "../utils/date";
import { formatPatientName } from "../utils/patientIdentity";

export function episodeTypeLabel(value: string) {
  const labels: Record<string, string> = {
    general: "Opca",
    gastroenterology: "Gastroenterologija",
    endoscopy: "Endoskopija",
    dermatology_aesthetics: "Dermatologija/estetika",
    metabolic: "Metabolicka",
    preventive: "Preventivna",
    administrative: "Administrativna"
  };
  return labels[value] ?? value;
}

export function Episodes() {
  const episodes = useApi<ClinicalEpisode[]>("/api/episodes", []);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>
            Epizode <HelpHint title="Eksperimentalno">Episode Engine je eksperimentalno/deferred podrucje. Primarni klinicki smjer je Patient Clinical Knowledge Layer.</HelpHint>
          </h1>
          <p>Eksperimentalni klinicki konteksti. Ne koristiti kao primarni workflow dok Patient Clinical Knowledge Layer nije stabilan.</p>
        </div>
        <span className="action-with-help">
          <Link className="primary link-button" to="/episodes/new">Nova epizoda</Link>
          <HelpHint title="Eksperimentalno">Ova funkcija ostaje dostupna samo radi kompatibilnosti s postojecim demo podacima.</HelpHint>
        </span>
      </div>
      <DataTable rows={episodes.data} columns={[
        { header: "Naziv", render: (row) => <Link to={`/episodes/${row.id}`}>{row.title}</Link> },
        { header: "Pacijent", render: (row) => row.patient ? <Link to={`/patients/${row.patient.id}`}>{formatPatientName(row.patient)}</Link> : row.patient_id },
        { header: "Tip", render: (row) => episodeTypeLabel(row.episode_type) },
        { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
        { header: "Prioritet", render: (row) => row.priority ?? "-" },
        { header: "Pocetak", render: (row) => formatDate(row.start_date) },
        { header: "Voditelj", render: (row) => row.owner_provider?.full_name ?? "-" },
        { header: "Detalj", render: (row) => <Link to={`/episodes/${row.id}`}>Otvori</Link> }
      ]} />
    </section>
  );
}
