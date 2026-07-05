# Human Pilot Facilitator Sheet

Use this one-page sheet to run a closed human pilot with demo data only.

## Pre-Session Setup

- Confirm Docker demo environment is running.
- Confirm frontend opens at http://localhost:5173.
- Confirm backend health at http://localhost:8000/health.
- Run demo seed if needed: `docker compose exec backend python -m app.demo.seed`.
- Keep `docs/PILOT_RUNBOOK.md` open.
- Keep `docs/pilot_sessions/HUMAN_PILOT_REPORT_TEMPLATE.md` ready for notes.

## Safety Warnings

- Do not enter real patient data.
- Do not enter real identifiers, phone numbers, emails or clinical notes.
- No real Croatian fiscalization is implemented.
- Use demo accounts and demo scenarios only.

## Browser/Device Note

- Browser:
- Device:
- Screen size:
- Any extensions or accessibility tools:

## Demo Login

- Admin: `demo.admin@astra.local`
- Physician: `demo.physician@astra.local`
- Reception: `demo.reception@astra.local`
- Inventory: `demo.inventory@astra.local`
- Password: `demo123`

## Participant

- Role: reception / physician / nurse / inventory / billing / admin
- Experience with clinic software: low / medium / high

## Tasks to Ask the Participant

1. Log in.
2. Find today's schedule.
3. Open a demo appointment.
4. Change appointment status.
5. Review suggested materials.
6. Complete the appointment with material consumption.
7. Find the stock movement.
8. Create a draft invoice.
9. Issue the invoice and explain the fiscalization warning.
10. Record payment for the remaining amount.
11. Receive a purchase order line.
12. Open audit log/timeline and explain what changed.

## What to Observe

- Where does the participant hesitate?
- Which labels are unclear?
- Which action feels risky?
- Are status changes understandable?
- Is the material/inventory flow understandable?
- Is the invoice/payment flow understandable?
- Does the participant understand that fiscalization is demo/noop only?
- Does the participant understand that real patient data is not allowed?

## Where to Write Issues

- Record notes in the human pilot report.
- Convert findings into GitHub issues with `.github/ISSUE_TEMPLATE/pilot_feedback.yml`.
- Use labels from `docs/ISSUE_LABELS.md`.

## Stop Conditions

Stop the session if:

- Real patient data is about to be entered.
- Demo banner or real-data warning is missing.
- Permission bypass is suspected.
- Stock, invoice or payment data becomes corrupted.
- Participant cannot complete a core task and there is no workaround.
