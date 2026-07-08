# Program 1 Phase D35 - Findings Read Permission Boundary

Status: permission boundary

## Permission Proposal

Future read-only findings access uses:

`clinical_findings.read`

No write permission is introduced in this phase.

## Demo/Pilot Access

Recommended demo/pilot access:

- admin: allowed
- physician: allowed
- nurse: not by default
- receptionist: not by default
- API key: denied by default
- AI agent: denied by default
- system job: denied by default

## Boundary

Read permission only allows viewing source-linked finding rows.

It does not imply:

- review authority
- diagnosis authority
- treatment authority
- approval
- clearance
- override
- Task creation
- Outcome Evidence creation
- patient messaging

## Runtime Note

If a GET prototype is added, seeding `clinical_findings.read` is acceptable only as a read-only permission. No `clinical_findings.write` permission may be seeded.

