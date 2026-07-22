#!/bin/sh
set -e

if [ "${APP_ENV:-development}" != "production" ]; then
  alembic upgrade head
  python -m app.seed
  if [ "${DEMO_MODE:-true}" = "true" ]; then
    python -m app.demo.seed
  fi
else
  echo "Production startup: automatic migrations and seed commands are disabled."
fi

exec "$@"
