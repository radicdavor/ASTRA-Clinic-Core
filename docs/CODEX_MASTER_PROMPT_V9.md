# Codex master prompt v9 — Closed Pilot Execution Sprint

Use this prompt in Codex for the next sprint of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack architect, QA-minded maintainer and pilot-execution lead.

ASTRA Clinic Core has implemented v8. The project is now demo/pilot-ready with demo data only.

Current state includes:

- pilot runbook
- pilot feedback template
- real data readiness checklist
- demo/development banner
- frontend pilot smoke script
- improved appointment material workflow
- improved purchase receiving workflow
- improved invoice issue/payment workflow
- improved API key scope UX
- audit timeline
- data-only module loader
- demo seed/reset tooling

The next sprint is:

**Closed Pilot Execution Sprint**

Main goal:

Run ASTRA through a controlled pilot process with demo data, convert feedback into actionable issues, and prepare a v0.1 pilot release. Do not expand broad feature scope yet.

## Non-negotiable rules

- Do not use real patient data.
- Do not implement real Croatian fiscalization yet.
- Do not start broad new clinical modules yet.
- Do not add AI automation that can mutate data beyond existing scoped API protections.
- Focus on controlled pilot execution and hardening.

## Phase 1 — Add module loader tests

The data-only module loader exists. Add tests now.

Required tests:

1. loading one module creates a Module record
2. loading the same module twice does not create duplicates
3. loading services creates Service records by code
4. loading services twice updates existing Service records without duplication
5. loading material templates creates templates by service code + item SKU
6. missing inventory item for material template is skipped without crash
7. invalid module manifest fails with clear validation error
8. loader does not execute arbitrary Python code

Suggested file:

```text
backend/tests/test_module_manifest_loader.py
```

Acceptance criteria:

- Module loader is idempotent and tested.
- Module config can be safely used for future Gastro/Endoscopy modules.

## Phase 2 — Add pilot feedback issue template

Add GitHub issue template:

```text
.github/ISSUE_TEMPLATE/pilot_feedback.yml
```

Fields:

- participant role
- demo scenario
- task attempted
- completed yes/no
- what worked
- what was confusing
- blocker severity
- screenshot/log link optional
- suggested improvement
- real-data readiness concern yes/no

Acceptance criteria:

- Pilot feedback can be entered as structured GitHub issues.

## Phase 3 — Add public runtime config endpoint

Frontend should not rely only on Vite build-time env for demo/production mode.

Add backend endpoint:

```text
GET /api/public-config
```

Return:

```json
{
  "app_name": "ASTRA Clinic Core",
  "app_env": "development",
  "demo_mode": true,
  "real_data_allowed": false,
  "fiscalization_mode": "noop"
}
```

Rules:

- `real_data_allowed` defaults to false.
- In development/demo, frontend banner must show.
- In production, backend safety checks still apply.
- Do not expose secrets.

Frontend:

- AppShell reads public config.
- Demo banner uses backend config, with Vite env as fallback only.

Acceptance criteria:

- Demo/real-data warning is driven by backend truth.

## Phase 4 — Real-data guardrails

Add explicit real-data guardrails.

Backend config:

- `DEMO_MODE=true|false`
- `REAL_DATA_ALLOWED=false|true`

Behavior:

- Default: demo_mode true, real_data_allowed false.
- If real_data_allowed false, public config says so.
- If APP_ENV=production and DEMO_MODE=true, log/return visible warning in public config.
- Do not hard-block all patient creation yet, but add optional warning header:
  - `X-ASTRA-REAL-DATA-ALLOWED: false`

Optional but useful:

- Add patient create warning if email/name looks non-demo only if safe and not annoying.

Acceptance criteria:

- It is visually and technically obvious whether real data is allowed.

## Phase 5 — Strengthen frontend pilot smoke

Current smoke is static string checking. Improve it without overcomplicating.

Option A: Playwright minimal smoke.

Test:

- app loads
- login page renders
- protected routes redirect without token
- dashboard shell renders after mock token if feasible

Option B: Keep static smoke but add more checks:

- AppointmentDetail contains material validation strings
- PurchaseOrders contains over-receive validation string
- Invoices contains remaining payment logic string
- ApiKeys contains dangerous scope confirmation string
- AppShell reads public config or demo banner text

Acceptance criteria:

- Frontend smoke catches missing key operational screens.

## Phase 6 — Runbook-driven QA artifacts

Add folder:

```text
docs/pilot_sessions/
```

Add sample session file:

```text
docs/pilot_sessions/README.md
```

Include:

- how to record each pilot session
- link to feedback template
- severity definitions
- how to convert findings into GitHub issues

Severity definitions:

- P0: data corruption/security issue/demo cannot proceed
- P1: core workflow blocked
- P2: confusing but workaround exists
- P3: cosmetic or minor wording issue

Acceptance criteria:

- Pilot feedback has an operational home.

## Phase 7 — v0.1 pilot release checklist

Create:

```text
docs/V0_1_PILOT_RELEASE_CHECKLIST.md
```

Checklist:

- CI green
- backend tests green
- frontend typecheck/build green
- pilot demo smoke green
- demo seed/reset verified
- pilot runbook followed end-to-end
- no P0/P1 pilot issues open
- real data readiness checklist reviewed and still blocks real data
- backup/restore docs reviewed
- fiscalization marked noop/stub
- demo banner visible
- API keys reviewed/deactivated after demo

Acceptance criteria:

- Project can tag a v0.1-pilot release only after checklist passes.

## Phase 8 — Add changelog discipline for pilot releases

Update `CHANGELOG.md` with sections:

- Added
- Changed
- Fixed
- Known limitations
- Real-data status

Add current known limitations:

- demo data only
- no real Croatian fiscalization
- not certified EMR
- no real patient data allowed
- module loader basic
- frontend e2e limited

Acceptance criteria:

- Changelog communicates risk and maturity honestly.

## Phase 9 — Optional: issue labels documentation

Create:

```text
docs/ISSUE_LABELS.md
```

Recommended labels:

- pilot:P0
- pilot:P1
- pilot:P2
- pilot:P3
- area:frontend
- area:backend
- area:inventory
- area:billing
- area:appointments
- area:audit
- area:security
- area:docs
- real-data-blocker

Acceptance criteria:

- Pilot issues can be triaged consistently.

## Phase 10 — Do one controlled pilot dry-run checklist

Add document:

```text
docs/PILOT_DRY_RUN_REPORT_TEMPLATE.md
```

Sections:

- environment
- commit SHA
- participants
- date/time
- demo script steps completed
- failed steps
- bugs found
- screenshots/logs
- P0/P1/P2/P3 summary
- go/no-go for next demo

Acceptance criteria:

- Each pilot run can produce an auditable report.

## Suggested commit sequence

1. `test: cover data-only module manifest loader`
2. `chore: add pilot feedback issue template`
3. `feat: add public runtime config endpoint`
4. `feat: drive demo banner from public config`
5. `chore: add real data guardrail config`
6. `test: strengthen frontend pilot smoke`
7. `docs: add pilot session triage workflow`
8. `docs: add v0.1 pilot release checklist`
9. `docs: update changelog with pilot limitations`
10. `docs: add pilot dry run report template`

## Definition of done

Closed Pilot Execution Sprint is done when:

- module loader tests pass
- public config endpoint exists and exposes demo/real-data flags
- demo banner uses backend public config
- real-data guardrails are visible
- pilot feedback can be entered as structured GitHub issue
- pilot session docs exist
- v0.1 pilot release checklist exists
- changelog clearly states real-data status and limitations
- pilot dry-run report template exists

After this sprint, run the actual closed pilot using demo data and collect feedback. Do not expand the clinical module scope until P0/P1 pilot feedback is resolved.
