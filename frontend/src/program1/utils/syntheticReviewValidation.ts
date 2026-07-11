import { SyntheticScenario } from "../types/syntheticReview";

function requireText(value: string, label: string) {
  if (!value.trim()) {
    throw new Error(`Invalid Program 1 synthetic fixture: ${label} is required.`);
  }
}

function ensureUnique(values: string[], label: string) {
  if (new Set(values).size !== values.length) {
    throw new Error(`Invalid Program 1 synthetic fixture: duplicate ${label}.`);
  }
}

export function validateSyntheticScenarios<T extends SyntheticScenario[]>(scenarios: T): T {
  ensureUnique(scenarios.map((scenario) => scenario.id), "scenario id");

  for (const scenario of scenarios) {
    if (scenario.syntheticOnly !== true) {
      throw new Error(`Invalid Program 1 synthetic fixture: ${scenario.id} is not marked synthetic-only.`);
    }
    if (scenario.provenance.realDataUsed !== false) {
      throw new Error(`Invalid Program 1 synthetic fixture: ${scenario.id} provenance allows real data.`);
    }
    [
      scenario.id,
      scenario.version,
      scenario.title,
      scenario.subjectLabel,
      scenario.summary,
      scenario.reviewQuestion,
      scenario.provenance.sourceReference
    ].forEach((value, index) => requireText(value, `${scenario.id} field ${index + 1}`));

    if (scenario.limitations.length === 0 || scenario.prohibitedInterpretations.length === 0) {
      throw new Error(`Invalid Program 1 synthetic fixture: ${scenario.id} must include limitations and prohibited interpretations.`);
    }

    const evidenceIds = scenario.evidence.map((item) => item.id);
    ensureUnique(evidenceIds, `${scenario.id} evidence id`);
    ensureUnique(scenario.timeline.map((item) => item.id), `${scenario.id} timeline id`);
    ensureUnique(scenario.findings.map((item) => item.id), `${scenario.id} finding id`);
    ensureUnique(scenario.readiness.map((item) => item.id), `${scenario.id} completeness id`);

    for (const item of scenario.evidence) {
      [item.id, item.type, item.title, item.summary, item.sourceLabel].forEach((value) => requireText(value, `${scenario.id} evidence`));
    }
    for (const event of scenario.timeline) {
      [event.id, event.relativeTime, event.category, event.title, event.description].forEach((value) => requireText(value, `${scenario.id} timeline`));
      for (const evidenceId of event.evidenceIds) {
        if (!evidenceIds.includes(evidenceId)) {
          throw new Error(`Invalid Program 1 synthetic fixture: ${scenario.id} timeline reference ${evidenceId} is missing.`);
        }
      }
    }
    for (const finding of scenario.findings) {
      [finding.id, finding.title, finding.description, finding.limitation].forEach((value) => requireText(value, `${scenario.id} finding`));
      for (const evidenceId of finding.evidenceIds) {
        if (!evidenceIds.includes(evidenceId)) {
          throw new Error(`Invalid Program 1 synthetic fixture: ${scenario.id} finding reference ${evidenceId} is missing.`);
        }
      }
    }
  }

  return scenarios;
}
