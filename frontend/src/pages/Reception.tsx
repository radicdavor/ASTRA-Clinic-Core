import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DateInput } from "../components/DateInput";
import { HelpHint } from "../components/HelpHint";
import { StatusBadge, statusLabel } from "../components/StatusBadge";
import { useApi } from "../hooks/useApi";
import { Appointment, Clinic, Provider, ReceptionSlot, Room, Service } from "../types";
import { formatDate } from "../utils/date";
import { formatPatientName } from "../utils/patientIdentity";

const today = new Date().toISOString().slice(0, 10);
const receptionStatuses = ["scheduled", "confirmed", "arrived", "in_progress", "completed", "cancelled", "no_show"];

function moveDate(value: string, days: number) {
  const next = new Date(`${value}T12:00:00`);
  next.setDate(next.getDate() + days);
  return next.toISOString().slice(0, 10);
}

function isHalfHour(time: string) {
  const minutes = Number(time.slice(3, 5));
  return minutes === 0 || minutes === 30;
}

export function Reception() {
  const location = useLocation();
  const [date, setDate] = useState(today);
  const [view, setView] = useState<"day" | "week" | "month">("day");
  const [filters, setFilters] = useState({ clinic_id: "", room_id: "", provider_id: "", service_id: "", status: "" });
  const [selected, setSelected] = useState<Appointment | null>(null);
  const [patientDraft, setPatientDraft] = useState({ first_name: "", last_name: "", date_of_birth: "", oib: "", phone: "", email: "" });
  const clinics = useApi<Clinic[]>("/api/clinics", []);
  const rooms = useApi<Room[]>("/api/rooms", []);
  const providers = useApi<Provider[]>("/api/providers", []);
  const services = useApi<Service[]>("/api/services", []);
  const query = useMemo(() => {
    const params = new URLSearchParams({ date });
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    return `/api/reception/day?${params.toString()}`;
  }, [date, filters]);
  const slots = useApi<ReceptionSlot[]>(query, []);
  const visibleSlots = useMemo(
    () => slots.data.filter((slot) => Boolean(slot.appointment) || (slot.empty && isHalfHour(slot.time))),
    [slots.data]
  );

  function openAppointment(appointment: Appointment) {
    setSelected(appointment);
    setPatientDraft({
      first_name: appointment.patient?.first_name ?? "",
      last_name: appointment.patient?.last_name ?? "",
      date_of_birth: appointment.patient?.date_of_birth ?? "",
      oib: appointment.patient?.oib ?? "",
      phone: appointment.patient?.phone ?? "",
      email: appointment.patient?.email ?? ""
    });
  }

  async function refresh() {
    slots.setData(await api<ReceptionSlot[]>(query));
  }

  useEffect(() => {
    function refreshAfterAppointmentChange() {
      void refresh();
    }
    window.addEventListener("astra:appointments-changed", refreshAfterAppointmentChange);
    return () => window.removeEventListener("astra:appointments-changed", refreshAfterAppointmentChange);
  }, [query]);

  async function markArrived() {
    if (!selected) return;
    await api<Appointment>(`/api/appointments/${selected.id}/mark-arrived`, {
      method: "POST",
      body: JSON.stringify({
        identity_verified: true,
        patient: {
          ...patientDraft,
          date_of_birth: patientDraft.date_of_birth || null,
          oib: patientDraft.oib || null,
          phone: patientDraft.phone || null,
          email: patientDraft.email || null
        }
      })
    });
    setSelected(null);
    await refresh();
  }

  async function startService() {
    if (!selected) return;
    await api<Appointment>(`/api/appointments/${selected.id}/start-service`, { method: "POST" });
    setSelected(null);
    await refresh();
  }

  const hasIdentityDetails = Boolean(
    patientDraft.first_name.trim()
    && patientDraft.last_name.trim()
    && (patientDraft.date_of_birth || patientDraft.oib || patientDraft.phone || patientDraft.email)
  );
  const canMarkArrived = Boolean(selected && ["scheduled", "confirmed"].includes(selected.status) && hasIdentityDetails);
  const canStartService = Boolean(selected && selected.status === "arrived" && selected.identity_verified_at);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>
            Prijem <HelpHint title="Prijem">Recepcija prikazuje resursni raspored i omogucuje provjeru identiteta prije oznake dolaska.</HelpHint>
          </h1>
          <p>Odabrani dan: {formatDate(date)}. Prazni slotovi prikazani su svakih pola sata; postojeći termini zadržavaju točno vrijeme početka.</p>
        </div>
        <div className="reception-date-controls">
          <button type="button" className="action-button" onClick={() => setDate(moveDate(date, -1))}>Prethodni dan</button>
          <button type="button" className="action-button" onClick={() => setDate(today)}>Danas</button>
          <DateInput required value={date} onChange={setDate} />
          <button type="button" className="action-button" onClick={() => setDate(moveDate(date, 1))}>Sljedeći dan</button>
        </div>
      </div>

      <div className="segmented-control">
        <button className={view === "day" ? "active" : ""} onClick={() => setView("day")}>Dan</button>
        <button className={view === "week" ? "active" : ""} onClick={() => setView("week")}>Tjedan</button>
        <button className={view === "month" ? "active" : ""} onClick={() => setView("month")}>Mjesec</button>
      </div>
      {view !== "day" && <p className="form-error">Tjedni i mjesecni prikaz su deferred; dnevni resursni grid je aktivan.</p>}

      <div className="filters">
        <select value={filters.clinic_id} onChange={(event) => setFilters({ ...filters, clinic_id: event.target.value })}><option value="">Sve klinike</option>{clinics.data.map((clinic) => <option key={clinic.id} value={clinic.id}>{clinic.name}</option>)}</select>
        <select value={filters.room_id} onChange={(event) => setFilters({ ...filters, room_id: event.target.value })}><option value="">Sve sobe</option>{rooms.data.map((room) => <option key={room.id} value={room.id}>{room.name}</option>)}</select>
        <select value={filters.provider_id} onChange={(event) => setFilters({ ...filters, provider_id: event.target.value })}><option value="">Svi djelatnici</option>{providers.data.map((provider) => <option key={provider.id} value={provider.id}>{provider.full_name}</option>)}</select>
        <select value={filters.service_id} onChange={(event) => setFilters({ ...filters, service_id: event.target.value })}><option value="">Sve usluge</option>{services.data.map((service) => <option key={service.id} value={service.id}>{service.name}</option>)}</select>
        <select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}><option value="">Svi statusi</option>{receptionStatuses.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}</select>
      </div>

      <div className="reception-grid">
        {visibleSlots.map((slot) => (
          <div key={slot.time} className={`reception-slot ${slot.empty ? "empty" : "occupied"}`}>
            <time>{slot.time}</time>
            {slot.appointment ? (
              <button className="reception-card" style={{ minHeight: `${Math.max(Math.ceil(slot.span / 3), 1) * 50}px` }} onClick={() => openAppointment(slot.appointment!)}>
                <strong>{slot.appointment.start_time.slice(0, 5)} - {slot.appointment.end_time.slice(0, 5)}</strong>
                <span>{slot.appointment.patient ? formatPatientName(slot.appointment.patient) : `Pacijent #${slot.appointment.patient_id}`}</span>
                <span>{slot.appointment.service?.name ?? slot.appointment.service_id}</span>
                <small>{slot.appointment.provider?.full_name ?? slot.appointment.provider_id} / {slot.appointment.room?.name ?? slot.appointment.room_id}</small>
                <StatusBadge status={slot.appointment.status} />
                <small>{slot.appointment.arrived_at ? "Dolazak evidentiran" : "Ceka dolazak"}</small>
              </button>
            ) : slot.empty ? (
              <Link className="empty-slot empty-slot-action" to={`/appointments/new?date=${date}&start_time=${slot.time}`} state={{ backgroundLocation: location }}>
                <span>Slobodno</span>
                <strong>Novi termin</strong>
              </Link>
            ) : <span className="empty-slot">Zauzeto</span>}
          </div>
        ))}
      </div>

      {selected && (
        <div className="modal-backdrop">
          <div className="modal-panel reception-panel">
            <div className="page-header">
              <div>
                <h2>Prijem pacijenta</h2>
                <p>{selected.service?.name} / {selected.start_time.slice(0, 5)} - {selected.end_time.slice(0, 5)}</p>
              </div>
              <StatusBadge status={selected.status} />
            </div>
            <div className="form-grid">
              <label>Ime<input value={patientDraft.first_name} onChange={(event) => setPatientDraft({ ...patientDraft, first_name: event.target.value })} /></label>
              <label>Prezime<input value={patientDraft.last_name} onChange={(event) => setPatientDraft({ ...patientDraft, last_name: event.target.value })} /></label>
              <label>Datum rodenja<DateInput value={patientDraft.date_of_birth} onChange={(value) => setPatientDraft({ ...patientDraft, date_of_birth: value })} /></label>
              <label>OIB<input value={patientDraft.oib} onChange={(event) => setPatientDraft({ ...patientDraft, oib: event.target.value })} /></label>
              <label>Telefon<input value={patientDraft.phone} onChange={(event) => setPatientDraft({ ...patientDraft, phone: event.target.value })} /></label>
              <label>E-posta<input value={patientDraft.email} onChange={(event) => setPatientDraft({ ...patientDraft, email: event.target.value })} /></label>
            </div>
            {!hasIdentityDetails && <p className="form-error">Za provjeru identiteta trebaju ime, prezime i najmanje jedan dodatni podatak: datum rođenja, OIB, telefon ili e-pošta.</p>}
            {selected.status === "arrived" && !selected.identity_verified_at && <p className="form-error">Dolazak postoji, ali provjera identiteta nije evidentirana. Usluga se ne može započeti.</p>}
            <div className="quick-actions">
              <ActionButton variant="workflow" className="primary" disabled={!canMarkArrived} onClick={markArrived} helpTitle="Oznaci kao pristigao" help="Dopunjava podatke pacijenta, biljezi provjeru identiteta i postavlja termin u status stigao/la. Dostupno je samo za zakazan ili potvrden termin.">
                Oznaci kao pristigao
              </ActionButton>
              <ActionButton variant="workflow" disabled={!canStartService} onClick={startService} helpTitle="Zapocni uslugu" help="Postavlja termin u status u tijeku tek nakon evidentiranog dolaska i provjere identiteta.">
                Zapocni uslugu
              </ActionButton>
              <Link to={`/appointments/${selected.id}`} state={{ backgroundLocation: location }} onClick={() => setSelected(null)}>Otvori termin</Link>
              <Link to={`/patients/${selected.patient_id}`}>Otvori pacijenta</Link>
              <button onClick={() => setSelected(null)}>Zatvori</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
