import { useEffect, useMemo, useState } from "react";
import { Trash2 } from "lucide-react";
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

function localDateValue(value = new Date()) {
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
}

const today = localDateValue();
const receptionStatuses = ["scheduled", "confirmed", "arrived", "in_progress", "completed", "cancelled", "no_show"];
const weekdayLabels = ["Ned", "Pon", "Uto", "Sri", "Čet", "Pet", "Sub"];
const blockingReceptionStatuses = new Set(["scheduled", "confirmed", "arrived", "in_progress", "waiting_for_result", "follow_up_needed", "rescheduled"]);
const halfHourTimes = Array.from({ length: 29 }, (_, index) => {
  const minutes = 7 * 60 + index * 30;
  return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
});

function moveDate(value: string, days: number) {
  const next = new Date(`${value}T12:00:00`);
  next.setDate(next.getDate() + days);
  return next.toISOString().slice(0, 10);
}

function isHalfHour(time: string) {
  const minutes = Number(time.slice(3, 5));
  return minutes === 0 || minutes === 30;
}

function shortDate(value: string) {
  const parsed = new Date(`${value}T12:00:00`);
  return `${weekdayLabels[parsed.getDay()]} ${String(parsed.getDate()).padStart(2, "0")}.${String(parsed.getMonth() + 1).padStart(2, "0")}.`;
}

function mondayOfWeek(value: string) {
  const parsed = new Date(`${value}T12:00:00`);
  const daysSinceMonday = (parsed.getDay() + 6) % 7;
  return moveDate(value, -daysSinceMonday);
}

function isSunday(value: string) {
  return new Date(`${value}T12:00:00`).getDay() === 0;
}

function timeToMinutes(value: string) {
  const [hours, minutes] = value.slice(0, 5).split(":").map(Number);
  return hours * 60 + minutes;
}

function freeHalfHourTimes(appointments: Appointment[], provider: Provider) {
  return halfHourTimes.filter((time) => {
    const start = timeToMinutes(time);
    const end = start + 30;
    const withinWorkingHours = start >= timeToMinutes(provider.work_start) && end <= timeToMinutes(provider.work_end);
    return withinWorkingHours && !appointments.some((appointment) => blockingReceptionStatuses.has(appointment.status)
      && timeToMinutes(appointment.start_time) < end
      && timeToMinutes(appointment.end_time) > start);
  });
}

export function Reception() {
  const location = useLocation();
  const [date, setDate] = useState(today);
  const [view, setView] = useState<"day" | "week">("day");
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
  const weekDates = useMemo(() => {
    const monday = mondayOfWeek(date);
    return Array.from({ length: 7 }, (_, index) => moveDate(monday, index));
  }, [date]);
  const weekQuery = useMemo(() => {
    const params = new URLSearchParams({ date_from: weekDates[0], date_to: weekDates[6] });
    if (filters.room_id) params.set("room_id", filters.room_id);
    if (filters.provider_id) params.set("provider_id", filters.provider_id);
    if (filters.status) params.set("status", filters.status);
    return `/api/appointments?${params.toString()}`;
  }, [weekDates, filters.room_id, filters.provider_id, filters.status]);
  const weekData = useApi<Appointment[]>(weekQuery, []);
  const weekAppointments = useMemo(() => weekData.data.filter((appointment) => {
    if (filters.service_id && String(appointment.service_id) !== filters.service_id) return false;
    if (filters.clinic_id) {
      const clinicId = appointment.room?.clinic_id ?? appointment.provider?.clinic_id;
      if (String(clinicId ?? "") !== filters.clinic_id) return false;
    }
    return true;
  }), [weekData.data, filters.service_id, filters.clinic_id]);
  const clinicProviders = useMemo(() => providers.data.filter((provider) => !filters.clinic_id || String(provider.clinic_id ?? "") === filters.clinic_id), [providers.data, filters.clinic_id]);
  const clinicRooms = useMemo(() => rooms.data.filter((room) => !filters.clinic_id || String(room.clinic_id ?? "") === filters.clinic_id), [rooms.data, filters.clinic_id]);
  const selectedProvider = useMemo(() => providers.data.find((provider) => String(provider.id) === filters.provider_id), [providers.data, filters.provider_id]);
  const resourcesReady = Boolean(filters.clinic_id && filters.provider_id && filters.room_id && selectedProvider);
  const visibleSlots = useMemo(
    () => slots.data.filter((slot) => Boolean(slot.appointment) || (resourcesReady && slot.empty && isHalfHour(slot.time))),
    [slots.data, resourcesReady]
  );
  const slotWithinProviderHours = (time: string) => Boolean(selectedProvider
    && timeToMinutes(time) >= timeToMinutes(selectedProvider.work_start)
    && timeToMinutes(time) + 30 <= timeToMinutes(selectedProvider.work_end));
  const bookingParams = (bookingDate: string, startTime: string) => new URLSearchParams({ date: bookingDate, start_time: startTime, clinic_id: filters.clinic_id, provider_id: filters.provider_id, room_id: filters.room_id }).toString();

  function selectClinic(clinicId: string) {
    const matchingProviders = providers.data.filter((provider) => String(provider.clinic_id ?? "") === clinicId);
    const matchingRooms = rooms.data.filter((room) => String(room.clinic_id ?? "") === clinicId);
    setFilters({
      ...filters,
      clinic_id: clinicId,
      provider_id: matchingProviders.length === 1 ? String(matchingProviders[0].id) : "",
      room_id: matchingRooms.length === 1 ? String(matchingRooms[0].id) : ""
    });
  }

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
    const [nextSlots, nextWeek] = await Promise.all([
      api<ReceptionSlot[]>(query),
      api<Appointment[]>(weekQuery)
    ]);
    slots.setData(nextSlots);
    weekData.setData(nextWeek);
  }

  useEffect(() => {
    function refreshAfterAppointmentChange() {
      void refresh();
    }
    window.addEventListener("astra:appointments-changed", refreshAfterAppointmentChange);
    return () => window.removeEventListener("astra:appointments-changed", refreshAfterAppointmentChange);
  }, [query, weekQuery]);

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

  async function deleteAppointment(appointment: Appointment) {
    const patientName = appointment.patient ? formatPatientName(appointment.patient) : `pacijenta #${appointment.patient_id}`;
    const confirmed = window.confirm(`Obrisati termin ${appointment.start_time.slice(0, 5)} za ${patientName}? Pacijent ostaje u evidenciji.`);
    if (!confirmed) return;
    await api(`/api/appointments/${appointment.id}`, { method: "DELETE" });
    if (selected?.id === appointment.id) setSelected(null);
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
          <p>{view === "day" ? `Dnevni popis za ${formatDate(date)}.` : `Sedmodnevni pregled od ${formatDate(weekDates[0])} do ${formatDate(weekDates[6])}.`}</p>
        </div>
        <div className="reception-date-controls">
          <button type="button" className="action-button" onClick={() => setDate(moveDate(date, view === "week" ? -7 : -1))}>Prethodni {view === "week" ? "tjedan" : "dan"}</button>
          <button type="button" className="action-button" onClick={() => setDate(today)}>Danas</button>
          <DateInput required value={date} onChange={setDate} />
          <button type="button" className="action-button" onClick={() => setDate(moveDate(date, view === "week" ? 7 : 1))}>Sljedeći {view === "week" ? "tjedan" : "dan"}</button>
        </div>
      </div>

      <div className="segmented-control">
        <button className={view === "day" ? "active" : ""} onClick={() => setView("day")}>Dan</button>
        <button className={view === "week" ? "active" : ""} onClick={() => setView("week")}>Tjedan</button>
      </div>

      <div className="filters reception-resource-filters">
        <select value={filters.clinic_id} onChange={(event) => selectClinic(event.target.value)}><option value="">Odaberi kliniku</option>{clinics.data.map((clinic) => <option key={clinic.id} value={clinic.id}>{clinic.name}</option>)}</select>
        <select disabled={!filters.clinic_id} value={filters.provider_id} onChange={(event) => setFilters({ ...filters, provider_id: event.target.value })}><option value="">Odaberi liječnika</option>{clinicProviders.map((provider) => <option key={provider.id} value={provider.id}>{provider.full_name} · {provider.work_start.slice(0, 5)}–{provider.work_end.slice(0, 5)}</option>)}</select>
        <select disabled={!filters.clinic_id} value={filters.room_id} onChange={(event) => setFilters({ ...filters, room_id: event.target.value })}><option value="">Odaberi prostoriju</option>{clinicRooms.map((room) => <option key={room.id} value={room.id}>{room.name}</option>)}</select>
      </div>
      <details className="secondary-filters">
        <summary>Dodatni filtri{filters.service_id || filters.status ? " · aktivni" : ""}</summary>
        <div className="filters">
          <select value={filters.service_id} onChange={(event) => setFilters({ ...filters, service_id: event.target.value })}><option value="">Sve usluge</option>{services.data.map((service) => <option key={service.id} value={service.id}>{service.name}</option>)}</select>
          <select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}><option value="">Svi statusi</option>{receptionStatuses.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}</select>
        </div>
      </details>
      {!resourcesReady && <p className="resource-filter-prompt">Odaberite kliniku, liječnika i prostoriju kako bi se prikazali stvarno slobodni termini.</p>}
      {resourcesReady && selectedProvider && <p className="resource-filter-ready">Slobodni termini po radnom vremenu liječnika: {selectedProvider.work_start.slice(0, 5)}–{selectedProvider.work_end.slice(0, 5)}.</p>}

      {view === "day" ? <div className="reception-grid reception-day-list">
        {visibleSlots.map((slot) => (
          <div key={slot.time} className={`reception-slot ${slot.empty ? "empty" : "occupied"}`}>
            <time>{slot.time}</time>
            {slot.appointment ? (
              <div className="reception-entry">
                <button className="reception-card reception-list-card" onClick={() => openAppointment(slot.appointment!)}>
                  <strong>{slot.appointment.patient ? formatPatientName(slot.appointment.patient) : `Pacijent #${slot.appointment.patient_id}`}</strong>
                  <span>{slot.appointment.service?.name ?? slot.appointment.service_id}</span>
                  <small>{slot.appointment.provider?.full_name ?? slot.appointment.provider_id}</small>
                  <small>{slot.appointment.room?.name ?? slot.appointment.room_id}</small>
                  <StatusBadge status={slot.appointment.status} />
                  <small>{slot.appointment.arrived_at ? "Dolazak evidentiran" : `${slot.appointment.start_time.slice(0, 5)}–${slot.appointment.end_time.slice(0, 5)}`}</small>
                </button>
                <button type="button" className="icon-button delete-icon-button" aria-label={`Obrisi termin u ${slot.appointment.start_time.slice(0, 5)}`} title="Obrisi termin" onClick={() => deleteAppointment(slot.appointment!)}>
                  <Trash2 size={18} aria-hidden="true" />
                </button>
              </div>
            ) : slot.empty && !isSunday(date) && resourcesReady && slotWithinProviderHours(slot.time) ? (
              <Link className="empty-slot empty-slot-action" to={`/appointments/new?${bookingParams(date, slot.time)}`} state={{ backgroundLocation: location }}>
                <span>Slobodno</span>
                <strong>Novi termin</strong>
              </Link>
            ) : <span className="empty-slot">{isSunday(date) ? "Neradni dan" : !resourcesReady ? "Odaberite resurse" : slot.empty ? "Izvan radnog vremena" : "Zauzeto"}</span>}
          </div>
        ))}
      </div> : (
        <div className="reception-week-wrap">
          <div className="reception-week-grid">
            {weekDates.map((weekDate) => {
              const dayAppointments = weekAppointments.filter((appointment) => appointment.date === weekDate);
              const freeTimes = isSunday(weekDate) || !selectedProvider ? [] : freeHalfHourTimes(dayAppointments, selectedProvider);
              return (
                <section className={`reception-week-day ${weekDate === today ? "today" : ""} ${isSunday(weekDate) ? "closed" : ""}`} key={weekDate}>
                  <header>
                    <button type="button" onClick={() => { setDate(weekDate); setView("day"); }}>{shortDate(weekDate)}</button>
                    <span>{dayAppointments.length}</span>
                  </header>
                  <div className="reception-week-items">
                    {dayAppointments.map((appointment) => (
                      <article className="reception-week-card" key={appointment.id}>
                        <button type="button" className="reception-week-main" onClick={() => openAppointment(appointment)}>
                          <time>{appointment.start_time.slice(0, 5)}</time>
                          <strong title={appointment.patient ? formatPatientName(appointment.patient) : undefined}>{appointment.patient ? formatPatientName(appointment.patient) : `Pacijent #${appointment.patient_id}`}</strong>
                          <span title={appointment.service?.name}>{appointment.service?.name ?? appointment.service_id}</span>
                          <small>{appointment.provider?.full_name ?? appointment.provider_id}</small>
                          <StatusBadge status={appointment.status} />
                        </button>
                        <button type="button" className="week-delete-button" aria-label={`Obrisi termin ${weekDate} u ${appointment.start_time.slice(0, 5)}`} title="Obrisi termin" onClick={() => deleteAppointment(appointment)}>
                          <Trash2 size={15} aria-hidden="true" />
                        </button>
                      </article>
                    ))}
                    {dayAppointments.length === 0 && <p className="week-empty">Nema upisanih pacijenata</p>}
                  </div>
                  {!isSunday(weekDate) && resourcesReady && (
                    <div className="week-free-slots">
                      <strong>Slobodno</strong>
                      <div>
                        {freeTimes.map((time) => (
                          <Link key={time} to={`/appointments/new?${bookingParams(weekDate, time)}`} state={{ backgroundLocation: location }}>{time}</Link>
                        ))}
                      </div>
                    </div>
                  )}
                  {isSunday(weekDate) && <span className="week-closed-label">Neradni dan</span>}
                </section>
              );
            })}
          </div>
        </div>
      )}

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
