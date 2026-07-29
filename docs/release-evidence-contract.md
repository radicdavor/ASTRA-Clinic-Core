# Release Evidence Contract

## Purpose

ASTRA uses one machine-readable release-evidence manifest to prevent code merge
readiness from being confused with deployment, production, or real-patient-data
authorization.

The manifest is evidence, not authorization. It never makes a medical decision,
changes application data, deploys software, rotates credentials, or seals a
Codex Security review.

## Canonical producer

`scripts/release_evidence.py`

The producer runs only after the backend, frontend, DB-backed E2E, and
remediation-evidence producers succeed. It consumes their exact-SHA execution
records and writes:

- `release-evidence.json`
- `release-evidence.json.sha256`

The validator is deterministic and has no network dependency.

## Checkout identity

The workflow never relies on the implicit pull-request merge checkout:

- `push` checks out exactly `github.sha`
- `pull_request` checks out exactly `github.event.pull_request.head.sha`

Every job calculates `git rev-parse HEAD` after checkout. The
`verify-checkout` command compares that value with the canonical SHA for the
event and fails before evidence production on a missing or mismatched value.
The verified checkout SHA is the manifest `source_sha` and the source SHA used
by every remediation evidence record. No separate declared head SHA can
override the commit that was actually tested.

## Required identity

Every manifest binds:

- full source Git SHA, meaning the commit actually checked out and tested
- GitHub workflow run ID
- workflow name and event
- every producer job result
- generation timestamp and freshness
- canonical artifact hash and file SHA-256

Evidence from another SHA, run, failed producer, future timestamp, or stale
timestamp is rejected.

## Canonical producers

The required producer mapping is a closed, case-sensitive set:

- `backend = success`
- `frontend = success`
- `e2e-db = success`

Missing, additional, duplicated, case-variant, whitespace-variant, or
non-success producer entries are rejected. Remediation behaviour records are
evidence inputs, not additional canonical producer names.

## Technical evidence

The current contract records:

- executed remediation behaviour units
- coverage dimensions
- execution-evidence record count
- executed target test-ID count
- skipped target-test count
- expected and observed Alembic head
- recovery evidence status
- unresolved-finding status
- review status
- formal security limitation
- human-usability status
- credential-rotation status
- dependency issue status
- deployment/proxy validation status

The test-count scope is explicitly `remediation_execution_evidence`; it must not
be presented as the total count of every test in the workflow.

## Readiness separation

The manifest always exposes four independent decisions:

1. `code_merge`
2. `deployment`
3. `production`
4. `real_patient_data`

Passing CI may complete technical execution evidence. It does not grant any of
the four authorizations. Review and owner decisions remain explicit inputs.

The CI-generated manifest therefore records:

- code merge: evidence complete, review and owner decision required
- deployment: blocked
- production: blocked
- real patient data: blocked

These four keys and values form the complete readiness mapping for schema
version 1:

- `code_merge = evidence_complete_review_and_owner_decision_required`
- `deployment = blocked`
- `production = blocked`
- `real_patient_data = blocked`

The validator compares the complete mapping, including types and values.
Unknown keys, missing keys, alternate casing, booleans, nulls, empty strings,
and positive readiness claims are rejected even when ordinary SHA-256 fields
have been recomputed. CI cannot emit a positive readiness or authorization
claim; such a future state requires a versioned contract with corresponding
authoritative evidence.

## Formal security limitation

Until the platform incident is resolved, the only valid value is:

`formal_codex_security_closure = unavailable_due_to_platform_incident`

The manifest must also state:

- `sealed = false`
- `manual_sealing_used = false`

The validator rejects a claim of formal approval or sealing.

## Documentation truth report

`truth-report` checks structured claims in supplied Markdown documents:

- `CURRENT_HEAD: <40-character SHA>`
- `MAIN HEAD: <40-character SHA>`
- `PR #<number> HEAD: <40-character SHA>`
- `ALEMBIC_HEAD: <revision>`
- `ALEMBIC HEAD: <revision>`
- `MIGRATION HEAD: <revision>`
- `UNRESOLVED_FINDINGS: <count>`
- any `FORMAL ... SECURITY CLOSURE: APPROVED` claim

Historical prose and arbitrary SHA references are intentionally not treated as
current-state claims. This avoids rewriting historical reports while making
release-authority assertions machine-checkable.

## Operator finalization

CI cannot infer GitHub review state, owner acceptance, deployment topology,
credential rotation, or human-usability completion. Those fields remain
`not_supplied`, `pending`, or `not_performed` until an authorized release process
provides evidence.

No production or real-patient-data authorization is granted by this contract.
