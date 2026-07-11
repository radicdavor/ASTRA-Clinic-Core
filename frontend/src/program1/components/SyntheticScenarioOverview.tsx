import { SyntheticScenario } from "../types/syntheticReview";

export function SyntheticScenarioOverview({ scenario }: { scenario: SyntheticScenario }) {
  return (
    <div className="program1-overview">
      <div className="summary-strip">
        <div><span>Scenarij</span><strong>{scenario.id}</strong></div>
        <div><span>Verzija</span><strong>{scenario.version}</strong></div>
        <div><span>Subjekt</span><strong>{scenario.subjectLabel}</strong></div>
        <div><span>Sinteticno</span><strong>{scenario.syntheticOnly ? "Da" : "Ne"}</strong></div>
        <div><span>Stvarni podaci</span><strong>{scenario.provenance.realDataUsed ? "Da" : "Ne"}</strong></div>
      </div>
      <section className="workflow-panel">
        <h2>{scenario.title}</h2>
        <div className="detail-list">
          <p><span>Svrha</span><strong>{scenario.purpose}</strong></p>
          <p><span>Pitanje pregleda</span><strong>{scenario.reviewQuestion}</strong></p>
          <p><span>Kratki sazetak</span><strong>{scenario.summary}</strong></p>
          <p><span>Provenijencija</span><strong>{scenario.provenance.sourceReference}</strong></p>
          <p><span>Izvor</span><strong>{scenario.provenance.source}</strong></p>
        </div>
      </section>
    </div>
  );
}
