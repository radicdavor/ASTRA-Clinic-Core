# ASTRA Clinic Core production deployment runbook

This runbook is the controlled production path. Do not use the development
Compose defaults for production and do not enter real patient data in demo or
test environments.

## 1. Prerequisites

- A production host or managed container platform.
- PostgreSQL 16 or a compatible managed PostgreSQL service.
- TLS termination for the public domain.
- A tested backup and restore process.
- Access to the repository at the exact commit intended for deployment.

## 2. Required environment variables

Use `.env.production.example` as the template. Required values include:

- `APP_ENV=production`
- `DATABASE_URL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `JWT_SECRET`
- `BROWSER_SESSION_MINUTES`
- `SESSION_COOKIE_SECURE=true`
- `CSRF_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAMESITE=lax` unless a reviewed cross-site deployment requires `none`
- `CORS_ORIGINS`
- `CORS_ORIGIN_REGEX=` empty
- `DEBUG=false`
- `RELOAD=false`
- `DEMO_MODE=false`
- `DEMO_SEED_ENABLED=false`
- `AUTO_CREATE_DEFAULT_ADMIN=false`
- `REAL_DATA_ALLOWED=true`
- provider modes for fiscalization, OCR, reminders and AI summaries

Never commit a filled production `.env` file.

Browser users authenticate with an opaque server-side session in the httpOnly
`astra_session` cookie. The browser must not receive or store an access token in
`localStorage` or `sessionStorage`. The separate Bearer token endpoint remains
for Swagger, CLI and integrations. HttpOnly cookies reduce token theft through
JavaScript, but they do not eliminate XSS; injected JavaScript could still
attempt actions in the active browser session, so CSP, escaping, CSRF and
Origin checks remain part of the production boundary.

## 3. Generate strong secrets

Generate unique values outside the repository, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Use separate values for `JWT_SECRET` and the database password. Do not reuse
development values such as `astra`, `secret`, `change-me`, or
`change-this-local-secret`.

## 4. Prepare PostgreSQL

Create the database and application user with the least privileges required for
the application and migrations. Verify connectivity from the backend runtime
before running migrations.

## 5. Back up before migration

Before every schema migration:

1. create a database backup;
2. verify that the backup completed successfully;
3. perform a restore test in a non-production environment when the migration is
   destructive or high risk.

Migrations are not executed automatically by application startup. They must be a
controlled deployment step.

The backend entrypoint enforces this boundary when `APP_ENV=production`: it
starts the requested API command without running Alembic, catalog seed or demo
seed. Development/test startup retains the local convenience behavior.

## 6. Check Alembic current/head

From the backend environment:

```bash
alembic current
alembic heads
```

There must be exactly one Alembic head.

## 7. Run migration

After backup verification:

```bash
alembic upgrade head
```

If a migration fails, stop deployment and investigate. Do not bypass failures by
manually editing `alembic_version`.

## 8. Startup

Start the application with explicit production configuration:

```bash
docker compose --env-file .env.production -f docker-compose.prod.example.yml up -d --build
```

The example is a baseline single-host deployment, not a high-availability
orchestration design.

The minimal process model is PostgreSQL, one FastAPI process and one Nginx
process serving the static React build. No Redis, queue broker, scheduler or
permanent maintenance worker is required.

This process boundary, startup measurements, maintenance ownership and known
limits are recorded in `lean-core-runtime-and-maintenance.md` and the final
`lean-core-optimization.md` report. Do not add a resident worker or cache without
a new measured requirement.

## 9. Liveness

Check:

```bash
curl -f http://localhost:8000/health
```

`/health` only confirms that the process is alive.

## 10. Readiness

Check:

```bash
curl -f http://localhost:8000/ready
```

`/ready` must report:

- database reachable;
- schema up to Alembic head;
- configuration valid.

It returns no secrets.

### Bounded maintenance

Run schema inspection and expired/revoked-session cleanup as explicit,
short-lived commands:

```bash
docker compose --env-file .env.production -f docker-compose.prod.example.yml exec backend python -m app.cli schema-status
docker compose --env-file .env.production -f docker-compose.prod.example.yml exec backend python -m app.cli session-cleanup
```

Schedule session cleanup with cron or the host task scheduler at an interval
appropriate to the installation. It must not become a loop inside the API
process. Backup and restore remain outside this module and require the separate
Module 4 workflow.

For pre-deployment performance checks, apply the budgets in
`performance-budget.md` with authenticated requests on a controlled host. A
developer-workstation sample is diagnostic evidence, not production capacity
approval.

## 11. Initial admin provisioning

Production must not auto-create a default admin with a static password. Use an
explicit provisioning step approved for the deployment environment, and require
the administrator to change any temporary password immediately.

## 12. Smoke test

After readiness succeeds:

- open the frontend through the production domain;
- log in with the provisioned admin;
- select the active clinic;
- load “Danas u poliklinici”;
- verify that no demo banner or demo seed data is present.

## 13. Logs

Review backend and database logs for:

- startup configuration failures;
- database connectivity;
- Alembic revision mismatch;
- authentication failures;
- provider integration failures.

Do not log secrets or patient data unnecessarily.

## 14. Application rollback

If application code fails but schema is compatible:

1. stop the new application containers;
2. start the previous application image;
3. verify `/health` and `/ready`;
4. run the smoke test.

## 15. Migration rollback

Only run Alembic downgrades if the specific migration is documented as safe for
the current data. Many production rollbacks should use application rollback plus
database restore instead of destructive schema downgrade.

## 16. Database restore

If data integrity is affected:

1. stop application writes;
2. restore the verified backup;
3. run `alembic current`;
4. start the compatible application version;
5. verify `/ready`.

## 17. Secret rotation

Rotate secrets when:

- a secret is exposed;
- personnel changes require it;
- provider credentials change;
- a scheduled security rotation is due.

After rotating `JWT_SECRET`, existing access tokens become invalid.

## 18. Demo/test prohibition

Do not use `docker-compose.yml`, `.env.example`, demo seed scripts, or any
synthetic/demo data flow for production. Real patient data belongs only in the
explicit production environment.
