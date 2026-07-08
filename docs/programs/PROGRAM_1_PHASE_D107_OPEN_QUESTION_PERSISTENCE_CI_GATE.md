# Program 1 Phase D107 - Open Question Persistence CI Gate

Status: documented

## Required Gate

- open question contract tests
- open question persistence tests
- Alembic upgrade through backend suite
- extraction contract tests
- findings lifecycle, persistence and read API tests
- no endpoint/service guard
- full backend suite
- frontend typecheck
- frontend build
- frontend smoke

## Current Coverage

`tests/test_clinical_open_questions_contract.py` covers passive schema and runtime absence boundaries. `tests/test_clinical_open_questions_persistence.py` covers model/table shape, source-linking constraints, status constraints and no workflow side effects.

The frontend smoke script continues to verify no open question client path or UI labels exist.

## CI Workflow Decision

The existing full backend suite and frontend smoke cover the required files. No new dependency or workflow expansion is needed in this phase.

## Safety Boundary

The gate approves only DB foundation checks. It does not approve an endpoint, service, UI, automatic question creation, production use or real patient data.
