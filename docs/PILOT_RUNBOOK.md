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
9. From Patient Workspace, review the Summary tab first: known problems, procedures, pathology, laboratory, imaging, therapy, open questions and latest recommendations.
10. Open at least one source badge and confirm it opens the original Clinical Document.
11. Open `/clinical-documents` and review documents awaiting physician review.
12. Open a document detail page, run AI extraction placeholder if needed, then confirm or reject the proposed summary.
13. Return to Patient Workspace and confirm reviewed document knowledge appears with source links.
14. Review appointments, invoices and audit context.
15. Create a new appointment from Patient Workspace or open new appointment and search for the patient by name or OIB.
16. Select the resolved patient from the search result; do not create an appointment from ambiguous free text.
17. Leave `Bez epizode` unless intentionally testing legacy/deferred Episode Engine compatibility.
18. Select a service and review the service context card.
19. Open daily dashboard.
20. Select today's date and open the demo appointment.
21. Use quick status actions: arrived, in progress.
22. Open appointment detail.
23. Confirm the appointment screen links back to Patient Workspace.
24. Load material suggestion.
25. Review required fixed, required variable, and optional material labels.
26. Complete appointment with material consumption and verify the confirmation prompt is clear.
27. Verify the appointment status is completed.
28. Verify stock movement appears on appointment detail.
29. Create draft invoice from appointment.
30. Open invoice detail.
31. Issue invoice and verify the confirmation prompt is clear.
32. Show demo fiscalization status and warning.
33. Record payment for the remaining amount and verify the confirmation prompt is clear.
34. Open purchase orders.
35. Receive demo purchase order line and verify the confirmation prompt is clear.
36. Open inventory and verify stock changed.
37. Open audit log or appointment audit timeline and review traceability.
38. Return to `/readiness` and review whether warnings changed or remain acceptable.
39. Capture feedback in `docs/PILOT_FEEDBACK_TEMPLATE.md`.

## Expected Outcomes

- Material consumption reduces stock.
- Appointment creation requires selecting a resolved patient from search results.
- Patient creation warns about possible duplicates when identity data overlaps.
- Patient Workspace shows source-linked clinical knowledge first.
- Clinical documents awaiting review are visible and do not become official knowledge until reviewed.
- Appointment may optionally link to an existing deferred episode, but appointments must not require episodes.
- Critical workflow actions use contextual help and confirmation.
- Patient OIB is optional and demo-only unless real-data readiness is approved.
- Invoice receives an official number after issue.
- Fiscalization provider is `noop`.
- Payment status updates after payment.
- Purchase receive increases inventory.
- Audit log contains user/API traceability.
- Readiness cockpit can link from warnings to operational screens.
- After the workflow, readiness and audit can be reviewed as release evidence.

## Known Limitations

- No real Croatian fiscalization is implemented.
- System is not a certified EMR.
- System is not a certified medical device.
- Demo data is not suitable for real patients.
- Real OIB values must not be entered in demo mode.
- Frontend browser e2e automation is intentionally deferred for the MVP; `npm run smoke` provides a lightweight route and screen guard.
- Episode Engine is experimental/deferred and hidden from primary navigation.
- OCR is a placeholder; no real OCR engine is implemented.
- AI extraction is a placeholder; no real AI provider is integrated.

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
