import { SyntheticScenario, SyntheticScenarioId } from "../types/syntheticReview";
import { buildSyntheticComparison, groupEvidenceByStatus, groupFindingsByState } from "../utils/syntheticReviewSelectors";
import { SyntheticEmptyState } from "./SyntheticEmptyState";

function ScenarioColumn({ scenario }: { scenario: SyntheticScenario }) {
  const evidence = groupEvidenceByStatus(scenario);
  const findings = groupFindingsByState(scenario);
  return (
    <div className="program1-comparison-column">
      <h3>{scenario.id}</h3>
      <p>{scenario.title}</p>
      <dl>
        <dt>Pitanje pregleda</dt>
        <dd>{scenario.reviewQuestion}</dd>
        <dt>Dostupnost dokaza</dt>
        <dd>{Object.entries(evidence).map(([state, titles]) => `${state}: ${titles.join("; ")}`).join(" / ")}</dd>
        <dt>Stanja nalaza</dt>
        <dd>{Object.entries(findings).map(([state, titles]) => `${state}: ${titles.join("; ")}`).join(" / ")}</dd>
        <dt>Potpunost scenarija</dt>
        <dd>{scenario.readiness.map((item) => `${item.label}: ${item.state}`).join(" / ")}</dd>
        <dt>Ogranicenja</dt>
        <dd>{scenario.limitations.join(" / ")}</dd>
      </dl>
    </div>
  );
}

export function SyntheticComparison({
  scenarios,
  leftId,
  rightId,
  onLeftChange,
  onRightChange,
  onReset
}: {
  scenarios: SyntheticScenario[];
  leftId: SyntheticScenarioId;
  rightId: SyntheticScenarioId;
  onLeftChange: (id: SyntheticScenarioId) => void;
  onRightChange: (id: SyntheticScenarioId) => void;
  onReset: () => void;
}) {
  const left = scenarios.find((scenario) => scenario.id === leftId);
  const right = scenarios.find((scenario) => scenario.id === rightId);
  const comparison = left && right ? buildSyntheticComparison(left, right) : null;

  return (
    <section className="workflow-panel program1-comparison" aria-labelledby="program1-comparison-title">
      <div className="page-header">
        <div>
          <h2 id="program1-comparison-title">Deskriptivna usporedba</h2>
          <p>Usporedba je deskriptivna. Ne predstavlja rangiranje ili preporuku. Ne odreduje klinicki prioritet.</p>
        </div>
        <button type="button" className="action-button" onClick={onReset}>Resetiraj pogled</button>
      </div>
      <div className="filters">
        <label>
          <span>Lijevi scenarij</span>
          <select value={leftId} onChange={(event) => onLeftChange(event.target.value as SyntheticScenarioId)}>
            {scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.id}</option>)}
          </select>
        </label>
        <label>
          <span>Desni scenarij</span>
          <select value={rightId} onChange={(event) => onRightChange(event.target.value as SyntheticScenarioId)}>
            {scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.id}</option>)}
          </select>
        </label>
      </div>
      {!left || !right ? (
        <SyntheticEmptyState title="Scenarij nije pronaden" message="Odaberite postojece sinteticne scenarije." />
      ) : !comparison ? (
        <SyntheticEmptyState title="Odaberite dva razlicita scenarija" message="Usporedba istog scenarija nije prikazana." />
      ) : (
        <>
          <p className="program1-note">Scenariji se razlikuju prema dostupnosti sinteticnih dokaza i stanju dokumentiranosti.</p>
          <div className="program1-comparison-grid">
            <ScenarioColumn scenario={comparison.left} />
            <ScenarioColumn scenario={comparison.right} />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Podrucje</th>
                  <th>{comparison.left.id}</th>
                  <th>{comparison.right.id}</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>Identitet</td><td>{comparison.left.subjectLabel}</td><td>{comparison.right.subjectLabel}</td></tr>
                <tr><td>Dokazi</td><td>{comparison.left.evidence.length}</td><td>{comparison.right.evidence.length}</td></tr>
                <tr><td>Nalazi</td><td>{comparison.left.findings.length}</td><td>{comparison.right.findings.length}</td></tr>
                <tr><td>Ogranicenja</td><td>{comparison.left.limitations.length}</td><td>{comparison.right.limitations.length}</td></tr>
                <tr><td>Zabranjena tumacenja</td><td>{comparison.left.prohibitedInterpretations.length}</td><td>{comparison.right.prohibitedInterpretations.length}</td></tr>
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
