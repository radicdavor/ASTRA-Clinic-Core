# Program 1 Phase B22 - Snapshot Supersession No-Go Matrix

Status: documentation-only no-go matrix

| Scenario | Allowed later? | Requirement | No-Go boundary |
| --- | --- | --- | --- |
| Physician supersedes snapshot with reason | Yes, future | Permission, reason, audit | Does not mean approval or clearance |
| Nurse supersedes snapshot | Deferred | Explicit governance required | Not default |
| Reception supersedes snapshot | No default | N/A | Reception is operational, not clinical governance |
| AI supersedes snapshot | No | N/A | AI must not finalize history relationships |
| API key supersedes snapshot | No default | Maintainer decision required | Must not bypass human reason |
| Supersede without reason | No | Reason required | Empty reason is invalid |
| Supersede and delete old snapshot | No | Old snapshot remains stored | Delete is forbidden |
| Supersede and edit old payload | No | Payload immutable | Edit is forbidden |
| Supersede and change appointment status | No | N/A | Appointment workflow unchanged |
| Supersede and create Task | No | N/A | Task engine out of scope |
| Supersede and create Outcome Evidence | No | N/A | Snapshot is not outcome |
| Supersede from wrong appointment | No | Same appointment required | Cross-appointment link forbidden |

## Hard No-Go Rules

Future supersession must not:

- delete old snapshot
- edit old copied payload
- hide old snapshot from history
- change appointment status
- create Task
- create Outcome Evidence
- approve procedure
- clear readiness
- override warning
- send patient message
- allow AI/system auto-supersession

## Conditional-Go Rules

Future implementation may proceed only after:

- permission contract is implemented
- required reason is implemented
- audit event is implemented
- appointment ownership validation exists
- regression tests prove old payload remains unchanged
- UI labels remain historical and read-only
