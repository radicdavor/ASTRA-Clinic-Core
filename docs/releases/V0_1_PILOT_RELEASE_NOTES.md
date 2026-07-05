# ASTRA Clinic Core v0.1-pilot Release Notes

## Version

- Version: `v0.1-pilot`
- Date: 05-07-2026
- Commit SHA: `a4a757fae302d722ee9f2a83bdda5bf06955efee` at V15 review start; replace with final tag SHA before publishing.
- Release type: pilot
- Supported environment: local Docker Compose demo/pilot environment

## Release Scope

This release candidate supports the core demo clinic operations flow with demo data only:

- login
- daily schedule
- appointment detail
- appointment status updates
- material consumption
- stock movements
- draft invoice
- invoice issue
- noop/stub fiscalization warning
- payment recording
- purchase receiving
- audit review
- scoped API key management

## Added

- Public runtime config for demo mode, real-data status and fiscalization mode.
- Backend-driven demo/real-data warning banner.
- Structured pilot feedback issue template.
- Pilot session workflow documentation.
- v0.1 pilot release checklist.
- Pilot dry-run report template.
- Module manifest loader tests.

## Changed

- Frontend date displays use Croatian `dd-mm-YYYY` format.
- Pilot documentation now separates demo readiness from real-data readiness.

## Fixed

- Pilot test coverage avoids hardcoded demo dates and payment amounts.

## Known Limitations

- Demo/pilot data only.
- No real patient data is allowed.
- No real Croatian fiscalization is implemented.
- This is not a certified EMR.
- This is not a certified medical device.
- Module loader is basic and data-only.
- Frontend browser e2e coverage is limited.
- Human participant dry-run feedback is still pending after maintainer command-level validation.
- V13 release decision is Deferred until human pilot is completed or explicitly waived.
- V14 keeps the release Deferred because human pilot evidence is still missing and no waiver exists.
- V15 keeps the release Deferred for the same reason: no completed human pilot and no waiver.
- No full EMR charting.
- No prescription system.
- No clinical decision support.

## Real Data Status

Real patient data is not allowed. `REAL_DATA_ALLOWED` defaults to `false`, and the real-data readiness checklist remains blocking.

## Fiscalization Status

Fiscalization mode is `noop`/stub for demo purposes only. It must not be used for real Croatian fiscalization.

## Migration Notes

- Run Alembic migrations before demo seed.
- For a clean demo environment, use `docker compose down -v` only in demo/local environments.

## Rollback Notes

- Revert to the previous commit and rebuild Docker images.
- Restore PostgreSQL from a known backup if testing against persistent demo data.

## QA Status

- CI: pending GitHub run after final V15 commit.
- Backend tests: passed locally in Docker, `64 passed`.
- Frontend typecheck/build: passed locally.
- Pilot smoke: passed locally.
- Release validation script: passed locally.
- Demo seed/reset: demo seed restored after integration tests.

## Open P0/P1 Issues

- No P0/P1 blocker found during maintainer command-level dry-run.
- Human participant dry-run remains pending before final tag decision.
- `v0.1-pilot` tag remains blocked unless human pilot completes or maintainer waiver is documented.

## Accepted P2/P3 Limitations

- P2: human participant browser pilot remains pending; release tag is deferred unless maintainer waives this risk.
