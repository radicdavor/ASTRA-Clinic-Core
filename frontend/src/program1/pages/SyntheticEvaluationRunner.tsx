import { useMemo, useState } from "react";
import { RotateCcw } from "lucide-react";
import { SyntheticEvaluationBoundary } from "../components/SyntheticEvaluationBoundary";
import { SyntheticEvaluationPreflight } from "../components/SyntheticEvaluationPreflight";
import { SyntheticEvaluationTaskList } from "../components/SyntheticEvaluationTaskList";
import { syntheticEvaluationPreflight, syntheticEvaluationTasks } from "../data/syntheticEvaluation";
import { SyntheticEvaluationTaskStatus } from "../types/syntheticEvaluation";

export function SyntheticEvaluationRunner() {
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [statuses, setStatuses] = useState<Record<string, SyntheticEvaluationTaskStatus>>({});
  const [stopped, setStopped] = useState(false);
  const preflightComplete = checked.size === syntheticEvaluationPreflight.length;
  const completedCount = useMemo(
    () => Object.values(statuses).filter((status) => status !== "not-reviewed").length,
    [statuses]
  );

  function updatePreflight(id: string, value: boolean) {
    setChecked((current) => {
      const next = new Set(current);
      value ? next.add(id) : next.delete(id);
      return next;
    });
  }

  function resetRunner() {
    setChecked(new Set());
    setStatuses({});
    setStopped(false);
  }

  return (
    <section className="page program1-workspace program1-evaluation-runner">
      <div className="page-header">
        <div>
          <h1>Program 1 - Moderator Evaluation Runner</h1>
          <p>Vođeni lokalni prolaz kroz Phase C synthetic-only protokol. Bez spremanja, izvoza i session evidence tvrdnje.</p>
        </div>
        <span className="readiness-pill readiness-attention_needed">Lokalni transient runner</span>
      </div>

      <SyntheticEvaluationBoundary />

      <section className="program1-evaluation-summary" aria-label="Sažetak prolaznog napretka">
        <div><span>Preflight</span><strong>{checked.size}/{syntheticEvaluationPreflight.length}</strong></div>
        <div><span>Pregledani zadaci</span><strong>{completedCount}/{syntheticEvaluationTasks.length}</strong></div>
        <div><span>Stop stanje</span><strong>{stopped ? "AKTIVNO" : "Nije aktivno"}</strong></div>
      </section>

      {stopped && (
        <section className="program1-stop-banner" role="alert">
          <strong>PROLAZ JE ZAUSTAVLJEN</strong>
          <p>Ne nastavljajte zadatke. Slijedite Phase C stop-condition i deviation protokol.</p>
        </section>
      )}

      <SyntheticEvaluationPreflight
        items={syntheticEvaluationPreflight}
        checked={checked}
        disabled={stopped}
        onChange={updatePreflight}
      />

      <SyntheticEvaluationTaskList
        tasks={syntheticEvaluationTasks}
        statuses={statuses}
        enabled={preflightComplete && !stopped}
        stopped={stopped}
        onStatusChange={(taskId, status) => setStatuses((current) => ({ ...current, [taskId]: status }))}
      />

      <section className="workflow-panel program1-evaluation-controls" aria-labelledby="evaluation-controls-title">
        <h2 id="evaluation-controls-title">Stop i reset</h2>
        <p>Stop koristite čim se pojave stvarni podaci, kliničko oslanjanje, povlačenje pristanka ili druga granica iz Phase C protokola.</p>
        <div>
          <button type="button" className="action-button action-danger" disabled={stopped} onClick={() => setStopped(true)}>
            Zaustavi lokalni prolaz
          </button>
          <button type="button" className="action-button" onClick={resetRunner}>
            <RotateCcw size={16} aria-hidden="true" /> Resetiraj prolazni prikaz
          </button>
        </div>
      </section>
    </section>
  );
}
