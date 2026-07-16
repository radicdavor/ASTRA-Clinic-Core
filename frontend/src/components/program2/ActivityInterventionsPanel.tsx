import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { JourneyActivity, ProcedureIntervention } from "../../types/program2";

const names: Record<string, string> = { biopsy: "Biopsija", polypectomy: "Polipektomija", injection: "Injekcija", clip_placement: "Klipse", dilation: "Dilatacija", hemostasis: "Hemostaza", foreign_body_removal: "Uklanjanje stranog tijela", other: "Drugo" };

export function ActivityInterventionsPanel({ journeyId, activity, onChanged }: { journeyId: number; activity: JourneyActivity; onChanged: () => Promise<void> }) {
  const [items, setItems] = useState<ProcedureIntervention[]>([]);
  const [type, setType] = useState("biopsy"); const [site, setSite] = useState(""); const [complication, setComplication] = useState("Nema");
  const base = `/api/patient-journeys/${journeyId}/activities/${activity.id}`;
  async function load() { setItems(await api<ProcedureIntervention[]>(`${base}/interventions`)); }
  useEffect(() => { load().catch(() => setItems([])); }, [activity.id]);
  async function add() {
    if (!site.trim()) return;
    const intervention = await api<ProcedureIntervention>(`${base}/interventions`, { method: "POST", body: JSON.stringify({ intervention_type: type, anatomical_site: site.trim(), count: 1, retrieval_status: type === "biopsy" || type === "polypectomy" ? "collected" : null, complication: complication.trim() || "Nema" }) });
    if (["biopsy", "polypectomy"].includes(type) && window.confirm("Je li uzorak poslan na patologiju?")) {
      const label = window.prompt("Oznaka uzorka", `U${items.length + 1}`);
      if (label?.trim()) await api(`${base}/pathology-case`, { method: "POST", body: JSON.stringify({ specimens: [{ specimen_label: label.trim(), anatomical_site: site.trim(), specimen_type: type === "biopsy" ? "biopsy" : "polyp", source_intervention_id: intervention.id, collection_time: new Date().toISOString() }] }) });
    }
    setSite(""); setComplication("Nema"); await load(); await onChanged();
  }
  return <section className="journey-panel activity-interventions"><header><div><span className="eyebrow">Odabrana aktivnost</span><h2>Intervencije i uzorci</h2></div></header>{items.length > 0 && <div className="intervention-list">{items.map(item => <span key={item.id}><b>{names[item.intervention_type] ?? item.intervention_type}</b> · {item.anatomical_site} · komplikacije: {item.complication ?? "nije razriješeno"}</span>)}</div>}{activity.status === "in_progress" && <div className="intervention-entry"><select aria-label="Vrsta intervencije" value={type} onChange={event => setType(event.target.value)}>{Object.entries(names).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><input aria-label="Anatomsko mjesto" placeholder="Anatomsko mjesto" value={site} onChange={event => setSite(event.target.value)}/><input aria-label="Komplikacije" placeholder="Komplikacije ili Nema" value={complication} onChange={event => setComplication(event.target.value)}/><button type="button" onClick={add}>Dodaj intervenciju</button></div>}</section>;
}
