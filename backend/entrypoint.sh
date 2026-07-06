#!/bin/sh
set -e

alembic upgrade head
python -m app.seed
if [ "${DEMO_MODE:-true}" = "true" ]; then
  python -m app.demo.seed
fi

exec "$@"
