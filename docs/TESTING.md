# Testing

V3 introduced backend pytest coverage and CI. V4 expands that safety net around scheduling conflicts, role/API-key permissions, billing state transitions and transaction boundaries.

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
- failed purchase order receiving leaves no partial inventory mutation
- appointment time validation, provider overlap and room overlap
- cancelled appointments not blocking a new appointment slot
- invoice total recalculation
- draft invoice creation from appointments
- issued invoice line immutability
- partial/full payments, draft payment rejection and overpayment rejection
- official invoice number uniqueness through a sequence table
- role-based permission denial for protected inventory and billing routes
- API-key scoped access and audit logging

CI runs database migrations against a test PostgreSQL service, backend pytest and frontend `npm run build` on push and pull request.
