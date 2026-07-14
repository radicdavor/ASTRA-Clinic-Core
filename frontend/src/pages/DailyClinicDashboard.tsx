import { ClipboardCheck, CreditCard, PackageCheck, RefreshCw, Search, Stethoscope } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";
import { DateInput } from "../components/DateInput";
import { useApi } from "../hooks/useApi";
import type { Provider, Room, Service } from "../types";

type DashboardBlocker = { id: number; title: string; details: string | null; is_clinical: boolean };
type DashboardRow = {
  journey_id: number; appointment_id: number; time: string; patient_name: string;
  service_id: number; service_name: string; clinician_id: number; clinician_name: string;
  room_id: number; room_name: string; intake_channel: string; workflow_stage: string;
  document_status: string; preparation_status: string; arrival_status: string;
  check_in_status: string; encounter_status: string; consumables_status: string;
  billing_status: string; payment_status: string; blocker_status: string;
  blocker_labels: string[]; blockers: DashboardBlocker[]; allowed_actions: string[];
};
type DashboardResponse = { date: string; refreshed_at: string; visible_sections: string[]; rows: DashboardRow[] };
type SignalTone = "resolved" | "active" | "problem" | "unresolved";
type OperationalState = { tone: SignalTone; label: string; detail: string; action?: "reception" | "encounter" | "consumables" | "billing" | "open"; actionLabel?: string; icon?: ReactNode };

const today = new Date().toISOString().slice(0, 10);
const preparationAttention: Record<string, string> = {
  assigned: "Priprema čeka potvrdu pacijenta.", acknowledged: "Pripremu treba dovršiti prije pregleda.",
  in_progress: "Priprema još nije dovršena.", review_required: "Pripremu treba provjeriti ovlaštena osoba.",
  blocked: "Priprema je blokirana i treba odluku ovlaštene osobe.",
};
const documentAttention: Record<string, string> = {
  requested: "Dokumentacija je zatražena, ali još nije zaprimljena.", partial: "Nedostaje dio tražene dokumentacije.",
  review_required: "Dokumentaciju treba pregledati ovlaštena osoba.", blocked: "Dokumentacija blokira nastavak obrade.",
};

function StatusSignal({ tone, description }: { tone: SignalTone; description: string }) {
  const symbol = tone === "resolved" ? "✓" : tone === "problem" ? "!" : tone === "active" ? "–" : "";
  return <span className="status-signal-wrap"><span className={`status-signal ${tone}`} tabIndex={0} aria-label={description} title={description}><span aria-hidden="true">{symbol}</span><span className="status-signal-tooltip" role="tooltip">{description}</span></span></span>;
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
  const attention = documentAttention[row.document_status] || preparationAttention[row.preparation_status];
  if (row.workflow_stage === "ready_for_arrival") { const mayOpen = row.allowed_actions.includes("open_check_in"); return { tone: attention ? "active" : "unresolved", label: attention ? "Čeka dolazak · potrebna provjera" : "Čeka dolazak", detail: attention || "Pacijent još nije započeo prijem.", action: mayOpen ? "reception" : "open", actionLabel: mayOpen ? "Započni prijem" : "Otvori", icon: <ClipboardCheck size={15}/> }; }
  if (attention) return { tone: "active", label: "Potrebna priprema", detail: attention, action: "open", actionLabel: "Otvori" };
  return { tone: "unresolved", label: "Nije započeto", detail: "Tijek još nema operativnu radnju.", action: "open", actionLabel: "Otvori" };
}

export function DailyClinicDashboard() {
  const navigate = useNavigate();
  const [day, setDay] = useState(today);
  const [clinician, setClinician] = useState(""); const [room, setRoom] = useState(""); const [service, setService] = useState("");
  const [stage, setStage] = useState(""); const [blocker, setBlocker] = useState(""); const [query, setQuery] = useState("");
  const [refresh, setRefresh] = useState(0); const [busyJourney, setBusyJourney] = useState<number | null>(null); const [actionError, setActionError] = useState("");
  const params = new URLSearchParams({ selected_date: day, refresh: String(refresh) });
  if (clinician) params.set("clinician_id", clinician); if (room) params.set("room_id", room); if (service) params.set("service_id", service);
  if (stage) params.set("status", stage); if (blocker) params.set("blocker", blocker); if (query.trim()) params.set("q", query.trim());
  const board = useApi<DashboardResponse>(`/api/dashboard/day?${params}`, { date: day, refreshed_at: "", visible_sections: [], rows: [] });
  const providers = useApi<Provider[]>("/api/providers", []); const rooms = useApi<Room[]>("/api/rooms", []); const services = useApi<Service[]>("/api/services", []);
  const counts = useMemo(() => ({ total: board.data.rows.length, active: board.data.rows.filter(row => operationalState(row).tone === "active").length, problems: board.data.rows.filter(row => operationalState(row).tone === "problem").length }), [board.data.rows]);

  async function openReception(row: DashboardRow) {
    setBusyJourney(row.journey_id); setActionError("");
    try {
      if (["ready_for_arrival", "arrived"].includes(row.workflow_stage)) await api(`/api/patient-journeys/${row.journey_id}/check-in`, { method: "POST" });
      navigate(`/journeys/${row.journey_id}?focus=check-in`);
    } catch (error) { setActionError(error instanceof Error ? error.message : "Prijem nije otvoren."); setBusyJourney(null); }
  }
  async function openBilling(row: DashboardRow) {
    setBusyJourney(row.journey_id); setActionError("");
    try {
      if (row.workflow_stage === "awaiting_billing") {
        if (!window.confirm("Izraditi i izdati račun za ovaj dolazak?")) { setBusyJourney(null); return; }
        await api(`/api/patient-journeys/${row.journey_id}/billing/prepare`, { method: "POST" });
      }
      navigate(`/journeys/${row.journey_id}?focus=payment`);
    } catch (error) { setActionError(error instanceof Error ? error.message : "Naplata nije otvorena."); setBusyJourney(null); }
  }
  function runAction(row: DashboardRow, state: OperationalState) {
    if (state.action === "reception") return openReception(row);
    if (state.action === "billing") return openBilling(row);
    const focus = state.action === "encounter" ? "encounter" : state.action === "consumables" ? "consumables" : "attention";
    navigate(`/journeys/${row.journey_id}?focus=${focus}`);
  }

  return <section className="page clinic-day-page">
    <header className="clinic-day-header"><div><span className="eyebrow">Dnevni operativni pregled</span><h1>Danas u poliklinici</h1><p>Tko je sljedeći, postoji li problem i što sada treba napraviti.</p></div><div className="clinic-day-date"><DateInput value={day} onChange={setDay} required/><button type="button" onClick={() => setRefresh(value => value + 1)}><RefreshCw size={16}/>Osvježi</button></div></header>
    <div className="clinic-day-summary"><span><b>{counts.total}</b> dolazaka</span><span><b>{counts.active}</b> u tijeku</span><span className={counts.problems ? "attention" : ""}><b>{counts.problems}</b> s problemom</span><small>Zadnje osvježenje: {board.data.refreshed_at ? new Date(board.data.refreshed_at).toLocaleTimeString("hr-HR", { hour: "2-digit", minute: "2-digit" }) : "—"}</small></div>
    <div className="clinic-day-filters"><label className="clinic-day-search"><Search size={16}/><input aria-label="Pretraži pacijenta" placeholder="Pretraži pacijenta" value={query} onChange={event => setQuery(event.target.value)}/></label><select aria-label="Liječnik" value={clinician} onChange={event => setClinician(event.target.value)}><option value="">Svi liječnici</option>{providers.data.filter(item => item.staff_role === "physician").map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select><select aria-label="Prostorija" value={room} onChange={event => setRoom(event.target.value)}><option value="">Sve prostorije</option>{rooms.data.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select aria-label="Usluga" value={service} onChange={event => setService(event.target.value)}><option value="">Sve usluge</option>{services.data.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select aria-label="Faza" value={stage} onChange={event => setStage(event.target.value)}><option value="">Sve faze</option><option value="ready_for_arrival">Čeka dolazak</option><option value="check_in_review">Prijem u tijeku</option><option value="ready_for_clinician">Čeka liječnika</option><option value="in_encounter">Pregled u tijeku</option><option value="awaiting_payment">Čeka naplatu</option></select><select aria-label="Problem" value={blocker} onChange={event => setBlocker(event.target.value)}><option value="">Sva stanja</option><option value="true">S problemom</option><option value="false">Bez problema</option></select></div>
    {board.error && <p className="form-error">Dnevni pregled nije učitan: {board.error}</p>}{actionError && <p className="form-error" role="alert">Radnja nije izvršena: {actionError}</p>}
    <div className="clinic-day-table-wrap"><table className="clinic-day-table clinic-day-table-simple"><thead><tr><th>Vrijeme i pacijent</th><th>Usluga i liječnik</th><th>Trenutačno stanje</th><th>Sljedeća radnja</th></tr></thead><tbody>
      {board.data.rows.map(row => { const state = operationalState(row); return <tr key={row.journey_id} className={`${state.tone}-row ${state.tone === "problem" ? "has-blocker" : ""}`}><td><span className="patient-time">{row.time.slice(0,5)}</span><Link to={`/journeys/${row.journey_id}`}>{row.patient_name}</Link><small>{row.room_name}</small></td><td><strong>{row.service_name}</strong><small>{row.clinician_name}</small></td><td><div className="operational-state"><StatusSignal tone={state.tone} description={`${state.label}. ${state.detail}`}/><span><strong>{state.label}</strong><small>{state.detail}</small></span></div></td><td className="clinic-day-actions">{state.action && <button type="button" disabled={busyJourney === row.journey_id} onClick={() => runAction(row, state)}>{state.icon}{state.actionLabel}</button>}</td></tr>; })}
      {!board.loading && !board.data.rows.length && <tr><td colSpan={4} className="clinic-day-empty">Za odabrani dan i filtre nema dolazaka.</td></tr>}
    </tbody></table></div>
    <p className="clinic-day-legend"><StatusSignal tone="unresolved" description="Nije započeto"/> nije započeto <StatusSignal tone="active" description="U tijeku"/> u tijeku <StatusSignal tone="problem" description="Postoji problem"/> problem <StatusSignal tone="resolved" description="Završeno"/> završeno</p>
  </section>;
}
