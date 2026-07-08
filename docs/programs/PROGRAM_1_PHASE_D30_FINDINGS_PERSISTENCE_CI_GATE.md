# Program 1 Phase D30 - Findings Persistence CI Gate

Status: CI gate documented

## Required Gate

The findings persistence gate must include:

- `tests/test_clinical_findings_lifecycle.py`
- `tests/test_clinical_findings_persistence.py`
- snapshot tests
- advisory signal tests
- acknowledgment tests
- full backend pytest suite
- frontend typecheck, build and smoke checks

## Covered Risks

- unsafe lifecycle vocabulary
- forbidden diagnosis/treatment/approval/clearance fields
- missing source-linking constraints
- accidental findings endpoint or service
- accidental Task, Outcome Evidence or patient messaging coupling

## Runtime Boundary

CI verifies DB foundation behavior only. It does not approve a findings endpoint, service, UI or production deployment.

