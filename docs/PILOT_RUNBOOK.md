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
2. Open patients and create or review a demo patient. If OIB is used, use only an invented demo OIB.
3. If the possible-duplicate warning appears, compare name, birth date, OIB, phone and e-mail before confirming a new patient.
4. Open new appointment and search for the patient by name or OIB.
5. Select the resolved patient from the search result; do not create an appointment from ambiguous free text.
6. Select a service and review the service context card.
7. Open daily dashboard.
8. Select today's date and open the demo appointment.
9. Use quick status actions: arrived, in progress.
10. Open appointment detail.
11. Load material suggestion.
12. Review required fixed, required variable, and optional material labels.
13. Complete appointment with material consumption and verify the confirmation prompt is clear.
14. Verify the appointment status is completed.
15. Verify stock movement appears on appointment detail.
16. Create draft invoice from appointment.
17. Open invoice detail.
18. Issue invoice and verify the confirmation prompt is clear.
19. Show demo fiscalization status and warning.
20. Record payment for the remaining amount and verify the confirmation prompt is clear.
21. Open purchase orders.
22. Receive demo purchase order line and verify the confirmation prompt is clear.
23. Open inventory and verify stock changed.
24. Open audit log or appointment audit timeline and review traceability.
25. Capture feedback in `docs/PILOT_FEEDBACK_TEMPLATE.md`.

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
