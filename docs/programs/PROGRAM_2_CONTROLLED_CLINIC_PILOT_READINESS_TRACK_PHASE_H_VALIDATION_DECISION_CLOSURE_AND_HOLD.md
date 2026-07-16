# Phase H — Validation, decision, closure and hold

Validation date: 16 July 2026. Repository baseline: `radicdavor/ASTRA-Clinic-Core`, `main`, starting commit `bd0b78f`.

## Recorded technical evidence

| Gate | Result |
|---|---|
| Backend full suite with `TEST_DATABASE_URL` required | **496 passed, 0 skipped**, 12 min 34 s after fixture hardening |
| PostgreSQL integration gate | **9 passed, 0 skipped**, 4 min 1 s |
| Frontend contract tests | **3 passed** |
| Frontend interactive tests | **30 passed** in 5 files |
| TypeScript | Passed |
| Production build | Passed; non-blocking 500 kB chunk warning remains |
| Frontend smoke | Passed |
| Dependency audit | 0 vulnerabilities reported by `npm audit` |
| Migration head | One head: `0046_encounter_findings_opinion` |
| PostgreSQL migration boundary | Empty upgrade, one-revision downgrade and re-upgrade passed |
| Synthetic backup/restore | Separate target restored; sentinel row count and checksum matched |
| Docker | Backend/frontend images built; backend health 200; frontend HTTP 200; demo login passed |
| Browser | Administrator/reception/nurse/physician/billing synthetic role review; current Docker build checked at 1024×720 and 1280×720 without horizontal overflow |
| Repository release script | Passed in an isolated Alpine shell |
| Diff hygiene | `git diff --check` passed |

The default Compose frontend port `5173` was occupied by an unrelated local process, so the built frontend image was started on test port `4179` on the same Compose network. The port conflict did not affect image build, backend health, frontend HTTP, login or browser validation and no unrelated process was stopped.

No direct browser-console capture API was available in the controlled in-app browser. No visible browser error, failed network workflow, backend error or container error occurred during the checked paths. This is recorded as a tooling limitation, not as a claim of exhaustive console certification.

## Safety conclusions

- AI diagnosis suggestions default to off and fail closed.
- Suggestions remain outside formal diagnosis and require individual clinician acceptance or rejection.
- No canonical repository ICD catalog exists; therefore AI diagnosis suggestions remain **DISABLED / PILOT BLOCKED**.
- Stub OCR, communication, summary and fiscalization providers cannot silently masquerade as production providers.
- No real data, live provider, production deployment or go-live was enabled.
- Human usability thresholds were not measured and are not claimed.

## Decision

**READY FOR HUMAN SYNTHETIC USABILITY EVALUATION**

This is decision A only. It does not authorize the evaluation session automatically, a controlled clinic pilot, real patient data, production deployment or go-live.

## Closure and hold

The readiness track is technically closed within its synthetic preparation scope. Exact post-closure hold:

**STOP AND CONDUCT HUMAN SYNTHETIC USABILITY EVALUATION**
