import { AlertTriangle, CheckCircle2, Circle, ClipboardCheck, Clock3, RefreshCw, Search, Stethoscope } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useMemo, useState } from "react";
import { api } from "../api/client";
import { DateInput } from "../components/DateInput";
import { journeyStatusLabel } from "../components/program2/journeyStatus";
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

const today = new Date().toISOString().slice(0, 10);
const good = new Set(["complete", "completed", "confirmed", "ready", "paid", "closed", "not_applicable", "clear"]);
const warning = new Set(["partial", "review_required", "blocked", "adjustment_required", "unpaid", "partially_paid"]);

function JourneyState({ value }: { value: string }) {
  const Icon = good.has(value) ? CheckCircle2 : warning.has(value) ? AlertTriangle : value.includes("progress") || value === "in_review" ? Clock3 : Circle;
  const tone = good.has(value) ? "ok" : warning.has(value) ? "warning" : "neutral";
  return <span className={`journey-state ${tone}`}><Icon size={14} />{journeyStatusLabel(value)}</span>;
}

const preparationAttention: Record<string, string> = {
  assigned: "Priprema čeka potvrdu pacijenta.",
  acknowledged: "Pripremu treba dovršiti prije pregleda.",
  in_progress: "Priprema još nije dovršena.",
  review_required: "Pripremu treba provjeriti ovlaštena osoba.",
  blocked: "Priprema je blokirana i treba odluku ovlaštene osobe.",
};

const documentAttention: Record<string, string> = {
  requested: "Dokumentacija je zatražena, ali još nije zaprimljena.",
  partial: "Nedostaje dio tražene dokumentacije.",
  review_required: "Dokumentaciju treba pregledati ovlaštena osoba.",
  blocked: "Dokumentacija blokira nastavak obrade.",
};

export function DailyClinicDashboard() {
  const navigate = useNavigate();
  const [day, setDay] = useState(today);
  const [clinician, setClinician] = useState("");
  const [room, setRoom] = useState("");
  const [service, setService] = useState("");
  const [stage, setStage] = useState("");
  const [blocker, setBlocker] = useState("");
  const [query, setQuery] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [busyJourney, setBusyJourney] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");
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
  const counts = useMemo(() => ({ total: board.data.rows.length, blocked: board.data.rows.filter(row => row.blocker_status === "blocked").length }), [board.data.rows]);

  async function openReception(row: DashboardRow) {
    setBusyJourney(row.journey_id); setActionError("");
    try {
      if (["ready_for_arrival", "arrived"].includes(row.workflow_stage)) await api(`/api/patient-journeys/${row.journey_id}/check-in`, { method: "POST" });
      navigate(`/journeys/${row.journey_id}?focus=check-in`);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Prijem nije otvoren.");
      setBusyJourney(null);
    }
  }

  return <section className="page clinic-day-page">
    <header className="clinic-day-header">
      <div><span className="eyebrow">Dnevni operativni pregled</span><h1>Danas u poliklinici</h1><p>Jedan red prikazuje cijeli tijek pacijenta — od dokumentacije i pripreme do pregleda i plaćanja.</p></div>
      <div className="clinic-day-date"><DateInput value={day} onChange={setDay} required /><button type="button" onClick={() => setRefresh(value => value + 1)}><RefreshCw size={16}/>Osvježi</button></div>
    </header>
    <div className="clinic-day-summary"><span><b>{counts.total}</b> dolazaka</span><span className={counts.blocked ? "attention" : ""}><b>{counts.blocked}</b> s blokadom</span><small>Zadnje osvježenje: {board.data.refreshed_at ? new Date(board.data.refreshed_at).toLocaleTimeString("hr-HR", { hour: "2-digit", minute: "2-digit" }) : "—"}</small></div>
    <div className="clinic-day-filters">
      <label className="clinic-day-search"><Search size={16}/><input aria-label="Pretraži pacijenta" placeholder="Pretraži pacijenta" value={query} onChange={event => setQuery(event.target.value)}/></label>
      <select aria-label="Liječnik" value={clinician} onChange={event => setClinician(event.target.value)}><option value="">Svi liječnici</option>{providers.data.filter(item => item.staff_role === "physician").map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select>
      <select aria-label="Prostorija" value={room} onChange={event => setRoom(event.target.value)}><option value="">Sve prostorije</option>{rooms.data.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
      <select aria-label="Usluga" value={service} onChange={event => setService(event.target.value)}><option value="">Sve usluge</option>{services.data.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
      <select aria-label="Faza" value={stage} onChange={event => setStage(event.target.value)}><option value="">Sve faze</option><option value="ready_for_arrival">Čeka dolazak</option><option value="check_in_review">U provjeri</option><option value="ready_for_clinician">Čeka liječnika</option><option value="in_encounter">Pregled u tijeku</option><option value="awaiting_payment">Čeka plaćanje</option></select>
      <select aria-label="Blokator" value={blocker} onChange={event => setBlocker(event.target.value)}><option value="">Svi blokatori</option><option value="true">S blokatorom</option><option value="false">Bez blokatora</option></select>
    </div>
    {board.error && <p className="form-error">Dnevni pregled nije učitan: {board.error}</p>}
    {actionError && <p className="form-error" role="alert">Radnja nije izvršena: {actionError}</p>}
    <div className="clinic-day-table-wrap"><table className="clinic-day-table"><thead><tr><th>Vrijeme i pacijent</th><th>Usluga</th><th>Prijemna provjera</th><th>Pregled</th><th>Materijal</th><th>Račun</th><th>Plaćanje</th><th>Potrebno riješiti</th><th>Sljedeća radnja</th></tr></thead><tbody>
      {board.data.rows.map(row => <tr key={row.journey_id} className={row.blocker_status === "blocked" ? "has-blocker" : ""}>
        <td><span className="patient-time">{row.time.slice(0,5)}</span><Link to={`/journeys/${row.journey_id}`}>{row.patient_name}</Link><small>{row.clinician_name} · {row.room_name}</small></td>
        <td><strong>{row.service_name}</strong><small>{row.intake_channel === "ai_secretary" ? "AI tajnica" : row.intake_channel === "web" ? "Web" : "Ručni unos"}</small></td>
        <td><JourneyState value={row.check_in_status}/></td><td><JourneyState value={row.encounter_status}/></td><td><JourneyState value={row.consumables_status}/></td><td><JourneyState value={row.billing_status}/></td><td><JourneyState value={row.payment_status}/></td>
        <td>{row.blockers.length || preparationAttention[row.preparation_status] || documentAttention[row.document_status] ? <div className="blocker-list">
          {row.blockers.map(item => <span className="blocker-copy" key={item.id}><AlertTriangle size={15}/><span><strong>{item.title}</strong><small>{item.details || (item.is_clinical ? "Potrebna je odluka ovlaštenog liječnika." : "Potrebna je provjera prije nastavka.")}</small></span></span>)}
          {documentAttention[row.document_status] && <span className="blocker-copy document-attention"><AlertTriangle size={15}/><span><strong>Dokumentacija</strong><small>{documentAttention[row.document_status]}</small></span></span>}
          {preparationAttention[row.preparation_status] && <span className="blocker-copy preparation-attention"><Clock3 size={15}/><span><strong>Priprema</strong><small>{preparationAttention[row.preparation_status]}</small></span></span>}
        </div> : <span className="nothing-to-resolve"><CheckCircle2 size={14}/>Nema otvorenih stavki</span>}</td>
        <td className="clinic-day-actions">
          {row.allowed_actions.includes("open_check_in") && <button type="button" disabled={busyJourney === row.journey_id} onClick={() => openReception(row)}><ClipboardCheck size={15}/>Otvori prijem</button>}
          {row.allowed_actions.includes("open_encounter") && <button type="button" onClick={() => navigate(`/journeys/${row.journey_id}?focus=encounter`)}><Stethoscope size={15}/>Otvori pregled</button>}
        </td>
      </tr>)}
      {!board.loading && !board.data.rows.length && <tr><td colSpan={9} className="clinic-day-empty">Za odabrani dan i filtre nema dolazaka.</td></tr>}
    </tbody></table></div>
  </section>;
}
