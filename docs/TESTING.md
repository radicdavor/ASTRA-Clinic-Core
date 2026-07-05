# Testing

V3 introduced backend pytest coverage and CI. V4 expands that safety net around scheduling conflicts, role/API-key permissions, billing state transitions and transaction boundaries.
V5 adds audit snapshot coverage and appointment material-consumption atomicity coverage.
Reliability First adds contract hardening, production guard and fiscalization boundary tests.

Run all local checks:

```bash
make test
```

Run backend tests only:

```bash
cd backend
pytest
```

The backend tests use an isolated in-memory database and do not depend on the local development PostgreSQL volume or manual seed data.

Quality Gate adds PostgreSQL integration tests. They run only when `TEST_DATABASE_URL` is set:

```bash
cd backend
TEST_DATABASE_URL=postgresql+psycopg://astra:astra@localhost:5432/astra_ci pytest -m integration
```

CI sets `TEST_DATABASE_URL` to the PostgreSQL service, so integration tests are mandatory on push and pull request. Local runs without `TEST_DATABASE_URL` skip those tests intentionally.

Current coverage focuses on:

- FEFO consumption and insufficient-stock rollback behavior
- transfer preserving total stock
- purchase order partial receiving and over-receive rejection
- failed purchase order receiving leaves no partial inventory mutation
- appointment time validation, provider overlap and room overlap
- cancelled appointments not blocking a new appointment slot
- appointment update revalidating conflicts
- appointment update audit before/after snapshots
- appointment completion with material consumption failing atomically when stock is insufficient
- invoice total recalculation
- draft invoice creation from appointments
- issued invoice line immutability
- partial/full payments, draft payment rejection and overpayment rejection
- official invoice number uniqueness through a sequence table
- role-based permission denial for protected inventory and billing routes
- API-key scoped access and audit logging
- OpenAPI schema does not expose `password_hash` or `key_hash`
- production mode rejects weak JWT/CORS configuration
- fiscalization provider boundary defaults to noop and Croatian provider remains a no-call stub
- PostgreSQL migration smoke checks for key tables
- PostgreSQL API-level permission, appointment and invoice issue/fiscalization workflows
- PostgreSQL FEFO, transfer merge, procurement rollback and appointment-material rollback workflows

CI runs database migrations against a test PostgreSQL service, backend pytest, frontend `npm run typecheck` and frontend `npm run build` on push and pull request.
