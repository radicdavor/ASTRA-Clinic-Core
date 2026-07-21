# Production Safety Foundation — PR preparation note

## Branch

`feature/production-safety-foundation`

## Proposed PR title

Production safety foundation hardening

## Suggested PR summary

This branch hardens production-safety foundations before further workflow expansion.

Included:

- backend-controlled sensitive-access audit event hardening
- complete clinic timezone handling for scheduling, dashboard dates and payment timestamps
- canonical backend operational status for the daily clinic dashboard
- extracted and tested daily-dashboard domain model
- OpenAPI-generated frontend DTO types with CI stale-type check
- Playwright browser E2E smoke for dashboard-native reception and clinical workspace routing
- frontend token persistence reduction from localStorage to sessionStorage with legacy migration
- frontend build warning cleanup through explicit PostCSS config and Vite manual chunks
- final security/integrity audit documentation

Validation:

- backend full suite: 620 passed, 15 skipped
- frontend tests: 53 passed + 4 contract checks
- frontend typecheck: passed
- Playwright E2E: 1 passed
- frontend pilot smoke: passed
- frontend production build: passed
- OpenAPI generated-type check: passed

Notes:

- No push has been performed from this local task.
- No PR has been opened from this local task.
- Browser/E2E validation is synthetic and route-mocked.
- Backend warning noise remains from an upstream `python-jose` UTC deprecation warning.

## Commit sequence prepared locally

- `b7c9df2` Harden sensitive access audit events
- `e6c7f3a` Complete clinic timezone handling
- `f069504` Add canonical dashboard operational status
- `cb66db7` Extract daily dashboard domain logic
- `86a705b` Add OpenAPI-generated frontend types
- `dc79059` Add dashboard Playwright E2E coverage
- `d77f691` Harden frontend auth token storage
- `ca48a29` Resolve frontend build warnings

The final documentation commit should be added after this note.
