import { useState } from "react";
import { api } from "../../api/client";
import type { SignedClinicalReport, VisitDocument } from "../../types/program2";

export function VisitDocumentCenter({ journeyId, items, onChanged }: { journeyId: number; items: VisitDocument[]; onChanged: () => Promise<void> }) {
  const [selected, setSelected] = useState<number[]>([]);
  const [preview, setPreview] = useState<SignedClinicalReport | null>(null);
  const [message, setMessage] = useState("");
  function toggle(id: number) { setSelected(value => value.includes(id) ? value.filter(item => item !== id) : [...value, id]); }
  async function print(report: SignedClinicalReport) {
    await api(`/api/signed-reports/${report.id}/print`, { method: "POST" });
    setPreview(report); setMessage("Ispis koristi točno ovu potpisanu verziju.");
    window.setTimeout(() => window.print(), 0);
    await onChanged();
  }
  async function deliver() {
    const recipient = window.prompt("E-mail pacijenta za demo/stub dostavu");
    if (!recipient?.trim() || selected.length === 0) return;
    const hasSuperseded = items.some(item => selected.includes(item.report.id) && item.report.superseded_at);
    const acknowledge = !hasSuperseded || window.confirm("Odabrana je starija verzija nalaza. Svejedno evidentirati dostavu?");
    if (!acknowledge) return;
    await api(`/api/patient-journeys/${journeyId}/visit-documents/deliver`, { method: "POST", body: JSON.stringify({ report_ids: selected, recipient: recipient.trim(), acknowledge_superseded: hasSuperseded }) });
    setMessage("Dostava je evidentirana samo u demo/stub redu. Slanje pacijentu nije potvrđeno.");
    await onChanged();
  }
  return <section className="journey-panel visit-document-center">
    <header><div><span className="eyebrow">Dokumenti ovog dolaska</span><h2>Potpisani nalazi</h2></div>{selected.length > 0 && <button type="button" onClick={deliver}>Pošalji odabrano ({selected.length})</button>}</header>
    {message && <p className="document-center-message" role="status">{message}</p>}
    {items.length === 0 ? <p>Još nema potpisanih nalaza. Potpisani obrazac automatski će se pojaviti ovdje.</p> : <div className="visit-document-list">{items.map(item => <article key={item.report.id} className={item.report.superseded_at ? "superseded" : ""}>
      <input aria-label={`Odaberi ${item.report.title}`} type="checkbox" checked={selected.includes(item.report.id)} onChange={() => toggle(item.report.id)}/>
      <div><b>{item.report.title}</b><small>Aktivnost {item.report.activity_id} · verzija {item.report.version_number} · {item.report.signer_name} · {new Date(item.report.signed_at).toLocaleDateString("hr-HR")}</small><small>{item.report.superseded_at ? "Zamijenjena novijom verzijom" : "Važeća potpisana verzija"} · ispisa: {item.print_count} · dostava: {item.latest_delivery?.status === "queued_stub" ? "demo/stub red" : item.latest_delivery?.status ?? "nije zatražena"}</small></div>
      <div className="row-actions"><button type="button" onClick={() => setPreview(item.report)}>Pregled</button><button type="button" onClick={() => print(item.report)}>Ispis</button></div>
    </article>)}</div>}
    {preview && <div className="modal-backdrop" role="presentation" onMouseDown={() => setPreview(null)}><section className="modal-card signed-report-preview" role="dialog" aria-modal="true" aria-label={preview.title} onMouseDown={event => event.stopPropagation()}><header><div><span className="eyebrow">Potpisana verzija {preview.version_number}</span><h2>{preview.title}</h2><p>{preview.signer_name} · {new Date(preview.signed_at).toLocaleString("hr-HR")}</p></div><button type="button" aria-label="Zatvori" onClick={() => setPreview(null)}>×</button></header><pre>{preview.rendered_content}</pre></section></div>}
  </section>;
}
