import { useState } from "react";
import { WorkspaceTabs } from "../../components/workspace/WorkspaceTabs";
import { syntheticScenarios, defaultSyntheticScenarioId } from "../data/syntheticScenarios";
import { SyntheticComparison } from "../components/SyntheticComparison";
import { SyntheticEmptyState } from "../components/SyntheticEmptyState";
import { SyntheticEvidenceList } from "../components/SyntheticEvidenceList";
import { SyntheticFindingsList } from "../components/SyntheticFindingsList";
import { SyntheticLimitations } from "../components/SyntheticLimitations";
import { SyntheticReadinessPanel } from "../components/SyntheticReadinessPanel";
import { SyntheticSafetyBanner } from "../components/SyntheticSafetyBanner";
import { SyntheticScenarioOverview } from "../components/SyntheticScenarioOverview";
import { SyntheticScenarioSelector } from "../components/SyntheticScenarioSelector";
import { SyntheticTimeline } from "../components/SyntheticTimeline";
import { SyntheticScenarioId } from "../types/syntheticReview";
import { filterSyntheticScenarios, findSyntheticScenario } from "../utils/syntheticReviewSelectors";

export function SyntheticReviewWorkspace() {
  const [selectedId, setSelectedId] = useState<SyntheticScenarioId>(defaultSyntheticScenarioId);
  const [query, setQuery] = useState("");
  const [timelineCategory, setTimelineCategory] = useState("");
  const [evidenceStatus, setEvidenceStatus] = useState("");
  const [findingState, setFindingState] = useState("");
  const [leftId, setLeftId] = useState<SyntheticScenarioId>("SYN-ALPHA");
  const [rightId, setRightId] = useState<SyntheticScenarioId>("SYN-BETA");

  const filteredScenarios = filterSyntheticScenarios(syntheticScenarios, query);
  const selected = findSyntheticScenario(syntheticScenarios, selectedId);
  const timelineCategories = selected ? Array.from(new Set(selected.timeline.map((event) => event.category))).sort() : [];
  const tabs = selected ? [
    {
      id: "summary",
      label: "Sazetak",
      content: <SyntheticScenarioOverview scenario={selected} />
    },
    {
      id: "timeline",
      label: "Vremenska crta",
      content: (
        <section className="workflow-panel">
          <div className="page-header">
            <div>
              <h2>Vremenska crta</h2>
              <p>Relativni prikaz sinteticnih dogadaja bez klinickog sljedeceg koraka.</p>
            </div>
            <label>
              <span>Kategorija</span>
              <select value={timelineCategory} onChange={(event) => setTimelineCategory(event.target.value)}>
                <option value="">Sve kategorije</option>
                {timelineCategories.map((category) => <option key={category} value={category}>{category}</option>)}
              </select>
            </label>
          </div>
          <SyntheticTimeline scenario={selected} categoryFilter={timelineCategory} />
        </section>
      )
    },
    {
      id: "evidence",
      label: "Dokazi / dokumenti",
      content: (
        <section className="workflow-panel">
          <div className="page-header">
            <div>
              <h2>Dokazi / dokumenti</h2>
              <p>Samo sinteticne repository fixture stavke. Nema uploada, preuzimanja ili stvarnih izvora.</p>
            </div>
            <label>
              <span>Status dokaza</span>
              <select value={evidenceStatus} onChange={(event) => setEvidenceStatus(event.target.value)}>
                <option value="">Svi statusi</option>
                <option value="available">Dostupno</option>
                <option value="missing">Nedostaje</option>
                <option value="ambiguous">Nejasno</option>
              </select>
            </label>
          </div>
          <SyntheticEvidenceList scenario={selected} statusFilter={evidenceStatus} />
        </section>
      )
    },
    {
      id: "findings",
      label: "Nalazi",
      content: (
        <section className="workflow-panel">
          <div className="page-header">
            <div>
              <h2>Nalazi</h2>
              <p>Deskriptivni sinteticni nalazi. Nisu zadaci, odluke, preporuke ili klinicki zakljucci.</p>
            </div>
            <label>
              <span>Stanje nalaza</span>
              <select value={findingState} onChange={(event) => setFindingState(event.target.value)}>
                <option value="">Sva stanja</option>
                <option value="open">Otvoreno u scenariju</option>
                <option value="resolved-in-scenario">Zatvoreno u scenariju</option>
                <option value="uncertain">Neizvjesno u scenariju</option>
              </select>
            </label>
          </div>
          <SyntheticFindingsList scenario={selected} stateFilter={findingState} />
        </section>
      )
    },
    {
      id: "readiness",
      label: "Spremnost / completeness",
      content: (
        <section className="workflow-panel">
          <h2>Potpunost sinteticnog scenarija</h2>
          <SyntheticReadinessPanel scenario={selected} />
        </section>
      )
    },
    {
      id: "limits",
      label: "Ogranicenja",
      content: (
        <section className="workflow-panel">
          <h2>Ogranicenja i zabranjena tumacenja</h2>
          <SyntheticLimitations scenario={selected} />
        </section>
      )
    }
  ] : [];

  return (
    <section className="page program1-workspace">
      <div className="page-header">
        <div>
          <h1>Program 1 - Synthetic Review</h1>
          <p>Local/demo-only read-only workspace with repository-controlled synthetic data.</p>
        </div>
        <span className="readiness-pill readiness-attention_needed">Sinteticni demo</span>
      </div>

      <SyntheticSafetyBanner />

      <section className="workflow-panel" aria-labelledby="program1-filter-title">
        <div className="page-header">
          <div>
            <h2 id="program1-filter-title">Pretrazivanje sinteticnog sadrzaja</h2>
            <p>Pretraga radi samo nad lokalnim in-memory fixtureima. Nema backend zahtjeva i nema povijesti pretrage.</p>
          </div>
          <label>
            <span>Filter scenarija</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} />
          </label>
        </div>
      </section>

      {filteredScenarios.length === 0 ? (
        <SyntheticEmptyState title="Nema sinteticnog scenarija" message="Promijenite filter. Nema backend pretrage." />
      ) : (
        <SyntheticScenarioSelector scenarios={filteredScenarios} selectedId={selectedId} onSelect={setSelectedId} />
      )}

      {selected ? (
        <>
          <WorkspaceTabs tabs={tabs} />
          <SyntheticComparison
            scenarios={syntheticScenarios}
            leftId={leftId}
            rightId={rightId}
            onLeftChange={setLeftId}
            onRightChange={setRightId}
            onReset={() => {
              setLeftId("SYN-ALPHA");
              setRightId("SYN-BETA");
            }}
          />
        </>
      ) : (
        <SyntheticEmptyState title="Scenarij nije pronaden" message="Odabrani scenarij nije dostupan u lokalnim fixtureima." />
      )}
    </section>
  );
}
