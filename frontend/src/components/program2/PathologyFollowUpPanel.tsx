import { api } from "../../api/client";
import type { PathologyCase } from "../../types/program2";

const labels: Record<string, string> = { specimens_ready: "Uzorci spremni", sent_to_lab: "Predano laboratoriju", received_by_lab: "Laboratorij zaprimio", awaiting_result: "Čeka nalaz", clinician_review_required: "Čeka pregled liječnika", clinician_reviewed: "Liječnik pregledao", patient_notification_ready: "Spremno za odobrenu dostavu", patient_notified: "Pacijent obaviješten", closed: "Zatvoreno", cancelled: "Otkazano" };
const next: Record<string, { target: string; label: string } | undefined> = { specimens_ready: { target: "sent_to_lab", label: "Predano laboratoriju" }, sent_to_lab: { target: "received_by_lab", label: "Laboratorij zaprimio" }, received_by_lab: { target: "awaiting_result", label: "Čeka nalaz" }, clinician_reviewed: { target: "patient_notification_ready", label: "Pripremi obavijest" } };

export function PathologyFollowUpPanel({ items, onChanged }: { items: PathologyCase[]; onChanged: () => Promise<void> }) {
  async function advance(item: PathologyCase) {
    const action = next[item.status]; if (!action) return;
    const external_case_number = item.status === "specimens_ready" ? window.prompt("Vanjski broj slučaja (opcionalno)") : undefined;
    await api(`/api/pathology-cases/${item.id}/transition`, { method: "POST", body: JSON.stringify({ target_status: action.target, external_case_number: external_case_number || null }) });
    await onChanged();
  }
  if (items.length === 0) return null;
  return <section className="journey-panel pathology-follow-up"><header><div><span className="eyebrow">Praćenje nakon dolaska</span><h2>Patologija</h2></div></header>{items.map(item => <article key={item.id}><i className={`activity-dot ${item.status === "clinician_review_required" ? "in_progress" : ["closed", "patient_notified"].includes(item.status) ? "completed" : ""}`} aria-hidden="true"/><div><b>{labels[item.status] ?? item.status}</b><small>{item.specimens.map(specimen => `${specimen.specimen_label}: ${specimen.anatomical_site}`).join(" · ")}</small><small>{item.external_case_number ? `Broj slučaja: ${item.external_case_number}` : "Vanjski broj još nije upisan"}</small></div>{next[item.status] && <button type="button" onClick={() => advance(item)}>{next[item.status]?.label}</button>}</article>)}</section>;
}
