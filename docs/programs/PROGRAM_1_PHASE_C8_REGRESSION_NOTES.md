# Program 1 Phase C8 - Regression Notes

Status: advisory signal safety regression guard

## Implemented

C8 is covered by backend advisory signal tests.

Regression guard proves:

- advisory signal serializes with safe fields only
- `is_decision` remains false
- decision semantics are rejected
- forbidden fields are absent
- unsafe severity/category values are rejected

## Forbidden Semantics Guarded

Guarded absence:

- approved
- cleared
- clearance
- override
- outcome evidence
- task created
- patient ready
- procedure approved

## Not Implemented

C8 did not implement:

- endpoint
- DB model
- UI surface
- workflow enforcement

## Tests Run

- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_advisory_signal.py`

## Recommended Next Task

`Program 1 Phase C9 - Enforcement Permission Model Design`
