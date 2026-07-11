import { SyntheticScenario, SyntheticScenarioId } from "../types/syntheticReview";

export function SyntheticScenarioSelector({
  scenarios,
  selectedId,
  onSelect
}: {
  scenarios: SyntheticScenario[];
  selectedId: SyntheticScenarioId;
  onSelect: (id: SyntheticScenarioId) => void;
}) {
  return (
    <section className="workflow-panel program1-selector" aria-labelledby="program1-selector-title">
      <div className="page-header">
        <div>
          <h2 id="program1-selector-title">Sinteticni scenarij</h2>
          <p>Odabir je privremen i resetira se osvjezavanjem stranice.</p>
        </div>
        <label>
          <span>Odaberi scenarij</span>
          <select value={selectedId} onChange={(event) => onSelect(event.target.value as SyntheticScenarioId)}>
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.id} - {scenario.title}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="program1-scenario-list">
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            type="button"
            className={scenario.id === selectedId ? "active" : ""}
            onClick={() => onSelect(scenario.id)}
          >
            <strong>{scenario.id}</strong>
            <span>{scenario.title}</span>
            <small>{scenario.purpose}</small>
          </button>
        ))}
      </div>
    </section>
  );
}
