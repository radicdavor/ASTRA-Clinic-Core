import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DateInput } from "../components/DateInput";
import { HelpHint } from "../components/HelpHint";
import { QuickPatientModal } from "../components/QuickPatientModal";
import { useApi } from "../hooks/useApi";
import { ClinicalEpisode, Patient, Provider } from "../types";
import { formatPatientIdentity, formatPatientName } from "../utils/patientIdentity";

const episodeTypes = ["general", "gastroenterology", "endoscopy", "dermatology_aesthetics", "metabolic", "preventive", "administrative"];
const episodeStatuses = ["open", "active", "waiting", "completed", "cancelled", "archived"];
const priorities = ["routine", "important", "urgent"];

export function EpisodeForm() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const initialPatientId = params.get("patient_id");
  const [patientQuery, setPatientQuery] = useState("");
  const patientSearchPath = patientQuery.trim().length >= 2 ? `/api/patients?q=${encodeURIComponent(patientQuery.trim())}` : "/api/patients?q=__no_initial_results__";
  const patients = useApi<Patient[]>(patientSearchPath, []);
  const providers = useApi<Provider[]>("/api/providers", []);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [showQuickPatient, setShowQuickPatient] = useState(false);
  const [form, setForm] = useState({
    title: "",
    episode_type: "general",
    status: "open",
    priority: "routine",
    start_date: new Date().toISOString().slice(0, 10),
    end_date: "",
    owner_provider_id: "",
    summary: "",
    clinical_notes: ""
  });

  useEffect(() => {
    if (!initialPatientId || selectedPatient) return;
    let alive = true;
    api<Patient>(`/api/patients/${initialPatientId}`).then((patient) => {
      if (!alive) return;
      selectPatient(patient);
    }).catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [initialPatientId, selectedPatient]);

  function selectPatient(patient: Patient) {
    setSelectedPatient(patient);
    setPatientQuery(`${patient.first_name} ${patient.last_name}`);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selectedPatient) return;
    const payload = {
      ...form,
      patient_id: selectedPatient.id,
      end_date: form.end_date || null,
      owner_provider_id: form.owner_provider_id ? Number(form.owner_provider_id) : null
    };
    const episode = await api<ClinicalEpisode>("/api/episodes", { method: "POST", body: JSON.stringify(payload) });
    navigate(`/episodes/${episode.id}`);
  }

  return (
    <section className="page narrow">
      <div className="page-header">
        <div>
          <h1>
            Nova epizoda <HelpHint title="Nova klinicka epizoda">Epizoda opisuje kontekst skrbi. Ne zamjenjuje dijagnozu, nalaz ni medicinsku odluku.</HelpHint>
          </h1>
        </div>
      </div>
      <form className="form-grid" onSubmit={submit}>
        <label className="wide-field">
          <span className="label-with-help">
            Pacijent
            <HelpHint title="Pacijent epizode">Epizoda uvijek pripada poznatom pacijentu. Termin se kasnije moze povezati samo s epizodom istog pacijenta.</HelpHint>
          </span>
          <input value={patientQuery} onChange={(event) => { setPatientQuery(event.target.value); setSelectedPatient(null); }} placeholder="Ime, prezime ili OIB" />
        </label>
        {patientQuery.trim().length >= 2 && !selectedPatient && (
          <div className="patient-results wide-field">
            {patients.data.length === 0 && (
              <div className="patient-not-found"><p>Nema pronađenog pacijenta.</p><button type="button" className="primary" onClick={()=>setShowQuickPatient(true)}>Dodaj pacijenta</button></div>
            )}
            {patients.data.map((patient) => (
              <button type="button" key={patient.id} onClick={() => selectPatient(patient)}>
                <strong>{formatPatientName(patient)}</strong>
                <span>{formatPatientIdentity(patient)}</span>
              </button>
            ))}
          </div>
        )}
        {selectedPatient && (
          <div className="selected-patient wide-field">
            <span>
              Odabrani pacijent: <strong>{formatPatientName(selectedPatient)}</strong>
              <small>{formatPatientIdentity(selectedPatient)}</small>
            </span>
            <button type="button" onClick={() => setSelectedPatient(null)}>Promijeni</button>
          </div>
        )}
        <label className="wide-field">Naziv<input required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="npr. GERB/refluks pracenje" /></label>
        <label>Tip<select value={form.episode_type} onChange={(event) => setForm({ ...form, episode_type: event.target.value })}>{episodeTypes.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
        <label>Status<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>{episodeStatuses.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
        <label>Prioritet<select value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}>{priorities.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
        <label>Voditelj<select value={form.owner_provider_id} onChange={(event) => setForm({ ...form, owner_provider_id: event.target.value })}><option value="">Bez voditelja</option>{providers.data.filter((provider) => provider.staff_role === "physician").map((provider) => <option key={provider.id} value={provider.id}>{provider.full_name}</option>)}</select></label>
        <label>Pocetak<DateInput required value={form.start_date} onChange={(value) => setForm({ ...form, start_date: value })} /></label>
        <label>Kraj<DateInput value={form.end_date} onChange={(value) => setForm({ ...form, end_date: value })} /></label>
        <label className="wide-field">Sazetak<textarea value={form.summary} onChange={(event) => setForm({ ...form, summary: event.target.value })} rows={3} /></label>
        <label className="wide-field">Klinicke biljeske<textarea value={form.clinical_notes} onChange={(event) => setForm({ ...form, clinical_notes: event.target.value })} rows={4} /></label>
        <ActionButton type="submit" className="primary" variant="create" disabled={!selectedPatient} helpTitle="Spremi epizodu" help="Sprema demo klinicki kontekst za postojeceg pacijenta. Ne unosi realne medicinske podatke.">
          Spremi epizodu
        </ActionButton>
      </form>
      {showQuickPatient&&<QuickPatientModal initialQuery={patientQuery} onClose={()=>setShowQuickPatient(false)} onCreated={patient=>{selectPatient(patient);setShowQuickPatient(false)}}/>}
    </section>
  );
}
