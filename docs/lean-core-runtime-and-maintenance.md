# Lean Core runtime and maintenance model

## Minimal process architecture

Both development and the production Compose example require three services:

1. PostgreSQL;
2. one FastAPI/uvicorn process;
3. one Nginx process serving the static React build.

There is no Redis, Celery, queue broker, permanent scheduler or maintenance
worker. The Nginx container is the static frontend server/reverse-proxy boundary,
not an application worker. This matches the intended small-clinic capacity and
does not need a distributed architecture.

## Startup boundary

Development and test retain convenient automatic migration plus catalog/demo
seed behavior. Production startup does neither. With `APP_ENV=production`, the
entrypoint immediately executes the requested server command after printing the
boundary notice.

Production deployment therefore remains explicit:

1. back up and verify according to the production runbook;
2. run `alembic current` and `alembic heads`;
3. run `alembic upgrade head` as a controlled deployment step;
4. start the API;
5. require `/ready` to report the expected revision.

Application import validates production configuration and performs only the
configured one-time schema readiness check. It does not seed data, migrate,
clean sessions, scan the database or wait for optional AI providers.

## Maintenance CLI

The standard-library CLI delegates to existing services:

```text
python -m app.cli schema-status
python -m app.cli session-cleanup
```

`schema-status` returns JSON and exits non-zero when the database is unreachable
or not at the single expected Alembic head. `session-cleanup` deletes only
revoked sessions whose expiry is in the past and commits once. It does not revoke
active sessions and does not run automatically.

Use Docker Compose one-shot commands, cron or Windows Task Scheduler. Do not add
a resident scheduler for these bounded operations. Backup/restore is explicitly
reserved for Module 4 and is not implemented here.

## Dependency review

Backend runtime packages are all used by the API or its current in-container
validation workflow: FastAPI/uvicorn, SQLAlchemy/psycopg/Alembic, Pydantic,
JWT/password hashing, multipart upload and e-mail validation. `pytest` and
`httpx` support the repository's backend tests; separating a runtime-only lock
file would add packaging drift without measured image-size evidence, so they are
retained in this increment.

Frontend runtime dependencies are React, React DOM, React Router and Lucide.
Vite, TypeScript, jsdom, Testing Library, Vitest and Playwright are build/test
dependencies. No unused package was removed based on text search alone. The
frontend image now uses `npm ci` against the committed lock file for a
deterministic build rather than resolving dependencies with `npm install`.
Its Docker context also excludes local `node_modules` (139.5 MiB in the measured
workspace), build output and browser-test artifacts. The observed context
transfer dropped from 148.09 MB before the ignore file to a small source-only
increment after it, removing 26.6 seconds of local context transfer from the
measured uncached build path.

## Operational validation

- CLI unit tests cover commit/output and ready/not-ready exit codes.
- production entrypoint behavior is validated with `APP_ENV=production` and a
  harmless command, proving Alembic and seed are not invoked;
- development Compose and production-example Compose configurations are parsed;
- frontend image dependency installation is lock-file deterministic;
- no service was added to either Compose configuration.
