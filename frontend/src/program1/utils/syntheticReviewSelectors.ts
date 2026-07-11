import { SyntheticComparison, SyntheticScenario, SyntheticScenarioId } from "../types/syntheticReview";

export function findSyntheticScenario(scenarios: SyntheticScenario[], id: SyntheticScenarioId) {
  return scenarios.find((scenario) => scenario.id === id);
}

export function filterSyntheticScenarios(scenarios: SyntheticScenario[], query: string) {
  const needle = query.trim().toLowerCase();
  if (!needle) return scenarios;
  return scenarios.filter((scenario) => `${scenario.id} ${scenario.title} ${scenario.purpose}`.toLowerCase().includes(needle));
}

export function buildSyntheticComparison(left: SyntheticScenario, right: SyntheticScenario): SyntheticComparison | null {
  if (left.id === right.id) return null;
  return {
    left,
    right,
    evidenceStatuses: Array.from(new Set([...left.evidence, ...right.evidence].map((item) => item.status))).sort(),
    findingStates: Array.from(new Set([...left.findings, ...right.findings].map((item) => item.state))).sort(),
    completenessStates: Array.from(new Set([...left.readiness, ...right.readiness].map((item) => item.state))).sort()
  };
}

export function groupEvidenceByStatus(scenario: SyntheticScenario) {
  return scenario.evidence.reduce<Record<string, string[]>>((groups, item) => {
    groups[item.status] = [...(groups[item.status] ?? []), item.title];
    return groups;
  }, {});
}

export function groupFindingsByState(scenario: SyntheticScenario) {
  return scenario.findings.reduce<Record<string, string[]>>((groups, item) => {
    groups[item.state] = [...(groups[item.state] ?? []), item.title];
    return groups;
  }, {});
}
