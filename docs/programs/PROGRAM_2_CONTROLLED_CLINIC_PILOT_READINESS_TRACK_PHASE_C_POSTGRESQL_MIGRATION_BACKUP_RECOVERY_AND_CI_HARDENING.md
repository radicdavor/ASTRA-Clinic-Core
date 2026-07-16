# Phase C — PostgreSQL, migration, backup, recovery and CI hardening

## Authoritative CI gate

GitHub Actions starts PostgreSQL 16, supplies `DATABASE_URL` and `TEST_DATABASE_URL`, and sets `ASTRA_REQUIRE_TEST_DATABASE=true`. The PostgreSQL fixtures fail rather than skip when the readiness gate lacks its URL. CI runs the full backend suite and a separate `tests/integration` gate.

Migration validation checks exactly one Alembic head, upgrades an empty PostgreSQL database to head, downgrades one supported revision and re-upgrades. This does not claim every historical downgrade path.

## Synthetic backup/restore drill

`scripts/validate_test_backup_restore.sh` requires explicit, different source and target URLs. It accepts only PostgreSQL URLs on local/test hosts whose database names contain `test`, `ci`, `synthetic` or `restore`. It never has production defaults and contains no credentials.

The drill inserts one clearly synthetic sentinel, creates a custom-format dump, recreates a separate target database, restores it, and compares sentinel row count and checksum. The corresponding Make target requires both URLs. This validates a test recovery path, not backup encryption, retention, production RPO/RTO or operator readiness.

## Failure and idempotency review

| Path | Existing behavior / control |
|---|---|
| Database unavailable/failed transaction | Request fails; transactional service paths roll back. No automated failover. |
| Consumable/invoice/payment failure | Explicit mutation, transaction and audit; user receives error. Duplicate protection varies by endpoint and remains a runbook stop condition. |
| Missing document/storage | Source endpoint returns 404/409; checksum/path boundary enforced. |
| AI/OCR/reminder unavailable | Explicit 503/failed job; clinical action is not retried automatically. |
| Stale browser/duplicate submission | State-machine and conflict responses protect major transitions; no universal idempotency key layer. |
| Journey closure | Closure prerequisites are re-evaluated; repeated invalid closure is rejected. |

Appointment/journey uniqueness, one preparation per journey, document job state, invoice state and closure guards supply narrow idempotency. A universal API redesign was intentionally not introduced.
