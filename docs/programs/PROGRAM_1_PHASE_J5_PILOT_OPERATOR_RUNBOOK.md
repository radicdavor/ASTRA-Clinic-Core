# Program 1 Phase J5 - Pilot Operator Runbook

## Pre-Demo Checklist

- confirm branch `main`
- confirm expected commit
- confirm working tree is clean
- confirm Docker is running
- confirm no real data is present
- confirm demo users and passwords are understood as development-only

## Startup

```bash
docker compose build backend
docker compose up
```

Backend startup runs Alembic migrations through the configured entrypoint.

## Validation

```bash
git status --short --branch
docker compose run --rm --entrypoint alembic -e PYTHONPATH=/app backend upgrade head
cd frontend && npm run smoke
```

## Demo State Reset

Use the existing demo seed/reset pattern from the main README. Do not use reset scripts in production.

## Failure Handling

- timeline panel fails: stop live clinical workflow demo and use docs/screenshots
- backend fails: stop and report environment issue
- permissions fail: do not bypass; explain access-control boundary
- real data appears: stop immediately and purge the demo environment according to operator policy
