import { SyntheticScenario } from "../types/syntheticReview";

const stateLabels = {
  documented: "dokumentirano",
  incomplete: "nepotpuno",
  "not-applicable": "nije primjenjivo",
  blocked: "blokirano u scenariju"
};

export function SyntheticReadinessPanel({ scenario }: { scenario: SyntheticScenario }) {
  return (
    <div className="program1-readiness">
      <p className="program1-note">Ovo je prikaz potpunosti sinteticnog scenarija, a ne klinicke spremnosti pacijenta.</p>
      <div className="program1-card-grid">
        {scenario.readiness.map((item) => (
          <article key={item.id} className="knowledge-card">
            <h3>{item.label}</h3>
            <span className={`program1-pill program1-${item.state}`}>{stateLabels[item.state]}</span>
            <p>{item.rationale}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
