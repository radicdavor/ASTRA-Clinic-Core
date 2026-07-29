import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Trash2 } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { ConfirmActionDialog } from "../components/ConfirmActionDialog";
import { DateInput } from "../components/DateInput";
import { HelpHint } from "../components/HelpHint";
import { StatusBadge, statusLabel } from "../components/StatusBadge";
import { useClinicContext } from "../contexts/ClinicContext";
import { useApi } from "../hooks/useApi";
import { Appointment, Clinic, Provider, ReceptionSlot, Room, Service } from "../types";
import { getClinicTodayForTimezone } from "../utils/clinicTime";
import { formatDate } from "../utils/date";
import { formatPatientName } from "../utils/patientIdentity";
import { providerHoursForDate } from "../utils/providerSchedule";
import {
  formatShortCalendarDate,
  isCalendarSunday,
  mondayOfCalendarWeek,
  moveCalendarDate,
} from "../utils/receptionDate";

const receptionStatuses = ["scheduled", "confirmed", "arrived", "in_progress", "completed", "cancelled", "no_show"];
const blockingReceptionStatuses = new Set(["scheduled", "confirmed", "arrived", "in_progress", "waiting_for_result", "follow_up_needed", "rescheduled"]);
const halfHourTimes = Array.from({ length: 29 }, (_, index) => {
  const minutes = 7 * 60 + index * 30;
  return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
});

function isHalfHour(time: string) {
  const minutes = Number(time.slice(3, 5));
  return minutes === 0 || minutes === 30;
}

function timeToMinutes(value: string) {
  const [hours, minutes] = value.slice(0, 5).split(":").map(Number);
  return hours * 60 + minutes;
}

function freeHalfHourTimes(appointments: Appointment[], provider: Provider, date: string) {
  const hours = providerHoursForDate(provider, date);
  if (!hours.enabled) return [];
  return halfHourTimes.filter((time) => {
    const start = timeToMinutes(time);
    const end = start + 30;
    const withinWorkingHours = start >= timeToMinutes(hours.start) && end <= timeToMinutes(hours.end);
    return withinWorkingHours && !appointments.some((appointment) => blockingReceptionStatuses.has(appointment.status)
      && timeToMinutes(appointment.start_time) < end
      && timeToMinutes(appointment.end_time) > start);
  });
}

export function Reception() {
  const location = useLocation();
  const clinicContext = useClinicContext();
  const [dateMode, setDateMode] = useState<"date_auto_today" | "date_user_selected">("date_auto_today");
  const [selectedDate, setSelectedDate] = useState("");
  const [clockInstant, setClockInstant] = useState(() => Date.now());
  const [view, setView] = useState<"day" | "week">("day");
  const [filters, setFilters] = useState({ clinic_id: "", room_id: "", provider_id: "", service_id: "", status: "" });
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Appointment | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Appointment | null>(null);
  const [patientDraft, setPatientDraft] = useState({ first_name: "", last_name: "", date_of_birth: "", oib: "", phone: "", email: "" });
  const directRefreshControllerRef = useRef<AbortController | null>(null);
  const directRefreshGenerationRef = useRef(0);
  const activeRefreshKeyRef = useRef("");
  const clinicIdentityReady = clinicContext.status === "clinic_context_ready" && clinicContext.clinicId !== null;
  const clinicDateState = useMemo(() => {
    if (!clinicIdentityReady) return { date: "", error: null };
    if (!clinicContext.timezone?.trim()) {
      return {
        date: "",
        error: "Aktivna klinika nema postavljenu vremensku zonu. Prijem je zaustavljen dok se postavka ne ispravi.",
      };
    }
    try {
      return {
        date: getClinicTodayForTimezone(clinicContext.timezone, new Date(clockInstant)),
        error: null,
      };
    } catch {
      return {
        date: "",
        error: "Vremenska zona aktivne klinike nije valjana. Prijem je zaustavljen dok se postavka ne ispravi.",
      };
    }
  }, [clinicIdentityReady, clinicContext.timezone, clockInstant]);
  const clinicContextReady = clinicIdentityReady && clinicDateState.error === null && clinicDateState.date !== "";
  const automaticClinicDate = clinicDateState.date;
  const date = dateMode === "date_auto_today" ? automaticClinicDate : selectedDate;
  const clinicRequestKey = clinicContextReady ? clinicContext.clinicId : null;
  const activeClinicFilterId = clinicContextReady ? clinicContext.clinicId! : "";
  const filtersMatchActiveClinic = filters.clinic_id === activeClinicFilterId;
  const scopedProviderFilterId = filtersMatchActiveClinic ? filters.provider_id : "";
  const scopedRoomFilterId = filtersMatchActiveClinic ? filters.room_id : "";
  useEffect(() => {
    setFilters((current) => {
      if (!clinicContextReady) {
        return current.clinic_id || current.provider_id || current.room_id
          ? { ...current, clinic_id: "", provider_id: "", room_id: "" }
          : current;
      }
      return current.clinic_id === clinicContext.clinicId
        ? current
        : { ...current, clinic_id: clinicContext.clinicId!, provider_id: "", room_id: "" };
    });
    setSelected(null);
    setDeleteTarget(null);
  }, [clinicContextReady, clinicContext.clinicId]);
  const clinics = useApi<Clinic[]>(clinicContextReady ? "/api/clinics" : null, [], clinicRequestKey);
  const rooms = useApi<Room[]>(clinicContextReady ? "/api/rooms" : null, [], clinicRequestKey);
  const providers = useApi<Provider[]>(clinicContextReady ? "/api/providers" : null, [], clinicRequestKey);
  const services = useApi<Service[]>(clinicContextReady ? "/api/services" : null, [], clinicRequestKey);
  useEffect(() => {
    if (!clinicContextReady || dateMode !== "date_auto_today") return;
    const updateAtClinicDateBoundary = window.setInterval(() => {
      setClockInstant(Date.now());
    }, 60_000);
    return () => window.clearInterval(updateAtClinicDateBoundary);
  }, [clinicContextReady, clinicContext.clinicId, clinicContext.timezone, dateMode]);
  const query = useMemo(() => {
    const params = new URLSearchParams({ date });
    Object.entries({
      ...filters,
      clinic_id: activeClinicFilterId,
      provider_id: scopedProviderFilterId,
      room_id: scopedRoomFilterId,
    }).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    return `/api/reception/day?${params.toString()}`;
  }, [date, filters, activeClinicFilterId, scopedProviderFilterId, scopedRoomFilterId]);
  const slots = useApi<ReceptionSlot[]>(clinicContextReady && date ? query : null, [], clinicRequestKey);
  const weekDates = useMemo(() => {
    if (!date) return [];
    const monday = mondayOfCalendarWeek(date);
    return Array.from({ length: 7 }, (_, index) => moveCalendarDate(monday, index));
  }, [date]);
  const weekQuery = useMemo(() => {
    if (weekDates.length !== 7) return "";
    const params = new URLSearchParams({ date_from: weekDates[0], date_to: weekDates[6] });
    if (scopedRoomFilterId) params.set("room_id", scopedRoomFilterId);
    if (scopedProviderFilterId) params.set("provider_id", scopedProviderFilterId);
    if (filters.status) params.set("status", filters.status);
    return `/api/appointments?${params.toString()}`;
  }, [weekDates, scopedRoomFilterId, scopedProviderFilterId, filters.status]);
  const weekData = useApi<Appointment[]>(clinicContextReady && date ? weekQuery : null, [], clinicRequestKey);
  const weekAppointments = useMemo(() => weekData.data.filter((appointment) => {
    if (filters.service_id && String(appointment.service_id) !== filters.service_id) return false;
    if (activeClinicFilterId) {
      const clinicId = appointment.room?.clinic_id ?? appointment.provider?.clinic_id;
      if (String(clinicId ?? "") !== activeClinicFilterId) return false;
    }
    return true;
  }), [weekData.data, filters.service_id, activeClinicFilterId]);
  const clinicProviders = useMemo(() => providers.data.filter((provider) => provider.staff_role === "physician" && String(provider.clinic_id ?? "") === activeClinicFilterId), [providers.data, activeClinicFilterId]);
  const clinicRooms = useMemo(() => rooms.data.filter((room) => String(room.clinic_id ?? "") === activeClinicFilterId), [rooms.data, activeClinicFilterId]);
  const selectedProvider = useMemo(() => providers.data.find((provider) => String(provider.id) === scopedProviderFilterId), [providers.data, scopedProviderFilterId]);
  const resourcesReady = Boolean(activeClinicFilterId && scopedProviderFilterId && scopedRoomFilterId && selectedProvider);
  const visibleSlots = useMemo(
    () => slots.data.filter((slot) => Boolean(slot.appointment) || (resourcesReady && slot.empty && isHalfHour(slot.time))),
    [slots.data, resourcesReady]
  );
  const selectedProviderHours = selectedProvider ? providerHoursForDate(selectedProvider, date) : null;
  const slotWithinProviderHours = (time: string) => Boolean(selectedProviderHours?.enabled
    && timeToMinutes(time) >= timeToMinutes(selectedProviderHours.start)
    && timeToMinutes(time) + 30 <= timeToMinutes(selectedProviderHours.end));
  const bookingParams = (bookingDate: string, startTime: string) => new URLSearchParams({
    date: bookingDate,
    start_time: startTime,
    clinic_id: activeClinicFilterId,
    provider_id: scopedProviderFilterId,
    room_id: scopedRoomFilterId,
  }).toString();

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

  const directRefreshKey = clinicContextReady && date
    ? `${clinicContext.clinicId}|${date}|${query}|${weekQuery}`
    : "";
  useEffect(() => {
    directRefreshGenerationRef.current += 1;
    directRefreshControllerRef.current?.abort();
    directRefreshControllerRef.current = null;
    activeRefreshKeyRef.current = directRefreshKey;
    setRefreshError(null);
    return () => {
      directRefreshGenerationRef.current += 1;
      directRefreshControllerRef.current?.abort();
      directRefreshControllerRef.current = null;
    };
  }, [directRefreshKey]);

  const refresh = useCallback(async () => {
    const capturedKey = directRefreshKey;
    if (!capturedKey || activeRefreshKeyRef.current !== capturedKey) return;
    directRefreshControllerRef.current?.abort();
    const controller = new AbortController();
    const generation = ++directRefreshGenerationRef.current;
    directRefreshControllerRef.current = controller;
    setRefreshError(null);
    try {
      const [nextSlots, nextWeek] = await Promise.all([
        api<ReceptionSlot[]>(query, { signal: controller.signal, suppressErrorToast: true }),
        api<Appointment[]>(weekQuery, { signal: controller.signal, suppressErrorToast: true }),
      ]);
      if (
        !controller.signal.aborted
        && generation === directRefreshGenerationRef.current
        && capturedKey === activeRefreshKeyRef.current
      ) {
        slots.setData(nextSlots);
        weekData.setData(nextWeek);
      }
    } catch (error) {
      if (
        !controller.signal.aborted
        && generation === directRefreshGenerationRef.current
        && capturedKey === activeRefreshKeyRef.current
      ) {
        setRefreshError(error instanceof Error ? error.message : "Raspored nije osvježen.");
      }
    } finally {
      if (generation === directRefreshGenerationRef.current) directRefreshControllerRef.current = null;
    }
  }, [directRefreshKey, query, weekQuery, slots.setData, weekData.setData]);

  useEffect(() => {
    function refreshAfterAppointmentChange() {
      void refresh();
    }
    window.addEventListener("astra:appointments-changed", refreshAfterAppointmentChange);
    return () => window.removeEventListener("astra:appointments-changed", refreshAfterAppointmentChange);
  }, [refresh]);

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

  async function deleteAppointment() {
    if (!deleteTarget) return;
    await api(`/api/appointments/${deleteTarget.id}`, { method: "DELETE" });
    if (selected?.id === deleteTarget.id) setSelected(null);
    setDeleteTarget(null);
    await refresh();
  }
  const deletePatientName = deleteTarget ? (deleteTarget.patient ? formatPatientName(deleteTarget.patient) : `pacijenta #${deleteTarget.patient_id}`) : "";

  const hasIdentityDetails = Boolean(
    patientDraft.first_name.trim()
    && patientDraft.last_name.trim()
    && (patientDraft.date_of_birth || patientDraft.oib || patientDraft.phone || patientDraft.email)
  );
  const canMarkArrived = Boolean(selected && ["scheduled", "confirmed"].includes(selected.status) && hasIdentityDetails);
  const canStartService = Boolean(selected && selected.status === "arrived" && selected.identity_verified_at);

  if (!clinicIdentityReady) {
    return (
      <section className="page-card clinic-context-empty" aria-live="polite">
        <h1>Učitavanje klinike</h1>
        <p>Prijem čeka aktivnu kliniku i njezinu vremensku zonu prije učitavanja dnevnog rasporeda.</p>
      </section>
    );
  }

  if (clinicDateState.error) {
    return (
      <section className="page-card clinic-context-empty" aria-live="assertive">
        <h1>Vremenska zona klinike nije dostupna</h1>
        <p>{clinicDateState.error}</p>
      </section>
    );
  }

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
          <button type="button" className="action-button" onClick={() => { setSelectedDate(moveCalendarDate(date, view === "week" ? -7 : -1)); setDateMode("date_user_selected"); }}>Prethodni {view === "week" ? "tjedan" : "dan"}</button>
          <button type="button" className="action-button" onClick={() => { setClockInstant(Date.now()); setDateMode("date_auto_today"); }}>Danas</button>
          <DateInput required value={date} onChange={(value) => { setSelectedDate(value); setDateMode("date_user_selected"); }} />
          <button type="button" className="action-button" onClick={() => { setSelectedDate(moveCalendarDate(date, view === "week" ? 7 : 1)); setDateMode("date_user_selected"); }}>Sljedeći {view === "week" ? "tjedan" : "dan"}</button>
        </div>
      </div>

      <div className="segmented-control">
        <button className={view === "day" ? "active" : ""} onClick={() => setView("day")}>Dan</button>
        <button className={view === "week" ? "active" : ""} onClick={() => setView("week")}>Tjedan</button>
      </div>

      <div className="filters reception-resource-filters">
        <select aria-label="Aktivna klinika" disabled value={activeClinicFilterId}><option value={activeClinicFilterId}>{clinics.data.find((clinic) => String(clinic.id) === activeClinicFilterId)?.name ?? `Klinika #${activeClinicFilterId}`}</option></select>
        <select disabled={!filters.clinic_id} value={filters.provider_id} onChange={(event) => setFilters({ ...filters, provider_id: event.target.value })}><option value="">Odaberi liječnika</option>{clinicProviders.map((provider) => { const hours=providerHoursForDate(provider,date); return <option key={provider.id} value={provider.id}>{provider.full_name} · {hours.enabled?`${hours.start}–${hours.end}`:"ne radi"}</option>; })}</select>
        <select disabled={!filters.clinic_id} value={filters.room_id} onChange={(event) => setFilters({ ...filters, room_id: event.target.value })}><option value="">Odaberi prostoriju</option>{clinicRooms.map((room) => <option key={room.id} value={room.id}>{room.name}</option>)}</select>
      </div>
      <details className="secondary-filters">
        <summary>Dodatni filtri{filters.service_id || filters.status ? " · aktivni" : ""}</summary>
        <div className="filters">
          <select value={filters.service_id} onChange={(event) => setFilters({ ...filters, service_id: event.target.value })}><option value="">Sve usluge</option>{services.data.map((service) => <option key={service.id} value={service.id}>{service.name}</option>)}</select>
          <select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}><option value="">Svi statusi</option>{receptionStatuses.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}</select>
        </div>
      </details>
      {refreshError && <p className="form-error" role="alert">{refreshError}</p>}
      {!resourcesReady && <p className="resource-filter-prompt">Odaberite kliniku, liječnika i prostoriju kako bi se prikazali stvarno slobodni termini.</p>}
      {resourcesReady && selectedProviderHours && <p className="resource-filter-ready">{selectedProviderHours.enabled ? `Slobodni termini po radnom vremenu liječnika: ${selectedProviderHours.start}–${selectedProviderHours.end}.` : "Liječnik ne radi odabranog dana."}</p>}

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
                <button type="button" className="icon-button delete-icon-button" aria-label={`Obrisi termin u ${slot.appointment.start_time.slice(0, 5)}`} title="Obrisi termin" onClick={() => setDeleteTarget(slot.appointment!)}>
                  <Trash2 size={18} aria-hidden="true" />
                </button>
              </div>
            ) : slot.empty && !isCalendarSunday(date) && resourcesReady && slotWithinProviderHours(slot.time) ? (
              <Link className="empty-slot empty-slot-action" to={`/appointments/new?${bookingParams(date, slot.time)}`} state={{ backgroundLocation: location }}>
                <span>Slobodno</span>
                <strong>Novi termin</strong>
              </Link>
            ) : <span className="empty-slot">{isCalendarSunday(date) ? "Neradni dan" : !resourcesReady ? "Odaberite resurse" : slot.empty ? "Izvan radnog vremena" : "Zauzeto"}</span>}
          </div>
        ))}
      </div> : (
        <div className="reception-week-wrap">
          <div className="reception-week-grid">
            {weekDates.map((weekDate) => {
              const dayAppointments = weekAppointments.filter((appointment) => appointment.date === weekDate);
              const freeTimes = isCalendarSunday(weekDate) || !selectedProvider ? [] : freeHalfHourTimes(dayAppointments, selectedProvider, weekDate);
              return (
                <section className={`reception-week-day ${weekDate === automaticClinicDate ? "today" : ""} ${isCalendarSunday(weekDate) ? "closed" : ""}`} key={weekDate}>
                  <header>
                    <button type="button" onClick={() => { setSelectedDate(weekDate); setDateMode("date_user_selected"); setView("day"); }}>{formatShortCalendarDate(weekDate)}</button>
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
                        <button type="button" className="week-delete-button" aria-label={`Obrisi termin ${weekDate} u ${appointment.start_time.slice(0, 5)}`} title="Obrisi termin" onClick={() => setDeleteTarget(appointment)}>
                          <Trash2 size={15} aria-hidden="true" />
                        </button>
                      </article>
                    ))}
                    {dayAppointments.length === 0 && <p className="week-empty">Nema upisanih pacijenata</p>}
                  </div>
                  {!isCalendarSunday(weekDate) && resourcesReady && (
                    <div className="week-free-slots">
                      <strong>Slobodno</strong>
                      <div>
                        {freeTimes.map((time) => (
                          <Link key={time} to={`/appointments/new?${bookingParams(weekDate, time)}`} state={{ backgroundLocation: location }}>{time}</Link>
                        ))}
                      </div>
                    </div>
                  )}
                  {isCalendarSunday(weekDate) && <span className="week-closed-label">Neradni dan</span>}
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
      <ConfirmActionDialog
        open={Boolean(deleteTarget)}
        title="Obrisati termin"
        message={deleteTarget ? `Obrisati termin ${deleteTarget.start_time.slice(0, 5)} za ${deletePatientName}? Pacijent ostaje u evidenciji.` : ""}
        confirmLabel="Obriši termin"
        onCancel={() => setDeleteTarget(null)}
        onConfirm={deleteAppointment}
      />
    </section>
  );
}
