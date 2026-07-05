# Changelog

## Unreleased

### Added

- Added PostgreSQL-backed quality gate coverage.
- Added Noop fiscalization integration during invoice issue.
- Added operational frontend workflows for material consumption, purchase receiving, invoice issue/payment and API key management.
- Added release, manual QA and demo-data discipline documents.
- Expanded PostgreSQL integration coverage for FEFO, transfer merge, procurement rollback and appointment-material rollback.
- Added closed pilot feedback issue template and pilot session triage workflow.
- Added public runtime config endpoint for demo mode, real-data status and fiscalization mode.
- Added v0.1 pilot release checklist and dry-run report template.

### Changed

- Demo banner now uses backend public config as the source of truth, with Vite env only as a fallback.
- Frontend date displays use Croatian `dd-mm-YYYY` format.

### Fixed

- Pilot flow tests no longer depend on hardcoded demo dates or payment amounts.

### Known limitations

- Demo data only.
- No real Croatian fiscalization; current fiscalization mode is noop/stub.
- Not a certified EMR.
- No real patient data allowed.
- Module loader is basic and data-only.
- Frontend e2e coverage is limited to static pilot smoke checks.

### Real-data status

- `REAL_DATA_ALLOWED` defaults to `false`.
- Real patient data remains blocked by `docs/REAL_DATA_READINESS_CHECKLIST.md`.
