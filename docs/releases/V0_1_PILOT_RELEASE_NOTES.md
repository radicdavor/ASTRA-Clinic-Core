# ASTRA Clinic Core v0.1-pilot Release Notes

## Version

- Version: `v0.1-pilot`
- Date: TBD
- Commit SHA: TBD
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

- CI: TBD
- Backend tests: TBD
- Frontend typecheck/build: TBD
- Pilot smoke: TBD
- Demo seed/reset: TBD

## Open P0/P1 Issues

- TBD before tagging.
