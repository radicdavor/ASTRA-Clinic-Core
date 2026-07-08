# Program 1 Phase D97 - Open Question Persistence CI Gate

Status: documented gate

## Required Checks

- open question contract tests
- extraction contract tests
- findings lifecycle tests
- findings persistence tests
- findings read API tests
- open question endpoint/service/model absence guard
- full backend suite
- frontend typecheck
- frontend build
- frontend smoke

## Current Coverage

`tests/test_clinical_open_questions_contract.py` verifies passive schema safety and absence of runtime route, DB model/table and service. `frontend/scripts/pilot-smoke.mjs` verifies absence of open question client methods, `/open-questions` paths and UI labels.

The full backend suite and frontend smoke are sufficient for this phase. No CI workflow change is required.

## Safety Boundary

This CI gate proves persistence is still not implemented. It does not approve an ORM model, migration, endpoint, service, UI, automatic question creation, production use or real patient data.
