import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = resolve(frontendRoot, "..");

const requiredFiles = [
  "frontend/src/program1/pages/SyntheticReviewWorkspace.tsx",
  "frontend/src/program1/pages/SyntheticEvaluationRunner.tsx",
  "frontend/src/program1/data/syntheticScenarios.ts",
  "frontend/src/program1/data/syntheticEvaluation.ts",
  "frontend/src/program1/types/syntheticEvaluation.ts",
  "docs/programs/PROGRAM_1_SYNTHETIC_READ_ONLY_UI_EVALUATION_TRACK_PHASE_C_PARTICIPANT_ELIGIBILITY_AND_CONSENT_RECORD.md",
  "docs/programs/PROGRAM_1_SYNTHETIC_READ_ONLY_UI_EVALUATION_TRACK_PHASE_C_MODERATOR_RUNBOOK.md",
  "docs/programs/PROGRAM_1_SYNTHETIC_READ_ONLY_UI_EVALUATION_TRACK_PHASE_C_SYNTHETIC_TASK_SCRIPT.md",
  "docs/programs/PROGRAM_1_SYNTHETIC_READ_ONLY_UI_EVALUATION_TRACK_PHASE_C_OBSERVATION_AND_SCORING_FORM.md",
  "docs/programs/PROGRAM_1_SYNTHETIC_READ_ONLY_UI_EVALUATION_TRACK_PHASE_C_STOP_CONDITION_AND_DEVIATION_PROTOCOL.md",
  "docs/programs/PROGRAM_1_SYNTHETIC_READ_ONLY_UI_EVALUATION_TRACK_PHASE_C_EVIDENCE_AND_DECISION_PACKET.md",
  "docs/programs/PROGRAM_1_SYNTHETIC_READ_ONLY_UI_EVALUATION_TRACK_PHASE_D_FINAL_STATUS_MATRIX_AND_CLOSURE.md"
];

const runnerFiles = [
  "frontend/src/program1/pages/SyntheticEvaluationRunner.tsx",
  "frontend/src/program1/data/syntheticEvaluation.ts",
  "frontend/src/program1/types/syntheticEvaluation.ts",
  "frontend/src/program1/components/SyntheticEvaluationBoundary.tsx",
  "frontend/src/program1/components/SyntheticEvaluationPreflight.tsx",
  "frontend/src/program1/components/SyntheticEvaluationTaskList.tsx"
];

const forbiddenPrimitives = [
  "fetch(", "axios", "useApi", "localStorage", "sessionStorage", "indexedDB", "document.cookie",
  "navigator.clipboard", "window.print", "showSaveFilePicker", "createObjectURL", "WebSocket",
  "EventSource", "sendBeacon", "download=", "dangerouslySetInnerHTML"
];

function read(relativePath) {
  return readFileSync(resolve(repositoryRoot, relativePath), "utf8");
}

function git(...args) {
  return execFileSync("git", args, { cwd: repositoryRoot, encoding: "utf8" }).trim();
}

const checks = [];
function check(id, pass, detail) {
  checks.push({ id, pass, detail });
}

for (const file of requiredFiles) {
  check(`required:${file}`, existsSync(resolve(repositoryRoot, file)), file);
}

const routes = read("frontend/src/routes/AppRoutes.tsx");
const shell = read("frontend/src/components/AppShell.tsx");
const evaluationData = read("frontend/src/program1/data/syntheticEvaluation.ts");
const preflightSource = evaluationData.split("export const syntheticEvaluationTasks")[0];

check("route:review", routes.includes('/program1/synthetic-review'), "synthetic review route");
check("route:evaluation", routes.includes('/program1/synthetic-evaluation'), "evaluation runner route");
check("navigation:evaluation", shell.includes("Program 1 Evaluacija"), "evaluation navigation label");
check("preflight:count", (preflightSource.match(/\{ id:/g) ?? []).length === 6, "six preflight items");
check("tasks:count", (evaluationData.match(/order:\s*\d+/g) ?? []).length === 8, "eight ordered tasks");
check("task:keyboard", evaluationData.includes('id: "keyboard"'), "keyboard-only task");
check("safety:no-real-cases", evaluationData.includes("stvarne pacijente") || evaluationData.includes("stvarnih pacijenata"), "real-data prohibition");

for (const file of runnerFiles) {
  const content = read(file);
  for (const primitive of forbiddenPrimitives) {
    check(`forbidden:${file}:${primitive}`, !content.includes(primitive), `absence of ${primitive}`);
  }
}

const commitSha = git("rev-parse", "HEAD");
const worktreeStatus = git("status", "--porcelain");
check("candidate:full-sha", /^[0-9a-f]{40}$/.test(commitSha), commitSha);
check("candidate:clean-worktree", worktreeStatus.length === 0, worktreeStatus || "clean");

const failed = checks.filter((item) => !item.pass);
const report = {
  candidate: "Program 1 Local Synthetic Evaluation Session Candidate",
  commit_sha: commitSha,
  generated_at: new Date().toISOString(),
  scope: "local-only/synthetic-only/read-only/transient-state",
  checks_total: checks.length,
  checks_passed: checks.length - failed.length,
  readiness: failed.length === 0 ? "READY FOR SEPARATELY AUTHORIZED EXTERNAL SESSION" : "NOT READY",
  failed_checks: failed,
  prohibited_authorizations: ["real data", "clinical use", "production", "deployment", "go-live"]
};

console.log(JSON.stringify(report, null, 2));
if (failed.length > 0) process.exitCode = 1;
