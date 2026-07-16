# Phase E — Narrow end-to-end synthetic pilot runbook and failure controls

This runbook prepares one separately authorized synthetic session. It does not authorize execution with real data.

## Included path

Manual/pre-existing appointment → local document upload → source review → timeline → local AI draft summary when enabled → arrival → check-in → encounter → consumables → invoice → payment → closure.

Excluded: public web intake, live AI secretary/mailbox/scanner/OCR/SMS/e-mail, fiscalization, payment terminal, EHR/EMR, real patient data and production.

## Setup and start checklist

1. Record commit, date, evaluator and environment; confirm `main` matches the authorized candidate.
2. Confirm `APP_ENV=development`, `DEMO_MODE=true`, `REAL_DATA_ALLOWED=false`, `FISCALIZATION_MODE=noop`, and `AI_DIAGNOSIS_SUGGESTIONS_ENABLED=false`.
3. Start PostgreSQL/backend/frontend; require healthy database, `/health` 200, demo banner and no browser-console errors.
4. Run migrations and the test backup/restore drill against explicit test databases.
5. Recreate a separately named, allow-listed synthetic test database, run migrations, and seed it. Do not use an in-place reset against a retained database. Verify five role accounts and least-privilege navigation.
6. Open the observation form, defect log and incident log. Name a moderator with stop authority.

## Session execution and evidence

Execute Phase D scenarios in order. Capture commit, role, scenario, timestamps, click/time counts, result, visible blocker/source status, audit IDs and synthetic-only screenshots. Record every help request and failed action. Do not change code during a stopped session.

## Mandatory stop conditions

Stop immediately for real data entry; consequential wrong-patient selection; invisible/missed blocker; unauthorized action; inaccessible or mismatched source; AI text shown as verified; automatic AI diagnosis insertion; duplicate invoice/payment; incorrect inventory deduction; missing audit; database/data-loss/storage error; unexplained state; unavailable restore; or browser/backend error affecting safety.

After stop: preserve logs and commit identity, disable external keys, export no patient data, classify severity, reset only the synthetic environment, and open a separately scoped fix. A stop does not authorize an emergency change on the same candidate.

## Rollback and cleanup

1. Stop new mutations and preserve synthetic evidence.
2. Stop application containers; do not run destructive commands against an unverified path/database.
3. Restore the last synthetic test dump into a separate test database and verify row count/checksum before switching anything.
4. Discard only the separately named, verified synthetic database and rebuild it from migrations/seed; remove test document-storage files only after absolute-path verification. The legacy in-place demo reset is not a pilot recovery control.
5. Revoke temporary keys/tokens and remove local environment secrets; retain no credentials in evidence.
6. Re-run migrations, health, login, RBAC/audit checks and the failed scenario before a new decision.

## End checklist

Confirm all accounts logged out; no real data; no external delivery; no open synthetic transaction; audit sequence explainable; consumable/invoice/payment counts match; defects and incidents triaged; backup/restore evidence attached; temporary databases/files/credentials cleaned; decision signed. The only automatic outcome is return to hold.
