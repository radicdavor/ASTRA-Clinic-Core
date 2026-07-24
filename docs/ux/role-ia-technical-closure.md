# Role and information architecture — technical closure

Measured: 23 July 2026

Branch: `ux/information-architecture-simplification`

Decision: **READY FOR HUMAN USABILITY REVIEW**

This decision covers the local, controlled, synthetic demo only. It does not
claim that a human usability session occurred and does not authorize
production, real patient data or clinical use.

## Root-cause findings

### Backend timeout

The full backend suite was slow but did not hang. A ten-minute outer command
limit stopped the former run shortly before pytest completed. The final run
used Python faulthandler and pytest duration reporting:

- 800 tests collected;
- 782 passed;
- 18 skipped because PostgreSQL integration and one POSIX-only check are
  separate platform gates;
- 667.39 seconds pytest time;
- slowest individual test: 4.70 seconds;
- no deadlock, leaked worker or blocked teardown was found.

The PostgreSQL tests were then run separately against a migrated isolated
database and all 16 passed. No global timeout was increased to hide a defect.

### DB-backed Playwright timeout

The old runner requested frontend port 5174 while an unrelated NURA Vite
process already owned it. Vite silently selected a different port, while the
runner accepted the unrelated server and Playwright waited for ASTRA content
that could never appear.

The runner now:

- reserves isolated backend and frontend ports;
- uses Vite `--strictPort`;
- uses its own PostgreSQL database and deterministic synthetic seed;
- validates an app-name and run-ID identity handshake;
- waits separately for migration, seed, health, readiness and frontend;
- tracks only its own process IDs;
- tears down processes and the database in `finally`;
- captures Playwright diagnostics on failure.

The final DB-backed suite completed 12 of 12 tests in 109.8 seconds including
the five-persona switch and stale-context regression.

### Smoke contract

The former source-fragment test depended on historical prose. It was replaced
with five browser-level semantic persona contracts based on routes, headings,
accessible labels, primary actions and prohibited navigation. All five pass.

## Persona and session evidence

The synthetic seed creates real database users, roles, permissions,
memberships and provider assignments for:

| Persona | Operational scope proven |
| --- | --- |
| Administrator | Administrative and security navigation; no automatic clinical editor |
| Tajnica | Clinic A operational workflow; no clinical/security scope |
| Medicinska sestra | Clinic A and Institution A medical support; no API-key administration |
| Liječnik 1 | Clinic A and Provider A workflow; own clinical draft |
| Liječnik 2 | Clinic B and Provider B workflow; no Clinic A operational obligation or foreign draft edit |

The browser scenario performs:

`Administrator → Tajnica → Sestra → Liječnik 1 → Liječnik 2 → Administrator`.

After every switch it waits for the new backend session, CSRF context, clinic
membership, route and relevant API response. Returning to a multi-clinic
administrator clears the previous persona's active clinic and requires an
explicit selection. Backend tests prove the allowlist, demo-only gate,
production denial, real-data denial, CSRF requirement, audit, logout,
revocation and stored role/membership/provider source of truth.

Frontend visibility remains presentation only; backend authorization remains
the security boundary.

## Timezone and responsive evidence

Clinic-local date regressions cover:

- Europe/Zagreb standard time;
- Europe/Zagreb daylight-saving time;
- both DST transition instants;
- local midnight where UTC and clinic dates differ;
- active-clinic timezone changes;
- dashboard default-day recalculation after clinic switch.

At 1024 × 768 the dashboard has no page-level horizontal overflow. The
timeline owns its internal overflow and keeps the primary controls available.

## Final validation

| Gate | Result |
| --- | --- |
| Backend full | 782 passed, 18 expected platform/gate skips; 667.39 s |
| Backend fast | 150 passed |
| PostgreSQL integration | 16 passed |
| PR3 security/provenance with required PostgreSQL | 59 passed, 0 skipped |
| Frontend unit | 101 passed |
| Program 2 contracts | 4 passed |
| Semantic smoke | 5 passed |
| Route-mocked Playwright | 7 passed |
| DB-backed Playwright | 12 passed |
| TypeScript | passed |
| Production build | passed |
| OpenAPI generated contract | passed |
| Empty PostgreSQL migration | `base → 0066` passed |
| Populated migration cycle | `0066 → 0062 → 0063 → 0066 → 0062 → 0066` passed |
| Alembic heads | one: `0066_api_key_tenant_scope` |
| Alembic metadata comparison | 86 previously classified historical operations; no new 0064–0066 drift |
| Development Compose config | passed |
| Production Compose contract | passed with temporary synthetic values |
| Production fail-closed config cases | passed |
| Synthetic backup/restore | passed, row count and checksum matched |
| Human usability session preflight | passed; five personas and isolated teardown verified |
| `git diff --check` | passed |

`alembic check` intentionally remains non-zero because of the classified
historical ORM/migration metadata differences in
`docs/alembic-metadata-drift.md`. Empty installation, populated downgrade and
upgrade, provenance validators and backup/restore all pass. A broad
autogenerated migration would be destructive and is not part of this closure.

## Environment

- Windows NT 10.0.22621
- Python 3.12.13
- Node 24.18.0
- npm 11.16.0
- PostgreSQL 16.14
- Docker 29.6.1
- Docker Compose 5.3.0
- Playwright 1.61.1

## Production and secret boundary

Production Compose was rendered only with temporary, obviously synthetic
values. Demo mode and the persona switcher are off in that configuration.
No `.env` file is tracked, no tracked `sk-proj-`/literal OpenAI key match was
found outside the validator fixture, and the production frontend bundle
contains no OpenAI, JWT or database secret marker.

No production deployment or provider connection was attempted.

## Human review package

Run:

```powershell
cd frontend
npm run usability:preflight
npm run usability:session
```

The second command leaves the isolated synthetic stack running until
`Ctrl+C`, then removes only its own processes and database. Moderator tasks,
measurements, scoring table and stop conditions are in
`docs/ux/human-usability-protocol.md`.

Human usability status remains **NIJE PROVEDENO**.

