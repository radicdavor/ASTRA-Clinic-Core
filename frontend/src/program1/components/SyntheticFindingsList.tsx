import { SyntheticScenario } from "../types/syntheticReview";

const stateLabels = {
  open: "otvoreno u scenariju",
  "resolved-in-scenario": "zatvoreno u scenariju",
  uncertain: "neizvjesno u scenariju"
};

export function SyntheticFindingsList({ scenario, stateFilter }: { scenario: SyntheticScenario; stateFilter: string }) {
  const findings = stateFilter ? scenario.findings.filter((item) => item.state === stateFilter) : scenario.findings;
  return (
    <div className="program1-card-grid">
      {findings.map((finding) => (
        <article key={finding.id} className="knowledge-card">
          <h3>{finding.title}</h3>
          <span className={`program1-pill program1-${finding.state}`}>{stateLabels[finding.state]}</span>
          <p>{finding.description}</p>
          <small>Dokazi: {finding.evidenceIds.join(", ")}</small>
          <small>Ogranicenje: {finding.limitation}</small>
          <small>Sinteticni scenarij; nije klinicki nalaz.</small>
        </article>
      ))}
    </div>
  );
}
