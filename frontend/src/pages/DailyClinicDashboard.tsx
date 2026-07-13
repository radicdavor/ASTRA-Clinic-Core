import { AlertTriangle, CheckCircle2, Circle, Clock3, RefreshCw, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { useMemo, useState } from "react";
import { DateInput } from "../components/DateInput";
import { useApi } from "../hooks/useApi";
import type { Provider, Room, Service } from "../types";

type DashboardRow = {
  journey_id: number; appointment_id: number; time: string; patient_name: string;
  service_id: number; service_name: string; clinician_id: number; clinician_name: string;
  room_id: number; room_name: string; intake_channel: string; workflow_stage: string;
  document_status: string; preparation_status: string; arrival_status: string;
  check_in_status: string; encounter_status: string; consumables_status: string;
  billing_status: string; payment_status: string; blocker_status: string; blocker_labels: string[];
};
type DashboardResponse = { date: string; refreshed_at: string; visible_sections: string[]; rows: DashboardRow[] };

const today = new Date().toISOString().slice(0, 10);
const labels: Record<string, string> = {
  not_requested: "Nije zatraženo", requested: "Zatraženo", partial: "Nedostaje dio", complete: "Dovršeno",
  review_required: "Treba pregled", blocked: "Blokirano", not_assigned: "Nije dodijeljeno", assigned: "Dodijeljeno",
  acknowledged: "Potvrđeno", in_progress: "U tijeku", not_arrived: "Nije stigao/la", arrived: "Stigao/la",
  in_review: "U provjeri", ready: "Spremno", not_started: "Nije započeto", completed: "Dovršeno",
  aborted: "Prekinuto", not_ready: "Nije spremno", pending: "Čeka potvrdu", confirmed: "Potvrđeno",
  not_applicable: "Nije primjenjivo", invoice_created: "Račun izrađen", adjustment_required: "Treba ispravak",
  closed: "Zatvoreno", not_due: "Nije dospjelo", unpaid: "Neplaćeno", partially_paid: "Djelomično plaćeno",
  paid: "Plaćeno", refunded: "Vraćeno", cancelled: "Otkazano", deferred: "Odgođeno", clear: "Bez blokatora"
};
const good = new Set(["complete", "completed", "confirmed", "ready", "paid", "closed", "not_applicable", "clear"]);
const warning = new Set(["partial", "review_required", "blocked", "adjustment_required", "unpaid", "partially_paid"]);

function JourneyState({ value }: { value: string }) {
  const Icon = good.has(value) ? CheckCircle2 : warning.has(value) ? AlertTriangle : value.includes("progress") || value === "in_review" ? Clock3 : Circle;
  const tone = good.has(value) ? "ok" : warning.has(value) ? "warning" : "neutral";
  return <span className={`journey-state ${tone}`}><Icon size={14} />{labels[value] ?? value}</span>;
}

export function DailyClinicDashboard() {
  const [day, setDay] = useState(today);
  const [clinician, setClinician] = useState("");
  const [room, setRoom] = useState("");
  const [service, setService] = useState("");
  const [stage, setStage] = useState("");
  const [blocker, setBlocker] = useState("");
  const [query, setQuery] = useState("");
  const [refresh, setRefresh] = useState(0);
  const params = new URLSearchParams({ selected_date: day, refresh: String(refresh) });
  if (clinician) params.set("clinician_id", clinician);
  if (room) params.set("room_id", room);
  if (service) params.set("service_id", service);
  if (stage) params.set("status", stage);
  if (blocker) params.set("blocker", blocker);
  if (query.trim()) params.set("q", query.trim());
  const board = useApi<DashboardResponse>(`/api/dashboard/day?${params}`, { date: day, refreshed_at: "", visible_sections: [], rows: [] });
  const providers = useApi<Provider[]>("/api/providers", []);
  const rooms = useApi<Room[]>("/api/rooms", []);
  const services = useApi<Service[]>("/api/services", []);
  const counts = useMemo(() => ({ total: board.data.rows.length, blocked: board.data.rows.filter(row => row.blocker_status === "blocked").length, arrived: board.data.rows.filter(row => row.arrival_status === "arrived").length }), [board.data.rows]);

  return <section className="page clinic-day-page">
    <header className="clinic-day-header">
      <div><span className="eyebrow">Dnevni operativni pregled</span><h1>Danas u poliklinici</h1><p>Jedan red prikazuje cijeli put pacijenta — od dokumenata do plaćanja.</p></div>
      <div className="clinic-day-date"><DateInput value={day} onChange={setDay} required /><button type="button" onClick={() => setRefresh(value => value + 1)}><RefreshCw size={16}/>Osvježi</button></div>
    </header>
    <div className="clinic-day-summary"><span><b>{counts.total}</b> putovanja</span><span><b>{counts.arrived}</b> stiglo</span><span className={counts.blocked ? "attention" : ""}><b>{counts.blocked}</b> blokirano</span><small>Zadnje osvježenje: {board.data.refreshed_at ? new Date(board.data.refreshed_at).toLocaleTimeString("hr-HR", { hour: "2-digit", minute: "2-digit" }) : "—"}</small></div>
    <div className="clinic-day-filters">
      <label className="clinic-day-search"><Search size={16}/><input aria-label="Pretraži pacijenta" placeholder="Pretraži pacijenta" value={query} onChange={event => setQuery(event.target.value)}/></label>
      <select aria-label="Liječnik" value={clinician} onChange={event => setClinician(event.target.value)}><option value="">Svi liječnici</option>{providers.data.filter(item => item.staff_role === "physician").map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select>
      <select aria-label="Prostorija" value={room} onChange={event => setRoom(event.target.value)}><option value="">Sve prostorije</option>{rooms.data.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
      <select aria-label="Usluga" value={service} onChange={event => setService(event.target.value)}><option value="">Sve usluge</option>{services.data.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
      <select aria-label="Faza" value={stage} onChange={event => setStage(event.target.value)}><option value="">Sve faze</option><option value="ready_for_arrival">Čeka dolazak</option><option value="check_in_review">U provjeri</option><option value="ready_for_clinician">Čeka liječnika</option><option value="in_encounter">Pregled u tijeku</option><option value="awaiting_payment">Čeka plaćanje</option></select>
      <select aria-label="Blokator" value={blocker} onChange={event => setBlocker(event.target.value)}><option value="">Svi blokatori</option><option value="true">S blokatorom</option><option value="false">Bez blokatora</option></select>
    </div>
    {board.error && <p className="form-error">Dnevni pregled nije učitan: {board.error}</p>}
    <div className="clinic-day-table-wrap"><table className="clinic-day-table"><thead><tr><th>Vrijeme i pacijent</th><th>Usluga</th><th>Dokumenti</th><th>Priprema</th><th>Dolazak</th><th>Check-in</th><th>Pregled</th><th>Materijal</th><th>Račun</th><th>Plaćanje</th><th>Blokator</th></tr></thead><tbody>
      {board.data.rows.map(row => <tr key={row.journey_id} className={row.blocker_status === "blocked" ? "has-blocker" : ""}>
        <td><span className="patient-time">{row.time.slice(0,5)}</span><Link to={`/journeys/${row.journey_id}`}>{row.patient_name}</Link><small>{row.clinician_name} · {row.room_name}</small></td>
        <td><strong>{row.service_name}</strong><small>{row.intake_channel === "ai_secretary" ? "AI tajnica" : row.intake_channel === "web" ? "Web" : "Ručni unos"}</small></td>
        <td><JourneyState value={row.document_status}/></td><td><JourneyState value={row.preparation_status}/></td><td><JourneyState value={row.arrival_status}/></td><td><JourneyState value={row.check_in_status}/></td><td><JourneyState value={row.encounter_status}/></td><td><JourneyState value={row.consumables_status}/></td><td><JourneyState value={row.billing_status}/></td><td><JourneyState value={row.payment_status}/></td>
        <td>{row.blocker_status === "blocked" ? <span className="blocker-copy"><AlertTriangle size={15}/>{row.blocker_labels.join(", ")}</span> : <JourneyState value="clear"/>}</td>
      </tr>)}
      {!board.loading && !board.data.rows.length && <tr><td colSpan={11} className="clinic-day-empty">Za odabrani dan i filtre nema putovanja pacijenata.</td></tr>}
    </tbody></table></div>
  </section>;
}
