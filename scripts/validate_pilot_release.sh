#!/usr/bin/env sh
set -eu

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

check_file() {
  [ -f "$1" ] || fail "Missing required file: $1"
}

check_dir() {
  [ -d "$1" ] || fail "Missing required directory: $1"
}

check_contains() {
  file="$1"
  text="$2"
  grep -F "$text" "$file" >/dev/null || fail "$file does not mention: $text"
}

check_file "backend/requirements.txt"
check_file "frontend/package.json"
check_file "docs/PILOT_RUNBOOK.md"
check_file "docs/ASTRA_ARCHITECTURE_BIBLE.md"
check_file "docs/ASTRA_DESIGN_SYSTEM.md"
check_file "docs/ASTRA_WORKSPACE_ARCHITECTURE.md"
check_file "docs/ASTRA_READINESS_MODEL.md"
check_file "docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md"
check_file "docs/CODEX_ARCHITECTURE_BIBLE_INSTRUCTIONS.md"
check_file "docs/V19_ARCHITECTURE_BIBLE_COMPLIANCE_GATE.md"
check_file "docs/V19_IMPLEMENTATION_REPORT.md"
check_file "docs/V20_READINESS_COCKPIT.md"
check_file "docs/CODEX_MASTER_PROMPT_V23.md"
check_file "docs/V23_PILOT_RELEASE_CANDIDATE.md"
check_file "docs/ARCHITECTURE_CHANGE_PROPOSAL.md"
check_file "docs/ARCHITECTURE_CHANGE_PROPOSAL_PATIENT_IDENTITY_AND_ACTION_LANGUAGE.md"
check_file "docs/ARCHITECTURE_CHANGE_PROPOSAL_WORKSPACES.md"
check_file "docs/ARCHITECTURE_CHANGE_PROPOSAL_READINESS_MODEL.md"
check_file "docs/ARCHITECTURE_CHANGE_PROPOSAL_OPERATIONAL_EVIDENCE_LOOP.md"
check_file "docs/INVOICE_WORKSPACE_PROPOSAL.md"
check_file "docs/PILOT_FEEDBACK_TEMPLATE.md"
check_file "docs/REAL_DATA_READINESS_CHECKLIST.md"
check_file "docs/V0_1_PILOT_RELEASE_CHECKLIST.md"
check_file "docs/RELEASE_NOTES_TEMPLATE.md"
check_file "docs/releases/V0_1_PILOT_RELEASE_NOTES.md"
check_file "docs/pilot_sessions/V0_1_DRY_RUN_EXAMPLE.md"
check_file "backend/app/demo/seed.py"
check_file "backend/app/demo/reset.py"
check_file "AGENTS.md"
check_file ".github/pull_request_template.md"
check_dir ".github/ISSUE_TEMPLATE"

check_contains "README.md" "Pilot status"
check_contains "README.md" "ASTRA Architecture Bible"
check_contains "README.md" "ASTRA Design System"
check_contains "README.md" "ASTRA Workspace Architecture"
check_contains "README.md" "ASTRA Readiness Model"
check_contains "README.md" "ASTRA Operational Evidence Loop"
check_contains "README.md" "V23 Pilot Release Candidate"
check_contains "AGENTS.md" "docs/ASTRA_ARCHITECTURE_BIBLE.md"
check_contains "AGENTS.md" "docs/ASTRA_DESIGN_SYSTEM.md"
check_contains "docs/V19_ARCHITECTURE_BIBLE_COMPLIANCE_GATE.md" "Architecture Bible"
check_contains "docs/ASTRA_DESIGN_SYSTEM.md" "Action Categories"
check_contains "docs/ASTRA_WORKSPACE_ARCHITECTURE.md" "Patient Workspace"
check_contains "docs/ASTRA_READINESS_MODEL.md" "ready_for_demo"
check_contains "docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md" "Readiness -> Workspace -> Action -> Audit"
check_contains "docs/V19_IMPLEMENTATION_REPORT.md" "possible-duplicates"
check_contains "docs/V20_READINESS_COCKPIT.md" "/api/readiness"
check_contains "docs/CODEX_MASTER_PROMPT_V23.md" "Pilot Release Candidate Sprint"
check_contains "docs/V23_PILOT_RELEASE_CANDIDATE.md" "v0.1-pilot"
check_contains "docs/V23_PILOT_RELEASE_CANDIDATE.md" "real_data_allowed=false"
check_contains "docs/V23_PILOT_RELEASE_CANDIDATE.md" "GitHub CI"
check_contains "docs/V23_PILOT_RELEASE_CANDIDATE.md" "human pilot evidence"
check_contains "docs/V23_PILOT_RELEASE_CANDIDATE.md" "/readiness"
check_contains "docs/INVOICE_WORKSPACE_PROPOSAL.md" "/invoices/:id"
check_contains "frontend/package.json" "\"typecheck\""
check_contains "frontend/package.json" "\"build\""
check_contains "frontend/package.json" "\"smoke\""
check_contains "docs/V0_1_PILOT_RELEASE_CHECKLIST.md" "No P0/P1 pilot issues open"
check_contains "docs/REAL_DATA_READINESS_CHECKLIST.md" "not ready for real patient data"
check_contains "docs/PILOT_RUNBOOK.md" "Go/No-Go"

echo "Pilot release validation passed."
