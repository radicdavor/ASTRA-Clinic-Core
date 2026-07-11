import { SyntheticScenario } from "../types/syntheticReview";

export function SyntheticLimitations({ scenario }: { scenario: SyntheticScenario }) {
  return (
    <div className="program1-two-column">
      <section className="knowledge-card">
        <h3>Ogranicenja</h3>
        <ul>
          {scenario.limitations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
      <section className="knowledge-card">
        <h3>Zabranjena tumacenja</h3>
        <ul>
          {scenario.prohibitedInterpretations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    </div>
  );
}
