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
2. Open daily dashboard.
3. Select today's date and open the demo appointment.
4. Use quick status actions: arrived, in progress.
5. Open appointment detail.
6. Load material suggestion.
7. Review required fixed, required variable, and optional material labels.
8. Complete appointment with material consumption.
9. Verify the appointment status is completed.
10. Verify stock movement appears on appointment detail.
11. Create draft invoice from appointment.
12. Open invoice detail.
13. Issue invoice.
14. Show demo fiscalization status and warning.
15. Record payment for the remaining amount.
16. Open purchase orders.
17. Receive demo purchase order line.
18. Open inventory and verify stock changed.
19. Open audit log or appointment audit timeline and review traceability.
20. Capture feedback in `docs/PILOT_FEEDBACK_TEMPLATE.md`.

## Expected Outcomes

- Material consumption reduces stock.
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
- Frontend browser e2e automation is intentionally deferred for the MVP; `npm run smoke` provides a lightweight route and screen guard.

## Fallback

If the pilot state becomes confusing, reset demo data and repeat only the failed step:

```bash
docker compose exec backend python -m app.demo.reset
docker compose exec backend python -m app.demo.seed
```

Do not use the reset command against production data.

## Backup Reminder

Before any non-demo pilot, review `docs/BACKUP_RESTORE.md` and test restore.
