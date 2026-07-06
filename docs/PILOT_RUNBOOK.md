# Pilot Runbook

ASTRA Clinic Core pilot is for demo data only. Do not enter real patient data.

## Start Local Demo

```bash
docker compose up --build
docker compose exec backend python -m app.demo.seed
```

Open:

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

Demo login:

- Admin: `demo.admin@astra.local`
- Physician: `demo.physician@astra.local`
- Reception: `demo.reception@astra.local`
- Inventory: `demo.inventory@astra.local`
- Password: `demo123`

## Reset Demo Data

```bash
docker compose exec backend python -m app.demo.reset
docker compose exec backend python -m app.demo.seed
```

Reset refuses to run when `APP_ENV=production`.

## Demo Script

Recommended duration: 30 to 45 minutes.

Recommended roles:

- Reception: dashboard, patient lookup, appointment status.
- Physician or nurse: appointment detail and material consumption.
- Billing: invoice issue and payment.
- Inventory or procurement: purchase order receiving.
- Admin: audit log and API key review.

Steps:

1. Log in as demo admin.
2. Open `/readiness`.
3. Confirm there are no critical blockers.
4. Review warnings and open linked screens for low stock, unpaid invoices, API keys, audit or other readiness issues.
5. Continue only after warnings are understood or explicitly accepted for demo.
6. Open patients and enter a Patient Workspace from the patient list.
7. Create or review a demo patient. If OIB is used, use only an invented demo OIB.
8. If the possible-duplicate warning appears, compare name, birth date, OIB, phone and e-mail before confirming a new patient.
9. From Patient Workspace, review appointments, invoices and audit context.
10. Create a new appointment from Patient Workspace or open new appointment and search for the patient by name or OIB.
11. Select the resolved patient from the search result; do not create an appointment from ambiguous free text.
12. Select a service and review the service context card.
13. Open daily dashboard.
14. Select today's date and open the demo appointment.
15. Use quick status actions: arrived, in progress.
16. Open appointment detail.
17. Confirm the appointment screen links back to Patient Workspace.
18. Load material suggestion.
19. Review required fixed, required variable, and optional material labels.
20. Complete appointment with material consumption and verify the confirmation prompt is clear.
21. Verify the appointment status is completed.
22. Verify stock movement appears on appointment detail.
23. Create draft invoice from appointment.
24. Open invoice detail.
25. Issue invoice and verify the confirmation prompt is clear.
26. Show demo fiscalization status and warning.
27. Record payment for the remaining amount and verify the confirmation prompt is clear.
28. Open purchase orders.
29. Receive demo purchase order line and verify the confirmation prompt is clear.
30. Open inventory and verify stock changed.
31. Open audit log or appointment audit timeline and review traceability.
32. Capture feedback in `docs/PILOT_FEEDBACK_TEMPLATE.md`.

## Expected Outcomes

- Material consumption reduces stock.
- Appointment creation requires selecting a resolved patient from search results.
- Patient creation warns about possible duplicates when identity data overlaps.
- Critical workflow actions use contextual help and confirmation.
- Patient OIB is optional and demo-only unless real-data readiness is approved.
- Invoice receives an official number after issue.
- Fiscalization provider is `noop`.
- Payment status updates after payment.
- Purchase receive increases inventory.
- Audit log contains user/API traceability.

## Known Limitations

- No real Croatian fiscalization is implemented.
- System is not a certified EMR.
- System is not a certified medical device.
- Demo data is not suitable for real patients.
- Real OIB values must not be entered in demo mode.
- Frontend browser e2e automation is intentionally deferred for the MVP; `npm run smoke` provides a lightweight route and screen guard.

## Fallback

If the pilot state becomes confusing, reset demo data and repeat only the failed step:

```bash
docker compose exec backend python -m app.demo.reset
docker compose exec backend python -m app.demo.seed
```

Do not use the reset command against production data.

## Go/No-Go

Go if:

- No P0/P1 issues are open.
- Demo data only was used.
- Fiscalization is clearly shown as noop/stub.
- Audit trail is visible for the completed workflow.
- Material, inventory and billing workflows completed successfully.
- Demo banner and real-data warning are visible.

No-Go if:

- Any data corruption appears.
- Any permission bypass appears.
- Demo banner is missing.
- Invoice/payment workflow is blocked.
- Stock movement does not match material consumption or purchase receiving.
- Participants are confused about whether real patient data is allowed.

## Backup Reminder

Before any non-demo pilot, review `docs/BACKUP_RESTORE.md` and test restore.
