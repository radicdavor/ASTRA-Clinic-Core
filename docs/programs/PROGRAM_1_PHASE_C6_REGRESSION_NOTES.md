# Program 1 Phase C6 - Regression Notes

Status: advisory signal backend type prototype

## Implemented

- `ClinicalReadinessAdvisorySignal` Pydantic schema
- no endpoint
- no DB model
- no service side effect
- serialization shape tests

## Safety

The schema is explicitly non-decision:

- `is_decision` must be false
- forbidden fields are absent
- unsafe severity/category values are rejected

## Tests Run

Targeted advisory schema tests are run as part of the C8 guard and final gate.

## Recommended Next Task

`Program 1 Phase C7 - Advisory Signal Read-Only Preview Mapping Design`
