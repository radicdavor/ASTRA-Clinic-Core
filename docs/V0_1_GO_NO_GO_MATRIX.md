# v0.1 Go/No-Go Matrix

| Criterion | Evidence file | Status | Go if | No-Go if |
| --- | --- | --- | --- | --- |
| CI/tests | GitHub Actions, `docs/pilot_sessions/2026-07-05_v0.1_dry_run.md` | Maintainer dry-run passed | CI and backend tests pass | CI fails or backend tests fail |
| Frontend smoke/build | `docs/pilot_sessions/2026-07-05_v0.1_dry_run.md` | Passed in maintainer dry-run | typecheck, smoke and build pass | any frontend release check fails |
| Maintainer dry-run | `docs/pilot_sessions/2026-07-05_v0.1_dry_run.md` | Passed | no P0/P1 found | P0/P1 found |
| Human pilot | `docs/pilot_sessions/2026-07-05_human_pilot_01.md` | Pending, release deferred | completed or explicitly waived | incomplete without waiver |
| P0/P1 issues | `docs/pilot_sessions/*_issue_triage.md` | None from maintainer dry-run; human pilot pending | no open P0/P1 | any open P0/P1 |
| Real-data warnings | `/api/public-config`, README, banner | Implemented, pending human confirmation | `real_data_allowed=false` visible and participant understands it | users may think real data is allowed |
| Fiscalization warning | Invoice UI and release notes | Implemented as noop/stub, pending human confirmation | noop/stub warning visible and participant understands it | users may think fiscalization is real |
| Demo reset safety | `backend/app/demo/reset.py`, runbook | Implemented | reset refuses production | reset can run in production |
| Audit visibility | Audit log/timeline | Pending human confirmation | participant can review who/what/when | audit trail missing or confusing for core flow |
| Material workflow | Appointment detail/backend tests | Pending human confirmation; backend tests passed | participant completes with correct stock movement | stock mismatch or workflow blocked |
| Invoice/payment workflow | Invoice UI/backend tests | Pending human confirmation; backend tests passed | participant issues invoice and records payment | invoice/payment workflow blocked or misleading |
| Purchase receiving workflow | Purchase Orders UI/backend tests | Pending human confirmation; backend tests passed | participant receives valid line and stock updates | receiving blocked or stock mismatch |

Release decision:

- Go: all Go conditions met and no P0/P1 open.
- Deferred: human pilot incomplete and not waived.
- No-Go: any No-Go condition met.
- Waiver: maintainer may waive human pilot only by updating ADR 0001 and release notes with explicit risk.
