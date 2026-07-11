import { SyntheticScenarioId } from "./syntheticReview";

export type SyntheticEvaluationTaskStatus = "not-reviewed" | "completed" | "assistance-needed";

export interface SyntheticEvaluationTask {
  id: string;
  order: number;
  title: string;
  prompt: string;
  scenarioId?: SyntheticScenarioId;
  successSignals: string[];
}

export interface SyntheticEvaluationPreflightItem {
  id: string;
  label: string;
}
