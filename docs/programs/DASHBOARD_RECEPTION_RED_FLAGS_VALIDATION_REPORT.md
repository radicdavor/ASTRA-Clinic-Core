# Dashboard Reception Red Flags Validation Report

Branch: `codex/dashboard-reception-red-flags`  
Starting commit: `1eb37fa Complete reception red flag handoff`  
Final commit: recorded in repository history as `Validate dashboard reception and medical handoff`  
Scope: validation and minimal safety fixes for dashboard-native reception, red flags, idempotency, and medical handoff.

## Implemented in this validation increment

- Patient-name links on the daily dashboard now open `/journeys/{id}` instead of forcing the reception-focused workspace route.
- The explicit dashboard action remains the only dashboard path that opens the reception floating modal.
- `complete-reception` now supports `idempotency_key`.
- Same idempotency key with the same reception payload returns the existing completed check-in.
- Same idempotency key with different payload returns HTTP 409 with `code = idempotency_conflict`.
- Reception completion stores the idempotency key and payload fingerprint in the journey event metadata.
- The dashboard reception modal submits a stable idempotency key per modal open.
- The older Patient Journey Workspace reception fallback also submits an idempotency key.
- The reception modal now sends only changed patient fields when confirming demographics.
- Existing synthetic/demo e-mails ending in `.invalid` remain readable in API responses.
- Changing patient e-mail clears `email_verified_at`.
- `JourneyCheckIn.reception_note` stores the new visit-scoped "Napomena za današnji dolazak".
- New reception notes are no longer written to longitudinal `patient.notes` from either the dashboard floating reception modal or the workspace fallback modal.
- Patient PATCH accepts `expected_updated_at` and rejects stale demographic edits with HTTP 409 and `code = stale_patient`.
- The frontend conflict panel keeps the modal open and preserves local red flags, conditional details, and the visit-scoped reception note.

## PostgreSQL and Alembic validation

Synthetic PostgreSQL database: `astra_reception_validation`  
Connection used from host PowerShell: `postgresql+psycopg://astra:astra@localhost:5432/astra_reception_validation`

The earlier `getaddrinfo failed` was environmental: local PowerShell was using the Docker service hostname (`db`). That hostname is valid from inside the Docker network, but not from the host process. The host-side validation uses `localhost`.

Validated:

- `alembic heads` reports one head: `0056_reception_note_patient_concurrency`.
- `alembic upgrade head` succeeded from an empty PostgreSQL database.
- `alembic current` initially reported `0055_check_in_red_flag_handoff`.
- `alembic upgrade head` applied `0056_reception_note_patient_concurrency`.
- `alembic downgrade -1` succeeded back to `0055_check_in_red_flag_handoff`.
- Re-upgrade to head succeeded.
- Final current head was `0056_reception_note_patient_concurrency`.
- `journey_check_in_items` contains the additive red-flag handoff fields, including `details_json`, `activity_ids_json`, `medical_disposition`, `medical_disposition_note`, `medical_reviewed_by`, and `medical_reviewed_at`.
- The medical disposition index and `medical_reviewed_by` foreign key were present.
- New additive column `journey_check_ins.reception_note` was created and downgraded cleanly.

## Backend validation

Targeted post-fix command:

```text
backend/.localrun-venv/Scripts/python.exe -m pytest tests/test_patient_oib.py tests/test_journey_check_in.py -q
```

Result from the first validation commit:

```text
15 passed, 66 warnings in 23.30s
```

Result after visit-scoped reception note and patient concurrency hardening:

```text
19 passed, 79 warnings in 29.76s
```

Additional backend validation performed earlier in the same validation run:

- `tests/test_journey_check_in.py`: 8 passed before adding the final idempotency regression.
- `tests/integration -q -rs` with `TEST_DATABASE_URL` set to the synthetic PostgreSQL database: 10 passed.
- Full backend suite was rerun with sufficient timeout:
  - `534 passed, 811 warnings in 510.19s (0:08:30)`.
  - No failed, skipped, or xfailed tests were reported.
  - Slowest setup/call durations were reported by `--durations=30`; the slowest setup was `5.83s` and the slowest call was `3.79s`.

Backend semantics confirmed by tests:

- Reception can complete while medical review remains pending.
- Reception completion does not create a medical disposition.
- Receptionist cannot call the medical-disposition endpoint; direct API call returns 403 for missing `checkin.clinical_review`.
- Authorized medical roles can record a medical disposition.
- Medical disposition is tied to the correct check-in item/activity.
- Shared red flags can reference multiple activities without creating a global blocker.
- Reception completion is idempotent for retries and conflicts on changed payload.
- Legacy synthetic `.invalid` e-mails are readable on unchanged patient updates.
- Changing e-mail clears verification state.
- Visit-scoped reception note is saved on the check-in and does not change `patient.notes`.
- Another arrival for the same patient does not inherit the previous reception note.
- Stale patient updates return 409 and do not overwrite server data.
- Stale e-mail updates do not clear the current e-mail verification timestamp.
- Duplicate OIB remains blocked when using `expected_updated_at`.

## Frontend validation

Post-fix command:

```text
npm run typecheck
npm test -- --run
npm run build
npm run smoke
```

Result:

- Typecheck passed.
- Frontend tests passed: 42 tests across 7 files.
- Contract tests passed: 4 tests.
- Production build passed.
- Smoke test passed.
- `npm ci` passed with 0 vulnerabilities.

Warnings:

- Vite reported a large JavaScript chunk warning.
- Tailwind reported missing or empty `content` configuration during smoke/build.
- These warnings pre-existed this validation scope and did not fail the build.

An earlier `npm ci` attempt failed because a live Windows `esbuild.exe` process locked a file in `node_modules`. After stopping the workspace-related process, `npm ci`, build, and smoke passed.

## Browser validation

Browser surface used: running synthetic stack at `http://127.0.0.1:5175/` with backend at `http://127.0.0.1:8010`.

Reception red-flag path was tested in the in-app browser as `demo.reception@astra.local`:

- Opened daily dashboard.
- Kept URL on `http://127.0.0.1:5175/`.
- Searched for `Sintetički 01`.
- Used explicit `Otvori prijem` action.
- Confirmed the floating modal opened over the dashboard.
- Confirmed patient identity form showed the selected patient.
- Changed the phone number.
- Confirmed patient data.
- Opened the short reception checklist.
- Marked `Problem s postom`.
- Confirmed conditional fields appeared for the selected red flag.
- Selected `2–4 sata` and `kava s mlijekom`.
- Added note: `Pacijent navodi kavu s mlijekom prije dolaska.`
- Completed reception.
- Confirmed URL stayed unchanged.
- Confirmed dashboard search/filter context stayed on `Sintetički 01`.
- Confirmed row updated to `Čeka pregled/pretragu`.
- Confirmed red detail was visible: `Prijem ima crvenu napomenu`.
- Confirmed next action became `Otvori pregled`.
- Confirmed no browser console errors were observed.

Fast path was tested in the same browser session:

- Searched for `Sintetički 02`.
- Opened `Otvori prijem`.
- Confirmed data.
- Did not mark any red flag.
- Completed reception.
- Confirmed URL stayed on the dashboard.
- Confirmed search/filter context stayed on `Sintetički 02`.
- Confirmed row updated to `Čeka pregled/pretragu`.
- Confirmed no red-warning note was shown.

Fast-path interaction count from dashboard row to completed reception:

1. `Otvori prijem`
2. `Podaci su točni`
3. `Provjereno`

Manual/browser concurrency status:

- Browser-level stale conflict was not repeated after the final backend/frontend hardening because the project does not include Playwright and the prompt did not authorize adding a full E2E track.
- The conflict behavior is unit-tested at the frontend level and API-tested at the backend level.

## Dashboard state preservation

Browser and frontend tests confirmed:

- URL remains unchanged when reception opens and closes from the dashboard.
- Dashboard remains mounted.
- Search/filter context is preserved.
- Patient/room view is preserved by component state.
- Focus returns to the originating row/action in frontend tests.

## Medical handoff

Implemented and tested:

- Clinical workspace exposes `Podaci evidentirani na prijemu`.
- Red-flag details carry structured note/details/activity provenance.
- Visit-scoped reception note is displayed in the handoff panel.
- Reception role does not receive medical-disposition controls.
- Direct receptionist API call to medical disposition returned 403.
- Backend tests cover authorized medical disposition and per-item/per-activity behavior.

Not fully browser-tested in this increment:

- A complete role-switched physician browser walkthrough was not automated because the project does not include Playwright, and adding a new E2E stack was outside this validation scope.

## Accessibility

Confirmed by component behavior/tests and browser inspection:

- Reception modal is rendered as an application dialog.
- The modal keeps the dashboard mounted underneath.
- Controlled unsaved-change dialog is used instead of `window.confirm`.
- Frontend tests cover focus return after modal close.

Partially deferred:

- Full manual screen-reader pass.
- Mobile viewport browser validation.
- Shared focus-trap primitive extraction.

## Remaining limitations

- Full per-field merge UI remains deferred; stale conflicts require loading current patient demographics before retry.
- Explicit OIB-change confirmation and duplicate-OIB workflow remain limited to existing patient validation behavior.
- A project-owned Playwright E2E suite is not present.
- No real SMS, e-mail, OCR, AI secretary, public booking, payment-terminal, or production integration was authorized or tested.

## Status

Implemented: dashboard-native reception validation fixes, idempotent completion, changed-field patient patching, verified e-mail invalidation, canonical patient-name link, visit-scoped reception note, patient optimistic concurrency.
Unit-tested: backend reception and patient update behavior; frontend dashboard/modal behavior.  
PostgreSQL-tested: Alembic 0055 and 0056 upgrade/downgrade/re-upgrade on synthetic PostgreSQL.
Integration-tested: PostgreSQL integration tests passed on synthetic database.  
Browser-tested: reception red-flag path and fast path on the running synthetic stack.  
Synthetic-only: all browser/API data used synthetic demo users and patients.  
Deferred: full Playwright E2E, mobile accessibility pass, per-field conflict merge, explicit OIB-change confirmation dialog.
