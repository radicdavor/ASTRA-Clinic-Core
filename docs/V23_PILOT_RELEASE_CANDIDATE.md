# V23 Pilot Release Candidate

## Status

ASTRA Clinic Core is a `v0.1-pilot` release candidate for explicit maintainer decision.

This document does not create the tag. It gathers the release evidence that must be reviewed before the maintainer decides whether to tag `v0.1-pilot`.

## Candidate Scope

The candidate is for closed demo/pilot use with demo data only.

It does not allow:

- real patient data
- real OIB values in demo mode
- real Croatian fiscalization
- production clinical use
- certified EMR use
- medical-device use

The demo/pilot environment must keep `real_data_allowed=false`.

## Required Evidence

Review these files before tagging:

- `docs/ASTRA_ARCHITECTURE_BIBLE.md`
- `docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md`
- `docs/ASTRA_READINESS_MODEL.md`
- `docs/PILOT_RUNBOOK.md`
- `docs/V0_1_GO_NO_GO_MATRIX.md`
- `docs/V0_1_PILOT_RELEASE_CHECKLIST.md`
- `docs/V0_1_TAG_READY.md`
- `docs/releases/V0_1_PILOT_RELEASE_NOTES.md`
- `docs/pilot_sessions/2026-07-05_human_pilot_01.md`
- `docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md`

## Required Validation

Before tag approval, confirm:

- GitHub CI is green on `main`.
- Backend tests pass.
- Frontend typecheck passes.
- Frontend smoke passes.
- Frontend production build passes.
- Pilot release validation passes.
- Docker Compose starts the local demo environment.
- `/api/public-config` reports `real_data_allowed=false`.
- `/readiness` has no unwaived critical blockers.
- Any readiness warnings are reviewed and documented.
- No P0/P1 pilot issue is open.

## Readiness Expectations

Readiness is the pre-demo cockpit, not production or compliance approval.

Expected state for `v0.1-pilot`:

- critical readiness checks: none, unless explicitly waived by maintainer
- fiscalization: warning/review is acceptable only because mode is noop/stub and visibly marked
- human pilot evidence: must remain the release decision source
- API keys: review active keys and deactivate those not needed for demo

## Known Non-Blocking Warnings

These warnings may be acceptable for `v0.1-pilot` if reviewed:

- noop/stub fiscalization
- human pilot evidence reminder after evidence has been reviewed
- low stock or unpaid invoice demo data when intentionally present
- active API keys used only for scoped demo/AI testing

## Blocker Policy

Do not tag if any of these is true:

- GitHub CI fails.
- Backend tests fail.
- Frontend typecheck, smoke or build fails.
- `/api/public-config` allows real data in demo/pilot.
- `/readiness` reports an unwaived critical blocker.
- Any P0/P1 pilot issue is open.
- Users may reasonably believe real patient data or real fiscalization is allowed.

Maintainer waivers must be explicit and documented in the Go/No-Go matrix or release notes.

## Tag Reminder

Tag only after explicit maintainer approval:

```bash
git tag -a v0.1-pilot -m "ASTRA Clinic Core v0.1 pilot"
git push origin v0.1-pilot
```

If a tag is created by mistake and has not been used publicly:

```bash
git tag -d v0.1-pilot
git push origin :refs/tags/v0.1-pilot
```

If the tag has already been shared publicly, do not delete it silently. Create a corrective release note and a new patch tag instead.

