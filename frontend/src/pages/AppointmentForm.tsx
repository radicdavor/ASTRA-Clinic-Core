import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, Location, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DateInput } from "../components/DateInput";
import { HelpHint } from "../components/HelpHint";
import { useApi } from "../hooks/useApi";
import { ClinicalEpisode, Patient, Provider, Room, Service } from "../types";
import { formatPatientIdentity, formatPatientName, hasStrongPatientIdentifier } from "../utils/patientIdentity";

function endTimeFrom(startTime: string, duration: number) {
  const [hours, minutes] = startTime.split(":").map(Number);
  const total = hours * 60 + minutes + duration;
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

export function AppointmentForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const initialPatientId = params.get("patient_id");
  const initialEpisodeId = params.get("episode_id");
  const requestedDate = params.get("date");
  const requestedStartTime = params.get("start_time");
  const initialDate = requestedDate && /^\d{4}-\d{2}-\d{2}$/.test(requestedDate) ? requestedDate : new Date().toISOString().slice(0, 10);
  const initialStartTime = requestedStartTime && /^([01]\d|2[0-3]):[0-5]\d$/.test(requestedStartTime) ? requestedStartTime : "09:00";
  const [patientQuery, setPatientQuery] = useState("");
  const patientSearchPath = patientQuery.trim().length >= 2 ? `/api/patients?q=${encodeURIComponent(patientQuery.trim())}` : "/api/patients?q=__no_initial_results__";
  const patients = useApi<Patient[]>(patientSearchPath, []);
  const services = useApi<Service[]>("/api/services", []);
  const providers = useApi<Provider[]>("/api/providers", []);
  const rooms = useApi<Room[]>("/api/rooms", []);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [form, setForm] = useState({ patient_id: "", episode_id: initialEpisodeId ?? "", service_id: "", provider_id: "", room_id: "", date: initialDate, start_time: initialStartTime, end_time: endTimeFrom(initialStartTime, 30), duration_minutes: 30, status: "scheduled", source: "manual", notes: "" });
  const patientEpisodesPath = selectedPatient ? `/api/patients/${selectedPatient.id}/episodes` : "/api/episodes?status=__no_patient__";
  const episodes = useApi<ClinicalEpisode[]>(patientEpisodesPath, []);
  const activeEpisodes = episodes.data.filter((episode) => ["open", "active", "waiting"].includes(episode.status));
  const selectedService = useMemo(() => services.data.find((service) => String(service.id) === form.service_id), [form.service_id, services.data]);
  const similarPatientWarning = patients.data.length > 1 && !selectedPatient;
  const createPatientLink = useMemo(() => {
    const next = new URLSearchParams({ return_to: "appointment" });
    if (patientQuery.trim()) next.set("name", patientQuery.trim());
    return `/patients/new?${next.toString()}`;
  }, [patientQuery]);

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
    setForm({ ...form, patient_id: String(patient.id) });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selectedPatient) return;
    const appointment = await api<{ id: number }>("/api/appointments", {
      method: "POST",
      body: JSON.stringify({ ...form, patient_id: selectedPatient.id, episode_id: form.episode_id ? Number(form.episode_id) : null, service_id: Number(form.service_id), provider_id: Number(form.provider_id), room_id: Number(form.room_id) })
    });
    const routeState = location.state as { backgroundLocation?: Location } | null;
    navigate(`/appointments/${appointment.id}`, routeState?.backgroundLocation ? { state: { backgroundLocation: routeState.backgroundLocation } } : undefined);
  }

  return (
    <section className="page narrow">
      <div className="page-header">
        <div>
          <h1>
            Novi termin <HelpHint title="Novi termin">Termin povezuje pacijenta, uslugu, lijecnika, sobu i vrijeme. Sustav provjerava preklapanje lijecnika i sobe.</HelpHint>
          </h1>
        </div>
      </div>
      {(requestedDate || requestedStartTime) && (
        <p className="program1-note appointment-slot-context">
          Termin je otvoren iz slobodnog recepcijskog slota: {form.date} u {form.start_time}. Vrijeme se može promijeniti prije spremanja.
        </p>
      )}
      <form className="form-grid" onSubmit={submit}>
        <label className="wide-field">
          <span className="label-with-help">
            Pacijent
            <HelpHint title="Pacijent u terminu">Pocnite upisivati ime, prezime, telefon, e-postu ili OIB. Ako postoji vise slicnih pacijenata, provjerite datum rodenja i OIB prije odabira.</HelpHint>
          </span>
          <input value={patientQuery} onChange={(event) => { setPatientQuery(event.target.value); setSelectedPatient(null); setForm({ ...form, patient_id: "", episode_id: "" }); }} placeholder="Ime, prezime ili OIB" />
        </label>
        {patientQuery.trim().length >= 2 && !selectedPatient && (
          <div className="patient-results wide-field">
            {similarPatientWarning && <p className="form-error">Pronadeno je vise slicnih pacijenata - provjerite datum rodenja/OIB prije odabira.</p>}
            {patients.data.length === 0 && (
              <p>
                Nema pronadenog pacijenta. <Link to={createPatientLink}>Kreiraj novog pacijenta</Link>
              </p>
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
              {!hasStrongPatientIdentifier(selectedPatient) && <small className="identity-warning">Pacijent nema jak identifikator. Provjerite prije spremanja termina.</small>}
            </span>
            <button type="button" onClick={() => { setSelectedPatient(null); setForm({ ...form, patient_id: "", episode_id: "" }); }}>Promijeni</button>
          </div>
        )}
        {selectedPatient && (
          <label className="wide-field">
            <span className="label-with-help">
              Klinicka epizoda
              <HelpHint title="Epizoda termina">Termin se moze povezati s otvorenom epizodom istog pacijenta. U prvoj verziji opcija Bez epizode ostaje dozvoljena.</HelpHint>
            </span>
            <select value={form.episode_id} onChange={(event) => setForm({ ...form, episode_id: event.target.value })}>
              <option value="">Bez epizode</option>
              {activeEpisodes.map((episode) => <option key={episode.id} value={episode.id}>{episode.title} / {episode.status}</option>)}
            </select>
          </label>
        )}
        <label>
          <span className="label-with-help">
            Usluga
            <HelpHint title="Usluga">Usluga odreduje trajanje, cijenu i moguce materijale koji se skidaju sa zalihe nakon zavrsetka termina.</HelpHint>
          </span>
          <select required value={form.service_id} onChange={(e) => {
            const service = services.data.find((item) => String(item.id) === e.target.value);
            setForm({ ...form, service_id: e.target.value, duration_minutes: service?.duration_minutes ?? form.duration_minutes, end_time: service ? endTimeFrom(form.start_time, service.duration_minutes) : form.end_time });
          }}><option value="">Odaberi</option>{services.data.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
        </label>
        {selectedService && (
          <div className="service-context wide-field">
            <strong>{selectedService.name}</strong>
            <span>Trajanje: {selectedService.duration_minutes} min / Cijena: {selectedService.price} EUR / Sifra: {selectedService.code ?? "-"}</span>
            <small>Materijali se skidaju pri zavrsetku termina ako usluga ima predlozak potrosnje.</small>
          </div>
        )}
        <label>Lijecnik<select required value={form.provider_id} onChange={(e) => setForm({ ...form, provider_id: e.target.value })}><option value="">Odaberi</option>{providers.data.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}</select></label>
        <label>Soba<select required value={form.room_id} onChange={(e) => setForm({ ...form, room_id: e.target.value })}><option value="">Odaberi</option>{rooms.data.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}</select></label>
        <label>Datum<DateInput required value={form.date} onChange={(value) => setForm({ ...form, date: value })} /></label>
        <label>Pocetak<input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value, end_time: selectedService ? endTimeFrom(e.target.value, selectedService.duration_minutes) : form.end_time })} /></label>
        <label>Kraj<input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} /></label>
        <label>Trajanje<input type="number" value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })} /></label>
        <ActionButton type="submit" className="primary" variant="create" disabled={!selectedPatient} helpTitle="Spremi termin" help="Termin se moze spremiti tek nakon odabira konkretnog pacijenta iz rezultata pretrage. Ne stvarajte termin za nepoznatog pacijenta.">
          Spremi termin
        </ActionButton>
      </form>
    </section>
  );
}
