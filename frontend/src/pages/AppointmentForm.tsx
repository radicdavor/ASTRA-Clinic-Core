import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { HelpHint } from "../components/HelpHint";
import { useApi } from "../hooks/useApi";
import { Patient, Provider, Room, Service } from "../types";
import { formatDate } from "../utils/date";

function patientSubtitle(patient: Patient) {
  const parts = [
    patient.date_of_birth ? `roden/a ${formatDate(patient.date_of_birth)}` : null,
    patient.oib ? `OIB ${patient.oib}` : null,
    patient.phone || patient.email || null
  ].filter(Boolean);
  return parts.length ? parts.join(" / ") : "Nema dodatnih identifikacijskih podataka";
}

export function AppointmentForm() {
  const navigate = useNavigate();
  const [patientQuery, setPatientQuery] = useState("");
  const patientSearchPath = patientQuery.trim().length >= 2 ? `/api/patients?q=${encodeURIComponent(patientQuery.trim())}` : "/api/patients?q=__no_initial_results__";
  const patients = useApi<Patient[]>(patientSearchPath, []);
  const services = useApi<Service[]>("/api/services", []);
  const providers = useApi<Provider[]>("/api/providers", []);
  const rooms = useApi<Room[]>("/api/rooms", []);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [form, setForm] = useState({ patient_id: "", service_id: "", provider_id: "", room_id: "", date: new Date().toISOString().slice(0, 10), start_time: "09:00", end_time: "09:30", duration_minutes: 30, status: "scheduled", source: "manual", notes: "" });
  const selectedService = useMemo(() => services.data.find((service) => String(service.id) === form.service_id), [form.service_id, services.data]);
  const similarPatientWarning = patients.data.length > 1 && !selectedPatient;

  function selectPatient(patient: Patient) {
    setSelectedPatient(patient);
    setPatientQuery(`${patient.first_name} ${patient.last_name}`);
    setForm({ ...form, patient_id: String(patient.id) });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selectedPatient) return;
    await api("/api/appointments", {
      method: "POST",
      body: JSON.stringify({ ...form, patient_id: selectedPatient.id, service_id: Number(form.service_id), provider_id: Number(form.provider_id), room_id: Number(form.room_id) })
    });
    navigate("/appointments");
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
      <form className="form-grid" onSubmit={submit}>
        <label className="wide-field">
          <span className="label-with-help">
            Pacijent
            <HelpHint title="Pacijent u terminu">Pocnite upisivati ime, prezime, telefon, e-postu ili OIB. Ako postoji vise slicnih pacijenata, provjerite datum rodenja i OIB prije odabira.</HelpHint>
          </span>
          <input value={patientQuery} onChange={(event) => { setPatientQuery(event.target.value); setSelectedPatient(null); setForm({ ...form, patient_id: "" }); }} placeholder="Ime, prezime ili OIB" />
        </label>
        {patientQuery.trim().length >= 2 && !selectedPatient && (
          <div className="patient-results wide-field">
            {similarPatientWarning && <p className="form-error">Pronadeno je vise slicnih pacijenata - provjerite datum rodenja/OIB prije odabira.</p>}
            {patients.data.length === 0 && (
              <p>
                Nema pronadenog pacijenta. <Link to="/patients/new">Kreiraj novog pacijenta</Link>
              </p>
            )}
            {patients.data.map((patient) => (
              <button type="button" key={patient.id} onClick={() => selectPatient(patient)}>
                <strong>{patient.first_name} {patient.last_name}</strong>
                <span>{patientSubtitle(patient)}</span>
              </button>
            ))}
          </div>
        )}
        {selectedPatient && (
          <div className="selected-patient wide-field">
            <span>
              Odabrani pacijent: <strong>{selectedPatient.first_name} {selectedPatient.last_name}</strong>
              <small>{patientSubtitle(selectedPatient)}</small>
            </span>
            <button type="button" onClick={() => { setSelectedPatient(null); setForm({ ...form, patient_id: "" }); }}>Promijeni</button>
          </div>
        )}
        <label>
          <span className="label-with-help">
            Usluga
            <HelpHint title="Usluga">Usluga odreduje trajanje, cijenu i moguce materijale koji se skidaju sa zalihe nakon zavrsetka termina.</HelpHint>
          </span>
          <select required value={form.service_id} onChange={(e) => setForm({ ...form, service_id: e.target.value })}><option value="">Odaberi</option>{services.data.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
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
        <label>Datum<input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} /></label>
        <label>Pocetak<input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} /></label>
        <label>Kraj<input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} /></label>
        <label>Trajanje<input type="number" value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })} /></label>
        <button className="primary" disabled={!selectedPatient}>Spremi termin</button>
        <HelpHint title="Spremi termin">Termin se moze spremiti tek nakon odabira konkretnog pacijenta iz rezultata pretrage.</HelpHint>
      </form>
    </section>
  );
}
