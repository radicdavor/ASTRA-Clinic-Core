# v0.1 Pilot Dry-Run Example

Copy this file for a real pilot run. Do not include real patient data.

## Environment

- Environment: local Docker Compose demo
- Frontend URL: http://localhost:5173
- Backend URL: http://localhost:8000
- Database: local PostgreSQL Docker volume
- Demo seed/reset verified: Yes / No

## Commit

- Commit SHA: `<fill-before-run>`
- Branch: `main`
- Run date/time: `<dd-mm-YYYY HH:mm>`

## Participants

- Facilitator: `<name>`
- Participant roles: reception, physician/nurse, billing, inventory, admin

## Demo Script Steps Completed

| Step | Expected result | Completed | Notes |
| --- | --- | --- | --- |
| Login | Demo admin can log in | Yes / No | |
| Dashboard schedule | Today's schedule is visible | Yes / No | |
| Appointment status updates | Status buttons update the appointment | Yes / No | |
| Material consumption | Appointment can complete and reduce stock | Yes / No | |
| Draft invoice | Draft invoice is created from appointment | Yes / No | |
| Issue invoice | Invoice gets issued with noop fiscalization warning | Yes / No | |
| Payment | Remaining amount can be recorded without overpayment | Yes / No | |
| Purchase receiving | Valid PO line increases stock | Yes / No | |
| Inventory verification | Stock movement is visible | Yes / No | |
| Audit review | Timeline/audit log shows traceability | Yes / No | |

## Failed Steps

- Step:
- What happened:
- Expected behavior:
- Reproduction notes:

## Bugs Found

| Severity | Area | Summary | Issue link |
| --- | --- | --- | --- |
| P0/P1/P2/P3 | | | |

## Known Limitations Confirmed

- Demo data only.
- No real patient data.
- No real Croatian fiscalization.
- Not certified EMR.
- Not certified medical device.

## Go/No-Go

- Next demo decision: Go / No-Go
- Required fixes before next demo:
