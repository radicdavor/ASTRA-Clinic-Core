# Release Checklist

- Canonical `release-evidence.json` and its SHA-256 sidecar validate for the exact source SHA and workflow run.
- Code-merge, deployment, production and real-patient-data readiness are recorded as separate decisions.
- Alembic migrations pass from an empty database.
- Architecture Bible compliance reviewed.
- Backend tests pass.
- PostgreSQL integration tests pass.
- Frontend typecheck passes.
- Frontend build passes.
- Backup and restore procedure reviewed.
- Default credentials changed before production.
- `APP_ENV=production` safety settings reviewed.
- `JWT_SECRET`, CORS and token expiration reviewed.
- RBAC and API key scopes reviewed.
- Audit log behavior reviewed for critical workflows.
- Critical actions have warning, confirmation and audit behavior.
- UI language preserves core ASTRA terms.
- Manual QA checklist completed.

Machine-readable evidence contract: `docs/release-evidence-contract.md`.

Passing this checklist does not itself authorize deployment, production use or
real patient data.
