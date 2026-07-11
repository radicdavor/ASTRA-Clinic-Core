import { SyntheticScenario } from "../types/syntheticReview";

const statusLabels = {
  available: "dostupno",
  missing: "nedostaje",
  ambiguous: "nejasno"
};

export function SyntheticEvidenceList({ scenario, statusFilter }: { scenario: SyntheticScenario; statusFilter: string }) {
  const evidence = statusFilter ? scenario.evidence.filter((item) => item.status === statusFilter) : scenario.evidence;
  return (
    <div className="program1-card-grid">
      {evidence.map((item) => (
        <article key={item.id} className="knowledge-card">
          <h3>{item.title}</h3>
          <span className={`program1-pill program1-${item.status}`}>{statusLabels[item.status]}</span>
          <p>{item.summary}</p>
          <small>{item.type} / {item.sourceLabel}</small>
        </article>
      ))}
    </div>
  );
}
