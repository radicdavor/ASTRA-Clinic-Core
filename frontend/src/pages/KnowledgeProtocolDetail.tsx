import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { useApi } from "../hooks/useApi";
import { KnowledgeProtocol } from "../types";

export function KnowledgeProtocolDetail() {
  const { id } = useParams();
  const protocol = useApi<KnowledgeProtocol | null>(`/api/knowledge-protocols/${id}`, null);
  const [openRuleIds, setOpenRuleIds] = useState<Set<number>>(new Set());

  if (!protocol.data) return <div className="page">Učitavanje...</div>;

  const refresh = async (path: string) =>
    protocol.setData(await api<KnowledgeProtocol>(path, { method: "POST" }));

  const toggleRule = (ruleId: number) => {
    setOpenRuleIds(current => {
      const next = new Set(current);
      if (next.has(ruleId)) next.delete(ruleId);
      else next.add(ruleId);
      return next;
    });
  };

  return (
    <div className="page knowledge-detail">
      <header className="page-header">
        <div>
          <span className="eyebrow">{protocol.data.specialty} · verzija {protocol.data.version}</span>
          <h1>{protocol.data.title}</h1>
          <p>{protocol.data.summary}</p>
        </div>
        <span className={`knowledge-state ${protocol.data.status}`}>{protocol.data.status}</span>
      </header>

      <section className="panel provenance-line">
        <div><span>Tvrdnja</span><strong>{protocol.data.rules.length} strukturiranih pravila</strong></div>
        <div><span>Pregled</span><strong>{protocol.data.status === "reviewed" ? "Liječnički pregledano" : "Nije službeno"}</strong></div>
        <div><span>Izvor</span><a href={protocol.data.source_url} target="_blank" rel="noreferrer">{protocol.data.source_title}</a></div>
      </section>

      <section className="knowledge-rules" aria-label="Postupanja">
        {protocol.data.rules.map(rule => {
          const isOpen = openRuleIds.has(rule.id);
          const explanationId = `knowledge-rule-explanation-${rule.id}`;
          return (
            <article className={`knowledge-rule ${isOpen ? "open" : ""}`} key={rule.id}>
              <div className="knowledge-rule-header">
                <h2>{rule.label}</h2>
                <button
                  type="button"
                  className="knowledge-rule-toggle"
                  aria-expanded={isOpen}
                  aria-controls={explanationId}
                  aria-label={`${isOpen ? "Sakrij" : "Prikaži"} objašnjenje: ${rule.label}`}
                  onClick={() => toggleRule(rule.id)}
                >
                  <span>{isOpen ? "Sakrij" : "Prikaži"}</span>
                  <ChevronDown size={17} aria-hidden="true" />
                </button>
              </div>
              {isOpen && (
                <div className="knowledge-rule-explanation" id={explanationId}>
                  <p className="knowledge-evidence">{rule.evidence_level || "Razina dokaza nije navedena"}</p>
                  <div><h3>Kada razmotriti</h3><p>{rule.condition_text}</p></div>
                  <div><h3>Referentna smjernica</h3><p>{rule.guidance_text}</p></div>
                  <small>Ovo nije automatska odluka niti preporuka za konkretnog pacijenta.</small>
                </div>
              )}
            </article>
          );
        })}
      </section>

      <div className="quick-actions">
        {protocol.data.status === "draft" && <ActionButton variant="update" onClick={() => refresh(`/api/knowledge-protocols/${id}/review`)} helpTitle="Potvrdi pregled" help="Liječnik potvrđuje izvor i sadržaj protokola.">Potvrdi liječnički pregled</ActionButton>}
        {protocol.data.status !== "archived" && <ActionButton variant="danger" confirmMessage="Arhivirati ovaj protokol?" onClick={() => refresh(`/api/knowledge-protocols/${id}/archive`)} helpTitle="Arhiviraj" help="Uklanja protokol iz aktivne službene knjižnice.">Arhiviraj</ActionButton>}
      </div>
    </div>
  );
}
