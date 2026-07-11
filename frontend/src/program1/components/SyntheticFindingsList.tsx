import { SyntheticScenario } from "../types/syntheticReview";
import { SyntheticEmptyState } from "./SyntheticEmptyState";

const stateLabels = {
  open: "otvoreno u scenariju",
  "resolved-in-scenario": "zatvoreno u scenariju",
  uncertain: "neizvjesno u scenariju"
};

export function SyntheticFindingsList({ scenario, stateFilter }: { scenario: SyntheticScenario; stateFilter: string }) {
  const findings = stateFilter ? scenario.findings.filter((item) => item.state === stateFilter) : scenario.findings;
  if (findings.length === 0) {
    return <SyntheticEmptyState title="Nema sinteticnih nalaza" message="Promijenite stanje nalaza. Nema backend pretrage." />;
  }
  return (
    <div className="program1-card-grid" role="list" aria-label="Sinteticni nalazi">
      {findings.map((finding) => (
        <article key={finding.id} className="knowledge-card" role="listitem">
          <h3>{finding.title}</h3>
          <span className={`program1-pill program1-${finding.state}`} role="status">{stateLabels[finding.state]}</span>
          <p>{finding.description}</p>
          <small>Dokazi: {finding.evidenceIds.join(", ")}</small>
          <small>Ogranicenje: {finding.limitation}</small>
          <small>Sinteticni scenarij; nije klinicki nalaz.</small>
        </article>
      ))}
    </div>
  );
}
