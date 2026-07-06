# ASTRA Clinic Core v0.1-pilot Release Notes

## Version

- Version: `v0.1-pilot`
- Date: 05-07-2026
- Commit SHA: pending final tag SHA before publishing. V18 implementation and CI fix are green on `bdc282c`.
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
- Global toast feedback after successful create/update/delete actions.
- Optional patient OIB field for demo/pilot identity disambiguation.
- Patient search selection in appointment creation instead of relying on a raw patient dropdown.
- Contextual help popovers for key Novi/Dodaj/Spremi/Izdaj/Zaprimi workflows.
- Service context card in appointment creation.

## Changed

- Frontend date displays use Croatian `dd-mm-YYYY` format.
- Pilot documentation now separates demo readiness from real-data readiness.

## Fixed

- Pilot test coverage avoids hardcoded demo dates and payment amounts.
- Human pilot evidence is now structured: tasks 1-12 passed, real-data confusion was not observed and fiscalization confusion was not observed.
- V18 pilot feedback added patient identity and contextual help hardening without enabling real patient data.

## Known Limitations

- Demo/pilot data only.
- No real patient data is allowed.
- No real OIB values may be entered in demo mode.
- No real Croatian fiscalization is implemented.
- This is not a certified EMR.
- This is not a certified medical device.
- Module loader is basic and data-only.
- Frontend browser e2e coverage is limited.
- Earlier V13-V17 release gates deferred tagging until structured human pilot evidence was complete.
- Structured human pilot evidence is now complete, but the tag still requires explicit maintainer approval.
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
- Structured human walkthrough reported no P0/P1 blockers.
- `v0.1-pilot` tag remains a separate explicit maintainer action after final validation.

## Accepted P2/P3 Limitations

- P2: action completion feedback was too subtle during human walkthrough; fixed with global toast feedback.
- P2: patient identity/search and contextual help needed hardening; fixed in V18.
