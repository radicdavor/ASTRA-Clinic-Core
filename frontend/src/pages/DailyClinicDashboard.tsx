import { ClipboardCheck, CreditCard, Filter, PackageCheck, RefreshCw, Search, Stethoscope, X } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { DateInput } from "../components/DateInput";
import { useApi } from "../hooks/useApi";
import type { Provider, Room, Service } from "../types";

type DashboardBlocker = { id: number; title: string; details: string | null; is_clinical: boolean };
type DashboardActivity = { id: number; sequence: number; time: string; service_name: string; clinician_name: string | null; room_name: string | null; status: string };
type DashboardRow = {
  journey_id: number; appointment_id: number; time: string; patient_name: string;
  service_id: number; service_name: string; clinician_id: number; clinician_name: string;
  room_id: number; room_name: string; clinic_id: number | null; clinic_name: string | null;
  intake_channel: string; workflow_stage: string;
  document_status: string; preparation_status: string; arrival_status: string;
  check_in_status: string; encounter_status: string; consumables_status: string;
  billing_status: string; payment_status: string; blocker_status: string;
  blocker_labels: string[]; blockers: DashboardBlocker[]; allowed_actions: string[];
  activity_count: number; current_activity_id: number | null; next_activity_id: number | null; activities: DashboardActivity[];
};
type DashboardClinic = { id: number; name: string };
type DashboardResponse = {
  date: string; refreshed_at: string; visible_sections: string[]; viewer_role: string;
  scope: string; scope_label: string; scoped_clinician_id: number | null;
  can_filter_clinician: boolean; available_clinics: DashboardClinic[]; rows: DashboardRow[];
};
type SignalTone = "resolved" | "active" | "problem" | "unresolved";
type OperationalState = { tone: SignalTone; label: string; detail: string; action?: "reception" | "encounter" | "consumables" | "billing" | "open"; actionLabel?: string; icon?: ReactNode };

const today = new Date().toISOString().slice(0, 10);
const preparationAttention: Record<string, string> = {
  assigned: "Priprema čeka potvrdu pacijenta.", acknowledged: "Pripremu treba dovršiti prije pregleda.",
  in_progress: "Priprema još nije dovršena.", review_required: "Pripremu treba provjeriti ovlaštena osoba.",
  blocked: "Priprema je blokirana i treba odluku ovlaštene osobe.",
};
const documentContext: Record<string, string> = {
  requested: "Ako pacijent ima ranije nalaze, može ih donijeti na pregled; to ne blokira početak pregleda.",
  partial: "Dio nalaza je već zaprimljen; ostale nalaze pacijent može donijeti na pregled.",
  review_required: "Zaprimljeni nalazi čekaju liječnički pregled, ali nisu administrativni uvjet za dolazak.",
};

function StatusSignal({ tone, description }: { tone: SignalTone; description: string }) {
  const symbol = tone === "resolved" ? "✓" : tone === "problem" ? "!" : tone === "active" ? "–" : "";
  return <span className="status-signal-wrap"><span className={`status-signal ${tone}`} tabIndex={0} aria-label={description} title={description}><span aria-hidden="true">{symbol}</span><span className="status-signal-tooltip" role="tooltip">{description}</span></span></span>;
}

function activityTone(status: string): SignalTone {
  if (["completed", "not_performed", "cancelled"].includes(status)) return "resolved";
  if (status === "in_progress") return "active";
  return "unresolved";
}

function operationalState(row: DashboardRow): OperationalState {
  const blocker = row.blockers[0];
  if (blocker) return { tone: "problem", label: blocker.title, detail: blocker.details || (blocker.is_clinical ? "Potrebna je odluka ovlaštenog liječnika." : "Stavku treba riješiti prije nastavka."), action: "open", actionLabel: "Otvori" };
  if (["completed", "cancelled"].includes(row.workflow_stage)) return { tone: "resolved", label: row.workflow_stage === "completed" ? "Završeno" : "Otkazano", detail: row.workflow_stage === "completed" ? "Pregled i naplata su završeni." : "Dolazak je otkazan." };
  if (row.workflow_stage === "no_show") return { tone: "problem", label: "Nije došao/la", detail: "Pacijent nije došao na termin." };
  if (row.workflow_stage === "procedure_completed") return { tone: "active", label: "Čeka materijal", detail: "Potvrdite korišteni materijal ili da materijal nije korišten.", action: row.allowed_actions.includes("record_consumables") ? "consumables" : "open", actionLabel: row.allowed_actions.includes("record_consumables") ? "Evidentiraj materijal" : "Otvori", icon: <PackageCheck size={15}/> };
  if (["awaiting_billing", "awaiting_payment"].includes(row.workflow_stage)) { const mayBill = row.allowed_actions.includes("prepare_billing") || row.allowed_actions.includes("open_payment"); return { tone: "active", label: "Čeka naplatu", detail: row.workflow_stage === "awaiting_billing" ? "Materijal je riješen. Račun treba izraditi." : "Račun je izrađen i čeka plaćanje.", action: mayBill ? "billing" : "open", actionLabel: mayBill ? "Naplati" : "Otvori", icon: <CreditCard size={15}/> }; }
  if (["ready_for_clinician", "in_encounter"].includes(row.workflow_stage)) { const mayOpen = row.allowed_actions.includes("open_encounter"); return { tone: "active", label: row.workflow_stage === "in_encounter" ? "Pregled u tijeku" : "Čeka liječnika", detail: row.workflow_stage === "in_encounter" ? "Klinički susret je otvoren." : "Prijem je završen; pacijent je spreman za liječnika.", action: mayOpen ? "encounter" : "open", actionLabel: mayOpen ? (row.workflow_stage === "in_encounter" ? "Nastavi pregled" : "Otvori pregled") : "Otvori", icon: <Stethoscope size={15}/> }; }
  if (["arrived", "check_in_review"].includes(row.workflow_stage)) { const mayOpen = row.allowed_actions.includes("open_check_in"); return { tone: "active", label: "Prijem u tijeku", detail: "Dovršite samo potrebne prijemne provjere.", action: mayOpen ? "reception" : "open", actionLabel: mayOpen ? "Nastavi prijem" : "Otvori", icon: <ClipboardCheck size={15}/> }; }
  const preparationDetail = preparationAttention[row.preparation_status];
  const attention = preparationDetail;
  if (["requested", "booked", "awaiting_forms", "awaiting_documents", "preparation_in_progress", "ready_for_arrival"].includes(row.workflow_stage)) {
    const mayOpen = row.allowed_actions.includes("open_check_in");
    if (attention) return { tone: "active", label: "Potrebna priprema", detail: attention, action: "open", actionLabel: "Otvori" };
    return { tone: "unresolved", label: "Čeka dolazak", detail: documentContext[row.document_status] || "Pacijent još nije započeo prijem.", action: mayOpen ? "reception" : "open", actionLabel: mayOpen ? "Započni prijem" : "Otvori", icon: <ClipboardCheck size={15}/> };
  }
  if (attention) return { tone: "active", label: "Potrebna priprema", detail: attention, action: "open", actionLabel: "Otvori" };
  return { tone: "unresolved", label: "Nije započeto", detail: "Tijek još nema operativnu radnju.", action: "open", actionLabel: "Otvori" };
}

export function DailyClinicDashboard() {
  const navigate = useNavigate();
  const [day, setDay] = useState(today);
  const [clinician, setClinician] = useState(""); const [clinic, setClinic] = useState(""); const [room, setRoom] = useState(""); const [service, setService] = useState("");
  const [stage, setStage] = useState(""); const [blocker, setBlocker] = useState(""); const [query, setQuery] = useState("");
  const [view, setView] = useState<"patients" | "rooms">("patients");
  const [refresh, setRefresh] = useState(0);
  const params = new URLSearchParams({ selected_date: day, refresh: String(refresh) });
  if (clinician) params.set("clinician_id", clinician); if (clinic) params.set("clinic_id", clinic); if (room) params.set("room_id", room); if (service) params.set("service_id", service);
  if (stage) params.set("status", stage); if (blocker) params.set("blocker", blocker); if (query.trim()) params.set("q", query.trim());
  const board = useApi<DashboardResponse>(`/api/dashboard/day?${params}`, { date: day, refreshed_at: "", visible_sections: [], viewer_role: "", scope: "", scope_label: "", scoped_clinician_id: null, can_filter_clinician: false, available_clinics: [], rows: [] });
  const providers = useApi<Provider[]>("/api/providers", []); const rooms = useApi<Room[]>("/api/rooms", []); const services = useApi<Service[]>("/api/services", []);
  useEffect(() => {
    if (clinic && !board.data.available_clinics.some(item => String(item.id) === clinic)) setClinic("");
  }, [board.data.available_clinics, clinic]);
  const counts = useMemo(() => ({ total: board.data.rows.length, active: board.data.rows.filter(row => operationalState(row).tone === "active").length, problems: board.data.rows.filter(row => operationalState(row).tone === "problem").length }), [board.data.rows]);
  const advancedFilterCount = [clinic, room, service, stage].filter(Boolean).length;
  const roomSchedule = useMemo(() => {
    const grouped = new Map<string, Array<{ row: DashboardRow; activity: DashboardActivity }>>();
    for (const row of board.data.rows) for (const activity of row.activities ?? []) {
      const key = activity.room_name ?? "Prostorija nije određena";
      grouped.set(key, [...(grouped.get(key) ?? []), { row, activity }]);
    }
    return [...grouped.entries()].map(([roomName, entries]) => ({ roomName, entries: entries.sort((a, b) => a.activity.time.localeCompare(b.activity.time)) }));
  }, [board.data.rows]);

  function focusFor(state: OperationalState) {
    if (state.action === "reception") return "arrival";
    if (state.action === "encounter") return "encounter";
    if (state.action === "consumables") return "consumables";
    if (state.action === "billing") return "billing";
    return "attention";
  }
  function runAction(row: DashboardRow, state: OperationalState) {
    navigate(`/journeys/${row.journey_id}?focus=${focusFor(state)}`);
  }
  function clearFilters() {
    setClinician(""); setClinic(""); setRoom(""); setService(""); setStage(""); setBlocker(""); setQuery("");
  }

  return <section className="page clinic-day-page">
    <header className="clinic-day-header"><div><span className="eyebrow">Dnevni operativni pregled</span><h1>Danas u poliklinici</h1><p>Tko je sljedeći, postoji li problem i što sada treba napraviti.</p><span className="clinic-day-scope">Prikaz: {board.data.scope_label || "učitavanje…"}</span></div><div className="clinic-day-date"><DateInput value={day} onChange={setDay} required/><button type="button" onClick={() => setRefresh(value => value + 1)}><RefreshCw size={16}/>Osvježi</button></div></header>
    <div className="clinic-day-summary"><span><b>{counts.total}</b> dolazaka</span><span><b>{counts.active}</b> u tijeku</span><span className={counts.problems ? "attention" : ""}><b>{counts.problems}</b> s problemom</span><small>Zadnje osvježenje: {board.data.refreshed_at ? new Date(board.data.refreshed_at).toLocaleTimeString("hr-HR", { hour: "2-digit", minute: "2-digit" }) : "—"}</small></div>
    <div className="clinic-day-view-toggle" role="group" aria-label="Način prikaza"><button type="button" className={view === "patients" ? "active" : ""} onClick={() => setView("patients")}>Po pacijentima</button><button type="button" className={view === "rooms" ? "active" : ""} onClick={() => setView("rooms")}>Po prostorijama</button></div>
    <div className="clinic-day-filter-bar"><label className="clinic-day-search"><Search size={16}/><input aria-label="Pretraži pacijenta" placeholder="Pretraži pacijenta" value={query} onChange={event => setQuery(event.target.value)}/></label>{board.data.can_filter_clinician && <select aria-label="Liječnik" value={clinician} onChange={event => { setClinician(event.target.value); setClinic(""); setRoom(""); }}><option value="">Svi liječnici</option>{providers.data.filter(item => item.staff_role === "physician").map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select>}<select aria-label="Problem" value={blocker} onChange={event => setBlocker(event.target.value)}><option value="">Sva stanja</option><option value="true">S problemom</option><option value="false">Bez problema</option></select><details className="clinic-day-advanced"><summary><Filter size={15}/>Dodatni filtri{advancedFilterCount > 0 && <b aria-label={`${advancedFilterCount} aktivna dodatna filtra`}>{advancedFilterCount}</b>}</summary><div className="clinic-day-filters">{board.data.available_clinics.length > 1 && <select aria-label="Klinika" value={clinic} onChange={event => { setClinic(event.target.value); setRoom(""); }}><option value="">Sve klinike</option>{board.data.available_clinics.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>}<select aria-label="Prostorija" value={room} onChange={event => setRoom(event.target.value)}><option value="">Sve prostorije</option>{rooms.data.filter(item => !clinic || String(item.clinic_id ?? "") === clinic).map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select aria-label="Usluga" value={service} onChange={event => setService(event.target.value)}><option value="">Sve usluge</option>{services.data.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select aria-label="Faza" value={stage} onChange={event => setStage(event.target.value)}><option value="">Sve faze</option><option value="ready_for_arrival">Čeka dolazak</option><option value="check_in_review">Prijem u tijeku</option><option value="ready_for_clinician">Čeka liječnika</option><option value="in_encounter">Pregled u tijeku</option><option value="awaiting_payment">Čeka naplatu</option></select></div></details>{[clinician, clinic, room, service, stage, blocker, query].some(Boolean) && <button type="button" className="clear-filters" onClick={clearFilters}><X size={15}/>Očisti filtre</button>}</div>
    {board.error && <p className="form-error">Dnevni pregled nije učitan: {board.error}</p>}
    {view === "patients" ? <div className="clinic-day-table-wrap"><table className="clinic-day-table clinic-day-table-simple"><thead><tr><th>Vrijeme i pacijent</th><th>Usluga i liječnik</th><th>Trenutačno stanje</th><th>Sljedeća radnja</th></tr></thead><tbody>
      {board.data.rows.map(row => { const state = operationalState(row); const focus = focusFor(state); const activities = row.activities ?? []; return <tr key={row.journey_id} className={`${state.tone}-row ${state.tone === "problem" ? "has-blocker" : ""}`}><td><span className="patient-time">{row.time.slice(0,5)}</span><Link to={`/journeys/${row.journey_id}?focus=${focus}`}>{row.patient_name}</Link><small>{board.data.available_clinics.length > 1 && row.clinic_name ? `${row.clinic_name} · ` : ""}{row.room_name}</small></td><td>{(row.activity_count ?? 1) > 1 ? <strong>{row.activity_count} aktivnosti</strong> : <strong>{row.service_name}</strong>}{activities.length > 0 && <div className="activity-rail" aria-label="Aktivnosti dolaska">{activities.map(activity => <Link key={activity.id} className={activity.id === row.current_activity_id ? "current" : ""} to={`/journeys/${row.journey_id}?focus=encounter&activity=${activity.id}`}><StatusSignal tone={activityTone(activity.status)} description={`${activity.service_name}. ${activity.status === "in_progress" ? "U tijeku" : activity.status === "completed" ? "Završeno" : "Nije započeto"}. ${activity.room_name ?? "Prostorija nije određena"}.`}/><span><b>{activity.time.slice(0,5)} {activity.service_name}</b><small>{activity.room_name ?? "Bez prostorije"}{activity.clinician_name ? ` · ${activity.clinician_name}` : ""}</small></span></Link>)}</div>}</td><td><div className="operational-state"><StatusSignal tone={state.tone} description={`${state.label}. ${state.detail}`}/><span><strong>{state.label}</strong><small>{state.detail}</small>{row.blockers.length > 1 && <small className="additional-problems">+{row.blockers.length - 1} dodatna problema</small>}</span></div></td><td className="clinic-day-actions">{state.action && <button type="button" onClick={() => runAction(row, state)}>{state.icon}{state.actionLabel}</button>}</td></tr>; })}
      {!board.loading && !board.data.rows.length && <tr><td colSpan={4} className="clinic-day-empty">Za odabrani dan i filtre nema dolazaka.</td></tr>}
    </tbody></table></div> : <div className="clinic-room-board">{roomSchedule.map(group => <section className="journey-panel" key={group.roomName}><header><h2>{group.roomName}</h2></header>{group.entries.map(({ row, activity }, index) => <Link className="clinic-room-slot" to={`/journeys/${row.journey_id}?focus=encounter&activity=${activity.id}`} key={activity.id}><StatusSignal tone={activityTone(activity.status)} description={`${activity.service_name}. ${activity.status === "in_progress" ? "U tijeku" : activity.status === "completed" ? "Završeno" : "Čeka"}.`}/><span><b>{activity.time.slice(0,5)} · {row.patient_name}</b><small>{activity.service_name}{activity.clinician_name ? ` · ${activity.clinician_name}` : ""}</small><small>{index === 0 ? "Prva planirana aktivnost" : "Sljedeća aktivnost u prostoriji"}</small></span></Link>)}</section>)}{!roomSchedule.length && <p className="clinic-day-empty">Za odabrani dan nema raspoređenih prostorija.</p>}</div>}
    <p className="clinic-day-legend"><StatusSignal tone="unresolved" description="Nije započeto"/> nije započeto <StatusSignal tone="active" description="U tijeku"/> u tijeku <StatusSignal tone="problem" description="Postoji problem"/> problem <StatusSignal tone="resolved" description="Završeno"/> završeno</p>
  </section>;
}
