import { SyntheticEvaluationPreflightItem } from "../types/syntheticEvaluation";

export function SyntheticEvaluationPreflight({
  items,
  checked,
  disabled,
  onChange
}: {
  items: SyntheticEvaluationPreflightItem[];
  checked: Set<string>;
  disabled: boolean;
  onChange: (id: string, value: boolean) => void;
}) {
  return (
    <section className="workflow-panel program1-evaluation-preflight" aria-labelledby="evaluation-preflight-title">
      <div className="page-header">
        <div>
          <h2 id="evaluation-preflight-title">Preflight prije sudionika</h2>
          <p>Sve stavke moraju biti potvrđene prije otvaranja zadataka.</p>
        </div>
        <span className="program1-pill" role="status">{checked.size}/{items.length} potvrđeno</span>
      </div>
      <div className="program1-checklist">
        {items.map((item) => (
          <label key={item.id}>
            <input
              type="checkbox"
              checked={checked.has(item.id)}
              disabled={disabled}
              onChange={(event) => onChange(item.id, event.target.checked)}
            />
            <span>{item.label}</span>
          </label>
        ))}
      </div>
    </section>
  );
}
