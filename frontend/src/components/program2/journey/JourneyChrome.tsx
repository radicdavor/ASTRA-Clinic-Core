import { AlertTriangle, ArrowRight, Check, Circle } from "lucide-react";
import type { JourneyStageKey, PatientJourneyDetail } from "../../../types/program2";
import { journeyStageLabel } from "../journeyStatus";

export const journeyStages: Array<{ key: JourneyStageKey; label: string }> = [
  { key: "documents", label: "Dokumenti i priprema" },
  { key: "arrival", label: "Dolazak i prijem" },
  { key: "encounter", label: "Pregled" },
  { key: "consumables", label: "Materijal" },
  { key: "billing", label: "Naplata" },
  { key: "completed", label: "Završeno" },
];

export function stageForJourney(stage: string): JourneyStageKey {
  if (["requested", "booked", "awaiting_forms", "awaiting_documents", "preparation_in_progress"].includes(stage)) return "documents";
  if (["ready_for_arrival", "arrived", "check_in_review"].includes(stage)) return "arrival";
  if (["ready_for_clinician", "in_encounter"].includes(stage)) return "encounter";
  if (stage === "procedure_completed") return "consumables";
  if (["awaiting_billing", "awaiting_payment"].includes(stage)) return "billing";
  return "completed";
}

export function focusToStage(focus: string | null, fallback: JourneyStageKey): JourneyStageKey {
  const aliases: Record<string, JourneyStageKey> = { attention: fallback, "check-in": "arrival", arrival: "arrival", encounter: "encounter", consumables: "consumables", payment: "billing", billing: "billing", documents: "documents", completed: "completed" };
  return focus ? aliases[focus] ?? fallback : fallback;
}

export function JourneyHeader({ journey, service, clinician, formatDate }: { journey: PatientJourneyDetail; service?: string; clinician?: string; formatDate: (value?: string | null) => string }) {
  const openBlockers = journey.blockers.filter(item => item.status === "open");
  return <header className="journey-focus-header">
    <div><span className="eyebrow">Tijek pacijenta</span><h1>{journey.patient.first_name} {journey.patient.last_name}</h1><p>{formatDate(journey.patient.date_of_birth)} · {journey.appointment.start_time.slice(0, 5)} · {service ?? "Usluga"} · {clinician ?? "Liječnik nije naveden"}</p></div>
    <div className="journey-focus-state"><span>{journeyStageLabel(journey.current_stage)}</span>{openBlockers.length > 0 && <strong><AlertTriangle size={15}/>{openBlockers.length} {openBlockers.length === 1 ? "problem" : "problema"}</strong>}</div>
  </header>;
}

export function JourneyNextAction({ journey, stage, onSelect }: { journey: PatientJourneyDetail; stage: JourneyStageKey; onSelect: (stage: JourneyStageKey) => void }) {
  const blocker = journey.blockers.find(item => item.status === "open");
  const content: Record<JourneyStageKey, { title: string; detail: string; action?: string; role: string }> = {
    documents: { title: blocker ? "Riješite problem prije dolaska" : "Provjerite dokumente i pripremu", detail: blocker?.details || "Prikažite samo ono što nedostaje ili traži potvrdu.", action: "Otvori dokumente i pripremu", role: "Recepcija ili medicinska sestra/tehničar" },
    arrival: { title: blocker ? "Prijem traži dodatnu provjeru" : "Dovršite prijem", detail: blocker?.details || "Evidentirajte dolazak i dovršite potrebne provjere.", action: "Otvori prijem", role: "Recepcija ili medicinska sestra/tehničar" },
    encounter: { title: journey.current_stage === "in_encounter" ? "Pregled je u tijeku" : "Pacijent čeka liječnika", detail: blocker?.details || "Administrativni prijem je završen.", action: journey.current_stage === "in_encounter" ? "Nastavi pregled" : "Otvori pregled", role: "Liječnik" },
    consumables: { title: "Potvrdite potrošni materijal", detail: "Pregled je završen, a materijal još nije potvrđen.", action: "Evidentiraj materijal", role: "Medicinska sestra/tehničar ili liječnik" },
    billing: { title: journey.current_stage === "awaiting_payment" ? "Evidentirajte plaćanje" : "Pripremite račun", detail: "Klinički dio i materijal su riješeni.", action: "Otvori naplatu", role: "Naplata ili recepcija" },
    completed: { title: "Dolazak je završen", detail: "Nema otvorene operativne radnje.", role: "—" },
  };
  const item = content[stage];
  return <section className="journey-next-action" aria-labelledby="journey-next-title"><div><span>Što sada treba napraviti?</span><h2 id="journey-next-title">{item.title}</h2><p>{item.detail}</p><small>Odgovorna uloga: {item.role}</small></div>{item.action && <button type="button" className="primary" onClick={() => onSelect(stage)}>{item.action}<ArrowRight size={16}/></button>}</section>;
}

export function JourneyStageStepper({ active, current, onSelect }: { active: JourneyStageKey; current: JourneyStageKey; onSelect: (stage: JourneyStageKey) => void }) {
  const currentIndex = journeyStages.findIndex(item => item.key === current);
  return <nav className="journey-stage-stepper" aria-label="Faze tijeka pacijenta">{journeyStages.map((item, index) => {
    const completed = index < currentIndex; const isActive = item.key === active;
    return <button type="button" key={item.key} className={isActive ? "active" : completed ? "completed" : "future"} aria-current={isActive ? "step" : undefined} onClick={() => onSelect(item.key)}>{completed ? <Check size={15}/> : <Circle size={13}/>}<span>{item.label}</span></button>;
  })}</nav>;
}
