import { ClipboardCheck, CreditCard, Filter, MoreVertical, PackageCheck, RefreshCw, Search, Stethoscope, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { DateInput } from "../components/DateInput";
import { ReceptionFloatingModal } from "../components/program2/ReceptionFloatingModal";
import { useApi } from "../hooks/useApi";
import type { Provider, Room, Service } from "../types";
import { formatUtcTimestampInClinic, getClinicToday } from "../utils/clinicTime";

type DashboardBlocker = { id: number; title: string; details: string | null; is_clinical: boolean };
type DashboardActivity = {
  id: number; sequence: number; time: string; end_time?: string;
  service_name: string; clinician_name: string | null; room_name: string | null; status: string;
};
type DashboardRow = {
  journey_id: number; appointment_id: number; time: string; patient_name: string;
  service_id: number; service_name: string; clinician_id: number; clinician_name: string;
  room_id: number; room_name: string; clinic_id: number | null; clinic_name: string | null;
  intake_channel: string; workflow_stage: string;
  document_status: string; preparation_status: string; arrival_status: string;
  check_in_status: string; encounter_status: string; consumables_status: string;
  billing_status: string; payment_status: string; blocker_status: string;
  blocker_labels: string[]; blockers: DashboardBlocker[]; allowed_actions: string[];
  reception_warning: boolean; reception_warning_details: string[];
  activity_count: number; current_activity_id: number | null; next_activity_id: number | null; activities: DashboardActivity[];
};
type DashboardClinic = { id: number; name: string };
type DashboardResponse = {
  date: string; refreshed_at: string; visible_sections: string[]; viewer_role: string;
  scope: string; scope_label: string; scoped_clinician_id: number | null;
  can_filter_clinician: boolean; available_clinics: DashboardClinic[]; rows: DashboardRow[];
};
type StatusTone = "gray" | "blue" | "red" | "orange" | "green";
type OperationalState = {
  tone: StatusTone; label: string; detail: string;
  action?: "reception" | "encounter" | "consumables" | "billing" | "open";
  actionLabel?: string; icon?: ReactNode;
};
type TimelineBlock = {
  row: DashboardRow; state: OperationalState; startMinutes: number; endMinutes: number;
  lane: number; laneCount: number; roomName: string;
};

const today = getClinicToday();
const dayStart = 7 * 60;
const dayEnd = 20 * 60;
const slotMinutes = 30;
const minimumBlockMinutes = 30;

const documentContext: Record<string, string> = {
  requested: "Ranije nalaze pacijent može donijeti na pregled; to ne blokira početak pregleda.",
  partial: "Dio nalaza je zaprimljen; ostalo se može pregledati tijekom pregleda.",
  review_required: "Nalazi čekaju liječnički pregled, ali nisu administrativni uvjet za dolazak.",
};

function minutesFromTime(value?: string | null) {
  if (!value) return Number.NaN;
  const [hours, minutes] = value.split(":").map(Number);
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return Number.NaN;
  return hours * 60 + minutes;
}

function formatMinutes(minutes: number) {
  const bounded = Math.max(0, minutes);
  const hours = Math.floor(bounded / 60);
  const mins = bounded % 60;
  return `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
}

function rowActivityWindow(row: DashboardRow) {
  const starts = (row.activities ?? []).map(activity => minutesFromTime(activity.time)).filter(Number.isFinite);
  const ends = (row.activities ?? []).map(activity => minutesFromTime(activity.end_time)).filter(Number.isFinite);
  const fallbackStart = minutesFromTime(row.time);
  const start = Math.min(...(starts.length ? starts : [fallbackStart]));
  const explicitEnd = ends.length ? Math.max(...ends) : Number.NaN;
  const end = Number.isFinite(explicitEnd) && explicitEnd > start ? explicitEnd : start + minimumBlockMinutes;
  return { start, end: Math.max(end, start + minimumBlockMinutes) };
}

function activityDurationLabel(activity: DashboardActivity) {
  const start = minutesFromTime(activity.time);
  const end = minutesFromTime(activity.end_time);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return activity.time.slice(0, 5);
  return `${formatMinutes(start)}–${formatMinutes(end)}`;
}

function operationalState(row: DashboardRow): OperationalState {
  const blocker = row.blockers[0];
  const redFlagCount = row.blockers.length + row.reception_warning_details.length;
  if (redFlagCount > 0) {
    const detail = [
      ...row.blockers.map(item => item.details || item.title),
      ...row.reception_warning_details,
    ].filter(Boolean).join("; ");
    const canOpenEncounter = row.allowed_actions.includes("open_encounter") && ["ready_for_clinician", "in_encounter"].includes(row.workflow_stage);
    return {
      tone: "red",
      label: row.workflow_stage === "ready_for_clinician" || row.workflow_stage === "in_encounter" ? "Čeka pregled/pretragu" : blocker?.title || "Crvena napomena",
      detail: detail || "Postoji odstupanje koje treba ljudsku provjeru.",
      action: canOpenEncounter ? "encounter" : row.allowed_actions.includes("open_check_in") ? "reception" : "open",
      actionLabel: canOpenEncounter ? "Otvori pregled" : row.allowed_actions.includes("open_check_in") ? "Otvori prijem" : "Otvori",
      icon: canOpenEncounter ? <Stethoscope size={15}/> : <ClipboardCheck size={15}/>,
    };
  }
  if (row.workflow_stage === "completed" && ["paid", "not_due", "cancelled"].includes(row.payment_status)) {
    return { tone: "green", label: "Završeno", detail: "Sve aktivnosti su završene i plaćanje je riješeno." };
  }
  if (row.workflow_stage === "completed") return { tone: "orange", label: "Čeka plaćanje", detail: "Klinički dio je završen; plaćanje još nije potpuno riješeno.", action: "billing", actionLabel: "Naplati", icon: <CreditCard size={15}/> };
  if (row.workflow_stage === "no_show") return { tone: "red", label: "Nije došao/la", detail: "Pacijent nije došao na termin." };
  if (row.workflow_stage === "procedure_completed") return { tone: "orange", label: "Čeka materijal", detail: "Treba potvrditi korišteni materijal.", action: row.allowed_actions.includes("record_consumables") ? "consumables" : "open", actionLabel: row.allowed_actions.includes("record_consumables") ? "Evidentiraj materijal" : "Otvori", icon: <PackageCheck size={15}/> };
  if (["awaiting_billing", "awaiting_payment"].includes(row.workflow_stage)) return { tone: "orange", label: row.workflow_stage === "awaiting_billing" ? "Čeka račun" : "Čeka plaćanje", detail: row.workflow_stage === "awaiting_billing" ? "Račun treba izraditi." : "Račun je izrađen i čeka plaćanje.", action: "billing", actionLabel: "Naplati", icon: <CreditCard size={15}/> };
  if (["ready_for_clinician", "in_encounter"].includes(row.workflow_stage)) return { tone: "blue", label: row.workflow_stage === "in_encounter" ? "Pregled u tijeku" : "Čeka pregled/pretragu", detail: row.workflow_stage === "in_encounter" ? "Klinički susret je otvoren." : "Prijem je završen; pacijent čeka liječnika ili pretragu.", action: row.allowed_actions.includes("open_encounter") ? "encounter" : "open", actionLabel: row.workflow_stage === "in_encounter" ? "Nastavi pregled" : "Otvori pregled", icon: <Stethoscope size={15}/> };
  if (["arrived", "check_in_review"].includes(row.workflow_stage)) return { tone: "blue", label: "Stigao", detail: "Otvorite prijem: opći podaci, potpis i kratka pitanja prije pregleda.", action: row.allowed_actions.includes("open_check_in") ? "reception" : "open", actionLabel: row.allowed_actions.includes("open_check_in") ? "Otvori prijem" : "Otvori", icon: <ClipboardCheck size={15}/> };
  if (["requested", "booked", "awaiting_forms", "awaiting_documents", "preparation_in_progress", "ready_for_arrival"].includes(row.workflow_stage)) return { tone: "gray", label: "Čeka dolazak", detail: documentContext[row.document_status] || "Pacijent je naručen; prijem počinje kad se javi tajnici ili sestri.", action: row.allowed_actions.includes("open_check_in") ? "reception" : "open", actionLabel: row.allowed_actions.includes("open_check_in") ? "Otvori prijem" : "Otvori", icon: <ClipboardCheck size={15}/> };
  return { tone: "gray", label: "Nije započeto", detail: "Nema trenutne operativne radnje.", action: "open", actionLabel: "Otvori" };
}

function StatusDot({ tone, label, detail }: { tone: StatusTone; label: string; detail: string }) {
  return (
    <span className="status-signal-wrap">
      <span className={`status-signal timeline-dot ${tone}`} tabIndex={0} aria-label={`${label}. ${detail}`} title={`${label}. ${detail}`}>
        <span className="sr-only">{label}</span>
        <span className="status-signal-tooltip" role="tooltip">{label}. {detail}</span>
      </span>
    </span>
  );
}

function buildTimelineBlocks(rows: DashboardRow[]) {
  const prepared = rows.map(row => {
    const state = operationalState(row);
    const window = rowActivityWindow(row);
    return { row, state, startMinutes: window.start, endMinutes: window.end, lane: 0, laneCount: 1, roomName: row.room_name || "Bez prostorije" };
  }).sort((a, b) => a.startMinutes - b.startMinutes || a.endMinutes - b.endMinutes);
  const lanes: number[] = [];
  for (const block of prepared) {
    let lane = lanes.findIndex(end => end <= block.startMinutes);
    if (lane === -1) {
      lane = lanes.length;
      lanes.push(block.endMinutes);
    } else {
      lanes[lane] = block.endMinutes;
    }
    block.lane = lane;
  }
  const laneCount = Math.max(1, lanes.length);
  return prepared.map(block => ({ ...block, laneCount }));
}

function visibleRange(blocks: TimelineBlock[]) {
  if (!blocks.length) return { start: dayStart, end: dayEnd };
  const earliest = Math.min(...blocks.map(block => block.startMinutes));
  const latest = Math.max(...blocks.map(block => block.endMinutes));
  return {
    start: Math.max(0, Math.min(dayStart, Math.floor(earliest / slotMinutes) * slotMinutes)),
    end: Math.min(24 * 60, Math.max(dayEnd, Math.ceil(latest / slotMinutes) * slotMinutes)),
  };
}

function timelineSlots(start: number, end: number) {
  const slots = [];
  for (let value = start; value <= end; value += slotMinutes) slots.push(value);
  return slots;
}

function primaryRoomName(row: DashboardRow, preferredRoomName?: string) {
  const activities = [...(row.activities ?? [])].sort((a, b) => minutesFromTime(a.time) - minutesFromTime(b.time));
  if (preferredRoomName && activities.some(activity => activity.room_name === preferredRoomName)) return preferredRoomName;
  return activities.find(activity => activity.room_name)?.room_name || row.room_name || "Bez prostorije";
}

function focusFor(state: OperationalState) {
  if (state.action === "reception") return "arrival";
  if (state.action === "encounter") return "encounter";
  if (state.action === "consumables") return "consumables";
  if (state.action === "billing") return "billing";
  return "attention";
}

function RedFlagButton({ row }: { row: DashboardRow }) {
  const [open, setOpen] = useState(false);
  const count = row.blockers.length + row.reception_warning_details.length;
  if (count === 0) return <span className="timeline-red-flag clear">0 napomena</span>;
  return (
    <span className="timeline-red-flag-wrap">
      <button type="button" className="timeline-red-flag" onClick={() => setOpen(value => !value)} aria-expanded={open} aria-haspopup="dialog">
        {count} crvenih napomena
      </button>
      {open && (
        <div className="timeline-flag-popover" role="dialog" aria-label={`Crvene napomene za ${row.patient_name}`}>
          <header>
            <strong>Crvene napomene</strong>
            <button type="button" onClick={() => setOpen(false)} aria-label="Zatvori crvene napomene">×</button>
          </header>
          {row.blockers.map(item => (
            <article key={`blocker-${item.id}`}>
              <b>{item.title}</b>
              <p>{item.details || (item.is_clinical ? "Potrebna je liječnička odluka." : "Potrebna je operativna provjera.")}</p>
            </article>
          ))}
          {row.reception_warning_details.map((detail, index) => (
            <article key={`reception-${index}`}>
              <b>Prijemna napomena</b>
              <p>{detail}</p>
            </article>
          ))}
        </div>
      )}
    </span>
  );
}

function PatientBlock({
  block,
  rangeStart,
  onPrimaryAction,
  actionRef,
}: {
  block: TimelineBlock;
  rangeStart: number;
  onPrimaryAction: (row: DashboardRow, state: OperationalState) => void;
  actionRef?: (element: HTMLButtonElement | null) => void;
}) {
  const { row, state } = block;
  const top = ((block.startMinutes - rangeStart) / slotMinutes) * 52 + 8;
  const height = Math.max(48, ((block.endMinutes - block.startMinutes) / slotMinutes) * 52 - 8);
  const laneWidthPercent = 100 / block.laneCount;
  const width = `calc(${laneWidthPercent}% - ${((block.laneCount - 1) * 10) / block.laneCount}px)`;
  const left = `calc(${block.lane * laneWidthPercent}% + ${(block.lane * 10) / block.laneCount}px)`;
  const actionCount = state.action ? 1 : 0;
  return (
    <article
      className={`timeline-patient-block tone-${state.tone}`}
      style={{ top, height, width, left }}
      aria-label={`${formatMinutes(block.startMinutes)} ${row.patient_name}. ${state.label}. ${state.detail}`}
    >
      <header>
        <div className="timeline-patient-title">
          <StatusDot tone={state.tone} label={state.label} detail={state.detail}/>
          <button type="button" className="link-button patient-name-button" onClick={() => onPrimaryAction(row, state)}>{row.patient_name}</button>
        </div>
        <time>{formatMinutes(block.startMinutes)}</time>
      </header>
      <div className="timeline-activity-list" aria-label={`Današnje aktivnosti za ${row.patient_name}`}>
        {(row.activities?.length ? row.activities : [{ id: row.appointment_id, sequence: 1, time: row.time, end_time: formatMinutes(block.endMinutes), service_name: row.service_name, clinician_name: row.clinician_name, room_name: row.room_name, status: row.workflow_stage }]).map(activity => (
          <div className="timeline-activity-row" key={activity.id}>
            <time>{activityDurationLabel(activity)}</time>
            <span>{activity.service_name}</span>
            <small>{activity.room_name || "Bez prostorije"}</small>
          </div>
        ))}
      </div>
      <footer>
        <span className="timeline-state-label">{state.label}</span>
        <RedFlagButton row={row}/>
        <div className="timeline-actions">
          {state.action && <button type="button" ref={actionRef} className="primary" onClick={() => onPrimaryAction(row, state)}>{state.icon}{state.actionLabel}</button>}
          <details className="timeline-more-menu">
            <summary aria-label={`Dodatne radnje za ${row.patient_name}`}><MoreVertical size={16}/></summary>
            <div>
              <button type="button" onClick={() => onPrimaryAction(row, { ...state, action: "open", actionLabel: "Otvori tijek" })}>Otvori tijek</button>
              {state.action !== "encounter" && row.allowed_actions.includes("open_encounter") && <button type="button" onClick={() => onPrimaryAction(row, { ...state, action: "encounter", actionLabel: "Otvori pregled" })}>Otvori pregled</button>}
              {state.action !== "reception" && row.allowed_actions.includes("open_check_in") && <button type="button" onClick={() => onPrimaryAction(row, { ...state, action: "reception", actionLabel: "Otvori prijem" })}>Otvori prijem</button>}
            </div>
          </details>
        </div>
        <span className="sr-only">Broj primarnih radnji: {actionCount > 0 ? 1 : 0}</span>
      </footer>
    </article>
  );
}

export function DailyClinicDashboard() {
  const navigate = useNavigate();
  const [day, setDay] = useState(today);
  const [clinician, setClinician] = useState(""); const [clinic, setClinic] = useState(""); const [room, setRoom] = useState(""); const [service, setService] = useState("");
  const [stage, setStage] = useState(""); const [blocker, setBlocker] = useState(""); const [query, setQuery] = useState("");
  const [view, setView] = useState<"patients" | "rooms">("patients");
  const [refresh, setRefresh] = useState(0);
  const [receptionJourneyId, setReceptionJourneyId] = useState<number | null>(null);
  const receptionActionRefs = useRef<Record<number, HTMLButtonElement | null>>({});
  const params = new URLSearchParams({ selected_date: day, refresh: String(refresh) });
  if (clinician) params.set("clinician_id", clinician); if (clinic) params.set("clinic_id", clinic); if (room) params.set("room_id", room); if (service) params.set("service_id", service);
  if (stage) params.set("status", stage); if (blocker) params.set("blocker", blocker); if (query.trim()) params.set("q", query.trim());
  const board = useApi<DashboardResponse>(`/api/dashboard/day?${params}`, { date: day, refreshed_at: "", visible_sections: [], viewer_role: "", scope: "", scope_label: "", scoped_clinician_id: null, can_filter_clinician: false, available_clinics: [], rows: [] });
  const providers = useApi<Provider[]>("/api/providers", []); const rooms = useApi<Room[]>("/api/rooms", []); const services = useApi<Service[]>("/api/services", []);
  useEffect(() => {
    if (clinic && !board.data.available_clinics.some(item => String(item.id) === clinic)) setClinic("");
  }, [board.data.available_clinics, clinic]);

  const blocks = useMemo(() => buildTimelineBlocks(board.data.rows), [board.data.rows]);
  const range = useMemo(() => visibleRange(blocks), [blocks]);
  const slots = useMemo(() => timelineSlots(range.start, range.end), [range]);
  const timelineHeight = ((range.end - range.start) / slotMinutes) * 52 + 24;
  const counts = useMemo(() => ({
    total: board.data.rows.length,
    active: board.data.rows.filter(row => ["blue", "orange"].includes(operationalState(row).tone)).length,
    problems: board.data.rows.filter(row => operationalState(row).tone === "red").length,
  }), [board.data.rows]);
  const advancedFilterCount = [clinic, room, service, stage].filter(Boolean).length;
  const selectedRoomName = useMemo(() => rooms.data.find(item => String(item.id) === room)?.name, [room, rooms.data]);
  const roomGroups = useMemo(() => {
    const grouped = new Map<string, DashboardRow[]>();
    for (const row of board.data.rows) {
      const name = primaryRoomName(row, selectedRoomName);
      grouped.set(name, [...(grouped.get(name) ?? []), row]);
    }
    return [...grouped.entries()].map(([roomName, rows]) => ({ roomName, blocks: buildTimelineBlocks(rows) })).sort((a, b) => a.roomName.localeCompare(b.roomName));
  }, [board.data.rows, selectedRoomName]);

  function journeyHref(row: DashboardRow, state: OperationalState) {
    const focus = focusFor(state);
    return `/journeys/${row.journey_id}?focus=${focus}${state.action === "reception" ? "&reception=1" : ""}`;
  }
  function runAction(row: DashboardRow, state: OperationalState) {
    if (state.action === "reception") {
      setReceptionJourneyId(row.journey_id);
      return;
    }
    navigate(journeyHref(row, state));
  }
  function closeReceptionModal(refreshBoard = false) {
    const focusedJourneyId = receptionJourneyId;
    setReceptionJourneyId(null);
    if (refreshBoard) setRefresh(value => value + 1);
    window.setTimeout(() => {
      if (focusedJourneyId != null) receptionActionRefs.current[focusedJourneyId]?.focus();
    }, 0);
  }
  function clearFilters() {
    setClinician(""); setClinic(""); setRoom(""); setService(""); setStage(""); setBlocker(""); setQuery("");
  }

  return <section className="page clinic-day-page">
    <header className="clinic-day-header">
      <div><span className="eyebrow">Dnevni operativni pregled</span><h1>Danas u poliklinici</h1><p>Tko je sljedeći, postoji li problem i što sada treba napraviti.</p><span className="clinic-day-scope">Prikaz: {board.data.scope_label || "učitavanje…"}</span></div>
      <div className="clinic-day-date"><DateInput value={day} onChange={setDay} required/><button type="button" onClick={() => setRefresh(value => value + 1)}><RefreshCw size={16}/>Osvježi</button></div>
    </header>
    <div className="clinic-day-summary"><span><b>{counts.total}</b> dolazaka</span><span><b>{counts.active}</b> u tijeku</span><span className={counts.problems ? "attention" : ""}><b>{counts.problems}</b> s problemom</span><small>Zadnje osvježenje: {formatUtcTimestampInClinic(board.data.refreshed_at)}</small></div>
    <div className="clinic-day-view-toggle" role="group" aria-label="Način prikaza"><button type="button" className={view === "patients" ? "active" : ""} onClick={() => setView("patients")}>Po pacijentima</button><button type="button" className={view === "rooms" ? "active" : ""} onClick={() => setView("rooms")}>Po prostorijama</button></div>
    <div className="clinic-day-filter-bar"><label className="clinic-day-search"><Search size={16}/><input aria-label="Pretraži pacijenta" placeholder="Pretraži pacijenta" value={query} onChange={event => setQuery(event.target.value)}/></label>{board.data.can_filter_clinician && <select aria-label="Liječnik" value={clinician} onChange={event => { setClinician(event.target.value); setClinic(""); setRoom(""); }}><option value="">Svi liječnici</option>{providers.data.filter(item => item.staff_role === "physician").map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select>}<select aria-label="Problem" value={blocker} onChange={event => setBlocker(event.target.value)}><option value="">Sva stanja</option><option value="true">S problemom</option><option value="false">Bez problema</option></select><details className="clinic-day-advanced"><summary><Filter size={15}/>Dodatni filtri{advancedFilterCount > 0 && <b aria-label={`${advancedFilterCount} aktivna dodatna filtra`}>{advancedFilterCount}</b>}</summary><div className="clinic-day-filters">{board.data.available_clinics.length > 1 && <select aria-label="Klinika" value={clinic} onChange={event => { setClinic(event.target.value); setRoom(""); }}><option value="">Sve klinike</option>{board.data.available_clinics.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>}<select aria-label="Prostorija" value={room} onChange={event => setRoom(event.target.value)}><option value="">Sve prostorije</option>{rooms.data.filter(item => !clinic || String(item.clinic_id ?? "") === clinic).map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select aria-label="Usluga" value={service} onChange={event => setService(event.target.value)}><option value="">Sve usluge</option>{services.data.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select aria-label="Faza" value={stage} onChange={event => setStage(event.target.value)}><option value="">Sve faze</option><option value="ready_for_arrival">Čeka dolazak</option><option value="check_in_review">Stigao</option><option value="ready_for_clinician">Čeka pregled/pretragu</option><option value="in_encounter">Pregled u tijeku</option><option value="awaiting_payment">Čeka naplatu</option></select></div></details>{[clinician, clinic, room, service, stage, blocker, query].some(Boolean) && <button type="button" className="clear-filters" onClick={clearFilters}><X size={15}/>Očisti filtre</button>}</div>
    {board.error && <p className="form-error">Dnevni pregled nije učitan: {board.error}</p>}
    {view === "patients" ? (
      <div className="clinic-timeline-card">
        <div className="clinic-timeline-head" role="row"><div>Vrijeme</div><div>Dolazak pacijenta</div></div>
        <div className="clinic-timeline" style={{ minHeight: timelineHeight }}>
          <div className="clinic-time-axis" aria-label="Vremenska os">
            {slots.map(slot => <div className="clinic-time-slot" key={slot} style={{ top: ((slot - range.start) / slotMinutes) * 52 }}><time>{formatMinutes(slot)}</time></div>)}
          </div>
          <div className="clinic-timeline-stage" aria-label="Dnevni raspored po vremenu">
            {slots.map(slot => <div className="clinic-timeline-line" key={slot} style={{ top: ((slot - range.start) / slotMinutes) * 52 }}/>)}
            {blocks.map(block => <PatientBlock key={block.row.journey_id} block={block} rangeStart={range.start} onPrimaryAction={runAction} actionRef={element => { receptionActionRefs.current[block.row.journey_id] = element; }}/>)}
            {!board.loading && !blocks.length && <p className="clinic-day-empty">Za odabrani dan i filtre nema dolazaka.</p>}
          </div>
        </div>
      </div>
    ) : (
      <div className="clinic-room-timeline-wrap">
        <div className="clinic-room-timelines" style={{ minHeight: timelineHeight }}>
          <div className="clinic-time-axis room-axis" aria-label="Vremenska os prostorija">
            {slots.map(slot => <div className="clinic-time-slot" key={slot} style={{ top: ((slot - range.start) / slotMinutes) * 52 }}><time>{formatMinutes(slot)}</time></div>)}
          </div>
          {roomGroups.map(group => (
            <section className="clinic-room-column" key={group.roomName} aria-label={`Raspored prostorije ${group.roomName}`}>
              <header>{group.roomName}</header>
              <div className="clinic-room-column-stage">
                {slots.map(slot => <div className="clinic-timeline-line" key={slot} style={{ top: ((slot - range.start) / slotMinutes) * 52 }}/>)}
                {group.blocks.map(block => <PatientBlock key={`${group.roomName}-${block.row.journey_id}`} block={{ ...block, laneCount: Math.max(1, block.laneCount) }} rangeStart={range.start} onPrimaryAction={runAction}/>)}
              </div>
            </section>
          ))}
          {!roomGroups.length && <p className="clinic-day-empty">Za odabrani dan nema raspoređenih prostorija.</p>}
        </div>
      </div>
    )}
    <p className="clinic-day-legend">
      <StatusDot tone="gray" label="Nije stigao" detail="Pacijent još nije evidentiran u poliklinici."/> nije stigao
      <StatusDot tone="blue" label="U tijeku" detail="Pacijent je stigao, čeka ili je pregled u tijeku."/> u tijeku
      <StatusDot tone="red" label="Problem" detail="Postoji crvena napomena ili neriješen problem."/> problem
      <StatusDot tone="orange" label="Čeka naplatu" detail="Čeka materijal, račun ili plaćanje."/> naplata/materijal
      <StatusDot tone="green" label="Završeno" detail="Aktivnosti i plaćanje su riješeni."/> završeno
    </p>
    <ReceptionFloatingModal journeyId={receptionJourneyId} open={receptionJourneyId !== null} onClose={() => closeReceptionModal(false)} onCompleted={() => closeReceptionModal(true)} />
  </section>;
}
