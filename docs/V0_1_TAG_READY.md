# v0.1-pilot Tag Readiness

## Status

Ready for explicit maintainer tag decision.

This document implements the V17 tag readiness note required after the structured pilot completion gate is accepted.

## Evidence Summary

Canonical evidence:

- `docs/pilot_sessions/2026-07-05_human_pilot_01.md`
- `docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md`
- `docs/V0_1_GO_NO_GO_MATRIX.md`
- `docs/ADR/0001-v0-1-pilot-decision.md`
- `docs/releases/V0_1_PILOT_RELEASE_NOTES.md`
- `docs/V23_PILOT_RELEASE_CANDIDATE.md`

Pilot evidence status:

- Structured human pilot answers were provided by the maintainer.
- Tasks 1-12 were answered Yes.
- Real-data confusion observed: No.
- Fiscalization confusion observed: No.
- No P0/P1 blocker was reported.
- One P2 UX finding was reported: action completion feedback was too subtle.
- The P2 UX finding was fixed with global toast feedback for successful create/update/delete actions and visible error feedback for failed mutations.
- V18 patient identity feedback was implemented: optional OIB, patient search/disambiguation for appointment creation, service context and contextual help on critical actions.

Validation status:

- GitHub CI passed after the V18 implementation and readiness documentation updates.
- Frontend typecheck passed.
- Frontend smoke passed.
- Frontend build passed.
- Backend tests passed, including OIB validation/search coverage.
- Fresh PostgreSQL migration replay passed through `0005_patient_oib`.
- Pilot release validation script passed.
- Local Docker frontend/backend services were rebuilt and started.
- V23 release candidate manifest exists and gathers final readiness, CI and human pilot evidence for maintainer tag decision.

## Boundaries

The `v0.1-pilot` tag does not allow:

- real patient data
- real OIB values in demo mode
- real Croatian fiscalization
- certified EMR use
- medical device use
- production deployment without completing the real-data readiness checklist

`REAL_DATA_ALLOWED` must remain false for demo/pilot use.

## Tag Command

Run only after the maintainer explicitly confirms tagging:

```bash
git tag -a v0.1-pilot -m "ASTRA Clinic Core v0.1 pilot"
git push origin v0.1-pilot
```

## Rollback Command

If the tag is created by mistake and has not been used publicly:

```bash
git tag -d v0.1-pilot
git push origin :refs/tags/v0.1-pilot
```

If the tag has already been shared publicly, do not delete it silently. Create a corrective release note and a new patch tag instead.
