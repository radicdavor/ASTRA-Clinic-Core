# Release Checklist

- Alembic migrations pass from an empty database.
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
- Manual QA checklist completed.
