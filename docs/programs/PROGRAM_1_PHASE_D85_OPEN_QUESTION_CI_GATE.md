# Program 1 Phase D85 - Open Question CI Gate

Status: documented gate

## Required Coverage

The open question safety gate includes:

- `tests/test_clinical_open_questions_contract.py`
- `tests/test_clinical_finding_extraction_contract.py`
- findings lifecycle, persistence and read API tests
- open question endpoint, DB model/table and service absence checks
- full backend pytest suite
- frontend typecheck, build and smoke

## Current CI Expectation

The full backend suite covers the open question contract tests. The frontend smoke script also guards against accidental open question client or UI action labels.

No additional CI dependency or workflow expansion is required in this phase.

## Safety Boundary

The gate verifies passive schema shape and no-go boundaries only. It does not approve runtime open-question creation, persistence, review, tasking, outcome evidence, patient messaging, diagnosis, treatment, production use or real patient data.
