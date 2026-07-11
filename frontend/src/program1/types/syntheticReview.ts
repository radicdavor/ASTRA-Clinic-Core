export type SyntheticScenarioId = "SYN-ALPHA" | "SYN-BETA" | "SYN-GAMMA" | "SYN-DELTA" | "SYN-EPSILON";

export type EvidenceStatus = "available" | "missing" | "ambiguous";
export type FindingState = "open" | "resolved-in-scenario" | "uncertain";
export type CompletenessState = "documented" | "incomplete" | "not-applicable" | "blocked";

export interface SyntheticProvenance {
  source: "repository-controlled-synthetic-fixture";
  derivedFromExistingSandbox: boolean;
  sourceReference: string;
  realDataUsed: false;
}

export interface SyntheticTimelineEvent {
  id: string;
  relativeTime: string;
  category: string;
  title: string;
  description: string;
  evidenceIds: string[];
}

export interface SyntheticEvidenceItem {
  id: string;
  type: string;
  title: string;
  summary: string;
  status: EvidenceStatus;
  sourceLabel: string;
}

export interface SyntheticFinding {
  id: string;
  title: string;
  description: string;
  state: FindingState;
  evidenceIds: string[];
  limitation: string;
}

export interface SyntheticReadinessItem {
  id: string;
  label: string;
  state: CompletenessState;
  rationale: string;
}

export interface SyntheticScenario {
  id: SyntheticScenarioId;
  syntheticOnly: true;
  version: string;
  title: string;
  purpose: string;
  subjectLabel: string;
  summary: string;
  reviewQuestion: string;
  timeline: SyntheticTimelineEvent[];
  evidence: SyntheticEvidenceItem[];
  findings: SyntheticFinding[];
  readiness: SyntheticReadinessItem[];
  limitations: string[];
  prohibitedInterpretations: string[];
  provenance: SyntheticProvenance;
}

export interface SyntheticComparison {
  left: SyntheticScenario;
  right: SyntheticScenario;
  evidenceStatuses: EvidenceStatus[];
  findingStates: FindingState[];
  completenessStates: CompletenessState[];
}
