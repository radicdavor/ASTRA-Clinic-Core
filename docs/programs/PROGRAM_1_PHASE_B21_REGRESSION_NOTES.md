# Program 1 Phase B21 - Regression Notes

Status: canonical disclaimer and immutability hardening

## Implemented

B21 hardens Clinical Readiness Snapshot safety before supersession.

Implemented:

- canonical disclaimer rules document
- UI displays stored server disclaimer directly
- removed ad-hoc frontend disclaimer rewriting
- regression coverage for missing update/delete endpoints
- regression coverage proving detail/history reads do not mutate payload
- regression coverage proving capture creates new rows rather than updating existing payload
- regression coverage proving supersession route is not implemented yet

## Behavioral changes

Frontend now displays stored snapshot disclaimer text as provided by backend.

Read endpoints remain read-only.

No update/delete/supersession behavior was added.

## Safety properties

B21 preserves:

- snapshot payload is treated as immutable
- UI does not rewrite server disclaimer dynamically
- no update endpoint
- no delete endpoint
- no supersession endpoint
- no edit/delete/supersession UI
- no approval
- no clearance
- no override
- no Outcome Evidence
- no Task engine
- no appointment status change

## Not implemented

B21 did not implement:

- supersession endpoint
- supersession UI
- edit snapshot
- delete snapshot
- approval
- clearance
- override
- Outcome Evidence
- Task engine
- appointment status change

## Remaining risks

- immutability is still enforced by route/service discipline, not database triggers
- supersession behavior is not yet contracted in enough detail
- canonical Croatian-only display field is deferred

## Recommended next task

`Program 1 Phase B22 - Snapshot Supersession Contract`
