import { SyntheticScenario } from "../types/syntheticReview";
import { SyntheticEmptyState } from "./SyntheticEmptyState";

const statusLabels = {
  available: "dostupno",
  missing: "nedostaje",
  ambiguous: "nejasno"
};

export function SyntheticEvidenceList({ scenario, statusFilter }: { scenario: SyntheticScenario; statusFilter: string }) {
  const evidence = statusFilter ? scenario.evidence.filter((item) => item.status === statusFilter) : scenario.evidence;
  if (evidence.length === 0) {
    return <SyntheticEmptyState title="Nema sinteticnih dokaza" message="Promijenite status dokaza. Nema backend pretrage." />;
  }
  return (
    <div className="program1-card-grid" role="list" aria-label="Sinteticni dokazi">
      {evidence.map((item) => (
        <article key={item.id} className="knowledge-card" role="listitem">
          <h3>{item.title}</h3>
          <span className={`program1-pill program1-${item.status}`} role="status">{statusLabels[item.status]}</span>
          <p>{item.summary}</p>
          <small>{item.type} / {item.sourceLabel}</small>
        </article>
      ))}
    </div>
  );
}
