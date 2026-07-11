# Program 1 Local Production Readiness Track Phase H8 - Stop Conditions and Deviation Handling Record

Status: documentation-only template. Stop conditions do not authorize execution.

## Stop-Condition Checklist

Immediate stop is required if any of the following occurs or is suspected:

- real data appears
- PHI or PII is suspected
- candidate identity cannot be confirmed
- commit drift is detected
- a network is required
- a network connection is attempted
- a listening port opens
- a server starts
- a database is accessed
- an external API is invoked
- telemetry or analytics is emitted
- persistence occurs outside the approved plan
- export becomes available
- screenshots or printing occur outside the approved plan
- patient-facing functionality appears
- messaging appears
- appointment mutation appears
- clinical writeback appears
- task creation appears
- approval or override appears
- diagnosis appears
- treatment recommendation appears
- triage appears
- patient instruction appears
- evidence is incomplete
- evaluator cannot explain observed behavior
- authorization is expired
- authorization is revoked
- machine custody is uncertain
- scope becomes ambiguous

## Deviation Template

| Field | Placeholder |
| --- | --- |
| Deviation ID | `[DEVIATION_ID]` |
| Date and time | `[DATE_TIME]` |
| Exact commit SHA | `[FULL_COMMIT_SHA]` |
| Evaluator | `[EVALUATOR_PLACEHOLDER]` |
| Custodian | `[CUSTODIAN_PLACEHOLDER]` |
| Reviewer | `[REVIEWER_PLACEHOLDER]` |
| Observed behavior | `[OBSERVED_BEHAVIOR]` |
| Affected boundary | `[AFFECTED_BOUNDARY]` |
| Stop decision | `[STOP_DECISION]` |
| Immediate containment | `[IMMEDIATE_CONTAINMENT]` |
| Real-data involvement | `[REAL_DATA_INVOLVEMENT]` |
| Evidence preserved | `[EVIDENCE_PRESERVED]` |
| Unresolved questions | `[UNRESOLVED_QUESTIONS]` |
| Disposition | `[DISPOSITION]` |
| Reauthorization requirement | `[REAUTHORIZATION_REQUIREMENT]` |

Deviation does not authorize troubleshooting. Failed preflight does not authorize code changes. Remediation requires a separate explicit track. Restart requires a new decision record.

## Reviewer Disposition

`[REVIEWER_DISPOSITION]`
