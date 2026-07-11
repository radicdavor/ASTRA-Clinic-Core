import { SyntheticEvaluationTask, SyntheticEvaluationTaskStatus } from "../types/syntheticEvaluation";

const statusLabels: Record<SyntheticEvaluationTaskStatus, string> = {
  "not-reviewed": "Nije pregledano",
  completed: "Završeno bez pomoći",
  "assistance-needed": "Potrebna pomoć"
};

export function SyntheticEvaluationTaskList({
  tasks,
  statuses,
  enabled,
  stopped,
  onStatusChange
}: {
  tasks: SyntheticEvaluationTask[];
  statuses: Record<string, SyntheticEvaluationTaskStatus>;
  enabled: boolean;
  stopped: boolean;
  onStatusChange: (taskId: string, status: SyntheticEvaluationTaskStatus) => void;
}) {
  return (
    <section className="program1-evaluation-tasks" aria-labelledby="evaluation-tasks-title">
      <div className="page-header">
        <div>
          <h2 id="evaluation-tasks-title">Moderirani sintetički zadaci</h2>
          <p>Redoslijed 1–8 je dio protokola. Statusi su prolazni i ne predstavljaju kontrolirani session record.</p>
        </div>
      </div>
      {!enabled ? (
        <div className="program1-empty" role="status">
          <strong>Zadaci su zaključani</strong>
          <p>Potvrdite cijeli preflight. Ako je stop uvjet aktivan, resetirajte prolaz tek nakon nove autorizacije.</p>
        </div>
      ) : (
        <ol className="program1-evaluation-task-list">
          {tasks.map((task) => {
            const status = statuses[task.id] ?? "not-reviewed";
            return (
              <li key={task.id} className="program1-evaluation-task">
                <div className="program1-evaluation-task-number" aria-hidden="true">{task.order}</div>
                <div>
                  <div className="page-header">
                    <div>
                      <h3>{task.title}</h3>
                      {task.scenarioId && <span className="program1-pill">{task.scenarioId}</span>}
                    </div>
                    <span className={`program1-pill program1-task-${status}`} role="status">{statusLabels[status]}</span>
                  </div>
                  <p className="program1-evaluation-prompt">{task.prompt}</p>
                  <details>
                    <summary>Signali uspješnog prolaza</summary>
                    <ul>{task.successSignals.map((signal) => <li key={signal}>{signal}</li>)}</ul>
                  </details>
                  <fieldset disabled={stopped}>
                    <legend>Prolazni moderatorski status</legend>
                    {(["not-reviewed", "completed", "assistance-needed"] as SyntheticEvaluationTaskStatus[]).map((value) => (
                      <label key={value}>
                        <input
                          type="radio"
                          name={`task-${task.id}`}
                          value={value}
                          checked={status === value}
                          onChange={() => onStatusChange(task.id, value)}
                        />
                        <span>{statusLabels[value]}</span>
                      </label>
                    ))}
                  </fieldset>
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
