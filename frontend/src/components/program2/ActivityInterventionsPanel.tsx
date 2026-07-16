import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { interventionLabels } from "../../constants/clinicalRegistries";
import type { JourneyActivity, ProcedureIntervention } from "../../types/program2";

const names: Record<string, string> = interventionLabels;
type StagedSpecimen = { specimen_label: string; anatomical_site: string; specimen_type: string; source_intervention_id: number; collection_time: string; container: string; fixation: string };

export function ActivityInterventionsPanel({ journeyId, activity, onChanged }: { journeyId: number; activity: JourneyActivity; onChanged: () => Promise<void> }) {
  const [items, setItems] = useState<ProcedureIntervention[]>([]); const [staged, setStaged] = useState<StagedSpecimen[]>([]);
  const [type, setType] = useState("biopsy"); const [site, setSite] = useState(""); const [technique, setTechnique] = useState(""); const [size, setSize] = useState(""); const [complication, setComplication] = useState("Nema");
  const [createSpecimen, setCreateSpecimen] = useState(true); const [label, setLabel] = useState(""); const [error, setError] = useState("");
  const base = `/api/patient-journeys/${journeyId}/activities/${activity.id}`;
  async function load() { setItems(await api<ProcedureIntervention[]>(`${base}/interventions`)); }
  useEffect(() => { setStaged([]); load().catch(() => setItems([])); }, [activity.id]);
  async function add() {
    if (!site.trim() || !complication.trim()) return;
    if (createSpecimen && ["biopsy", "polypectomy"].includes(type) && !label.trim()) { setError("Upišite jedinstvenu oznaku uzorka."); return; }
    setError("");
    const intervention = await api<ProcedureIntervention>(`${base}/interventions`, { method: "POST", body: JSON.stringify({ intervention_type: type, anatomical_site: site.trim(), technique: technique.trim() || null, size: size.trim() || null, count: 1, retrieval_status: type === "biopsy" || type === "polypectomy" ? "collected" : "not_applicable", complication: complication.trim() }) });
    if (createSpecimen && ["biopsy", "polypectomy"].includes(type)) setStaged(current => [...current, { specimen_label: label.trim(), anatomical_site: site.trim(), specimen_type: type === "biopsy" ? "biopsy" : "polyp", source_intervention_id: intervention.id, collection_time: new Date().toISOString(), container: "Zaseban spremnik", fixation: "Formalin" }]);
    setSite(""); setTechnique(""); setSize(""); setLabel(""); await load(); await onChanged();
  }
  async function createPathology() {
    if (!staged.length) return;
    await api(`${base}/pathology-case`, { method: "POST", body: JSON.stringify({ idempotency_key: `activity-${activity.id}-pathology`, specimens: staged }) });
    setStaged([]); await onChanged();
  }
  return <section className="journey-panel activity-interventions"><header><div><span className="eyebrow">Odabrana aktivnost</span><h2>Intervencije i uzorci</h2></div></header>
    {items.length > 0 && <div className="intervention-list">{items.map(item => <span key={item.id}><b>{names[item.intervention_type] ?? item.intervention_type}</b> · {item.anatomical_site} · {item.technique || "bez upisane tehnike"} · komplikacije: {item.complication}</span>)}</div>}
    {activity.status === "in_progress" && <div className="intervention-entry structured"><select aria-label="Vrsta intervencije" value={type} onChange={event => { setType(event.target.value); setCreateSpecimen(["biopsy", "polypectomy"].includes(event.target.value)); }}>{Object.entries(names).map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select><input aria-label="Anatomsko mjesto" placeholder="Anatomsko mjesto" value={site} onChange={event => setSite(event.target.value)}/><input aria-label="Tehnika" placeholder="Tehnika" value={technique} onChange={event => setTechnique(event.target.value)}/><input aria-label="Veličina" placeholder="Veličina" value={size} onChange={event => setSize(event.target.value)}/><input aria-label="Komplikacije" placeholder="Komplikacije ili Nema" value={complication} onChange={event => setComplication(event.target.value)}/>
      {["biopsy", "polypectomy"].includes(type) && <label className="clinical-form-check"><input type="checkbox" checked={createSpecimen} onChange={event => setCreateSpecimen(event.target.checked)}/><span>Evidentiraj patološki uzorak</span></label>}{createSpecimen && ["biopsy", "polypectomy"].includes(type) && <input aria-label="Oznaka uzorka" placeholder="Oznaka uzorka, npr. G1" value={label} onChange={event => setLabel(event.target.value)}/>}<button type="button" onClick={add}>Dodaj intervenciju</button>
    </div>}
    {error && <p className="inline-error" role="alert">{error}</p>}
    {staged.length > 0 && <div className="staged-specimens"><strong>Uzorci za patologiju</strong>{staged.map(item => <span key={item.specimen_label}>{item.specimen_label} · {item.anatomical_site} · {item.specimen_type}</span>)}<button type="button" className="primary" onClick={createPathology}>Stvori patološki slučaj ({staged.length})</button></div>}
  </section>;
}
