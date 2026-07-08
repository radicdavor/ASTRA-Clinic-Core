# Program 1 Pilot Demo RC1 Manifest

Release candidate name: `program-1-pilot-demo-rc1`

HEAD commit SHA: `64216216d36f8de05ac7172beb7ceaa76745f267`

## Included Modules

- B: readiness snapshots and snapshot governance
- C: acknowledgments and human review signal governance
- D: findings, extraction contracts, open questions and read surfaces
- E: review workflow foundation
- F: Clinical Evidence Timeline foundation
- G: Clinical Evidence Timeline GET-only read API
- H: Clinical Evidence Timeline read-only workspace UI
- I: production governance consolidation
- J: pilot demo release candidate packaging

## Demo-Only Scope

This release candidate is for a closed demo/pilot with synthetic demo data only.

It is not production approval and it is not real patient data approval.

## Key Capabilities

- readiness snapshots
- acknowledgments
- findings read surface
- open questions read API
- timeline read API
- timeline workspace UI
- governance docs
- pilot demo release docs

## Excluded Capabilities

- no write workflows
- no Task engine
- no Outcome Evidence
- no patient messaging
- no automatic diagnosis/treatment
- no approval/clearance/override
- no production approval
- no real-data approval

## Latest Validation

Last validation for J0-J20:

- `git diff --check`: passed
- `python -m py_compile app/main.py app/models/domain.py app/api/routes/appointments.py app/api/routes/patients.py app/services/clinical_readiness_snapshots.py app/services/clinical_readiness_acknowledgments.py app/services/clinical_evidence_timeline.py`: passed
- `docker compose build backend`: passed
- `docker compose run --rm --entrypoint alembic -e PYTHONPATH=/app backend upgrade head`: passed
- targeted backend suites: passed
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend`: `412 passed, 9 skipped`
- `cd frontend && npm run typecheck`: passed
- `cd frontend && npm run build`: passed
- `cd frontend && npm run smoke`: passed

## Push/Tag Status

At manifest creation:

- local `main` is ahead of `origin/main` by 3 commits
- `origin/main` points to `44609013005750baec3e59e5185c273db1025977`
- local HEAD points to `64216216d36f8de05ac7172beb7ceaa76745f267`
- tag `program-1-pilot-demo-rc1` has not been created
- branch push has not been performed for J0-J20
- tag push has not been performed

