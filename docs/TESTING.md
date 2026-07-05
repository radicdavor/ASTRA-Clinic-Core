# Testing

V3 introduces backend pytest coverage and CI.

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

Current coverage focuses on:

- FEFO consumption and insufficient-stock rollback behavior
- transfer preserving total stock
- purchase order partial receiving and over-receive rejection
- invoice total recalculation
- partial/full payments and overpayment rejection
- official invoice number uniqueness through a sequence table

CI runs backend pytest and frontend `npm run build` on push and pull request.
