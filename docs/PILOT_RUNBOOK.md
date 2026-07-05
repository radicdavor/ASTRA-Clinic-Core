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

1. Log in as demo admin.
2. Open daily dashboard.
3. Open today's demo appointment.
4. Load material suggestion.
5. Complete appointment with material consumption.
6. Verify the appointment status is completed.
7. Verify stock movement appears on appointment detail.
8. Create draft invoice from appointment.
9. Open invoice detail.
10. Issue invoice.
11. Show Noop fiscalization status and warning.
12. Record payment for the remaining amount.
13. Open purchase orders.
14. Receive demo purchase order line.
15. Open inventory and verify stock changed.
16. Open audit log or appointment audit timeline and review traceability.

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

## Backup Reminder

Before any non-demo pilot, review `docs/BACKUP_RESTORE.md` and test restore.
