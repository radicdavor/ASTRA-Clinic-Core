# Production Safety Foundation — final security and integrity audit

## Scope

This audit covers the completed local increments on branch `feature/production-safety-foundation`.

The track focused on production-safety foundations, not new clinical automation:

- sensitive audit access hardening
- clinic timezone handling
- canonical dashboard operational status
- daily-dashboard domain extraction
- OpenAPI-generated frontend DTO typing
- Playwright E2E browser coverage
- frontend auth-token storage hardening
- frontend build warning remediation

## Security and integrity findings

### Sensitive access audit

Implemented:

- Sensitive access events are now generated through backend-controlled audit access helpers.
- Client-supplied actor, clinic, journey and arbitrary metadata are not trusted as the source of truth.
- Event-specific permission checks prevent broad generic audit writes.
- Direct patient-export audit event creation is rejected through the public endpoint.
- Audit-log reads are themselves audited without recursive audit loops.
- Interaction idempotency prevents duplicate sensitive-access events.

Residual risk:

- This does not replace full SIEM integration.
- It hardens application-level audit integrity only.

### Clinic timezone handling

Implemented:

- Clinic-local date/time conversion helpers.
- DST ambiguous/nonexistent local-time rejection.
- UTC-aware payment timestamps.
- Clinic timezone exposed through authenticated clinic context.
- Frontend date defaults and refresh timestamps use active clinic timezone.

Residual risk:

- External integrations must still send explicit timezone-aware timestamps or clinic-local date/time pairs.

### Dashboard operational status

Implemented:

- Backend now computes the canonical daily-dashboard operational status.
- Frontend uses backend canonical label, severity and reasons where present.
- Frontend fallback remains only as compatibility behavior for older/mock payloads.
- Red/problem state takes priority over less severe operational states.
- Completed-but-unpaid visits remain payment/billing warnings, not green completion.

Residual risk:

- Operational status policy will need review when additional specialties introduce new terminal states.

### Daily-dashboard domain extraction

Implemented:

- Timeline math, visible range, lane layout, room grouping, journey deduplication and status mapping were extracted from the React page into a tested model.
- Duplicate backend rows for one `journey_id` are collapsed into one physical patient-arrival block.
- Missing `end_time` falls back to a safe minimum block.
- Malformed time data falls back to clinic day start instead of generating invalid CSS positions.
- Loading state hides stale row data while refreshed data is pending.
- Reception modal state closes if the selected journey disappears after filter/date changes.

Residual risk:

- Full visual usability still needs human review on real clinic monitors/tablets.

### OpenAPI-generated frontend types

Implemented:

- Added `scripts/generate_openapi_types.py`.
- Generated `frontend/src/api/generated-openapi.ts` from FastAPI OpenAPI component schemas.
- Connected the dashboard model to generated DailyDashboard types.
- Added CI check to fail if generated frontend types become stale.

Residual risk:

- The generator intentionally covers lightweight TypeScript DTOs, not a full typed API client.

### Playwright E2E

Implemented:

- Added Playwright config and Chromium E2E script.
- Added synthetic dashboard E2E covering:
  - authenticated app shell
  - daily dashboard rendering
  - status signal visibility
  - dashboard-native reception modal
  - red-flag capture
  - canonical clinical workspace routing
- CI installs Chromium and runs the E2E smoke.

Residual risk:

- This is a synthetic route-mocked browser smoke, not a full database-backed end-to-end scenario.

### Auth storage hardening

Implemented:

- New frontend access tokens are stored in `sessionStorage`, not `localStorage`.
- Legacy `localStorage` tokens are migrated to `sessionStorage` on first read and then removed.
- Logout clears both session and legacy token locations.
- Tests cover new-token storage, legacy migration and clearing.

Residual risk:

- This reduces token persistence but does not make browser tokens immune to active XSS.
- A future production hardening track should consider HttpOnly secure cookies and CSRF protection if deployment architecture supports it.

### Frontend build warnings

Implemented:

- Added explicit empty PostCSS config to prevent ambient Tailwind configuration bleed.
- Added Vite manual chunks for stable frontend domains and vendor code.
- Production build no longer emits the Tailwind warning or chunk-size warning.

Residual risk:

- Route-level lazy loading remains a future performance improvement.

## Validation summary

Executed locally:

- Backend full test suite: `620 passed, 15 skipped`
- OpenAPI generated-type check: passed
- Frontend typecheck: passed
- Frontend tests: `53 passed` plus `4` contract checks
- Playwright E2E: `1 passed`
- Frontend pilot smoke: passed
- Frontend production build: passed

Known warnings:

- Backend tests still emit deprecation warnings from `python-jose` use of `datetime.utcnow()`.
- These warnings pre-existed this final audit and are not introduced by this track.

## Safety boundary

No changes in this track authorize or implement:

- autonomous diagnosis
- autonomous treatment
- autonomous procedural clearance
- live external messaging
- live payment terminal integration
- real patient data use

All browser/E2E validation remains synthetic/demo-only.
