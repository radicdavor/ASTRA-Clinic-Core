# v0.1 Go/No-Go Matrix

| Criterion | Evidence file | Status | Go if | No-Go if |
| --- | --- | --- | --- | --- |
| CI/tests | GitHub Actions, `docs/pilot_sessions/2026-07-05_v0.1_dry_run.md` | Maintainer dry-run passed | CI and backend tests pass | CI fails or backend tests fail |
| Frontend smoke/build | `docs/pilot_sessions/2026-07-05_v0.1_dry_run.md` | Passed in maintainer dry-run | typecheck, smoke and build pass | any frontend release check fails |
| Maintainer dry-run | `docs/pilot_sessions/2026-07-05_v0.1_dry_run.md` | Passed | no P0/P1 found | P0/P1 found |
| Human pilot | `docs/pilot_sessions/2026-07-05_human_pilot_01.md` | Structured walkthrough completed | structured report completed or explicitly waived | incomplete without waiver |
| P0/P1 issues | `docs/pilot_sessions/*_issue_triage.md` | None from maintainer dry-run or structured human walkthrough | no open P0/P1 | any open P0/P1 |
| Real-data warnings | `/api/public-config`, README, banner | Implemented and human check reported no confusion | `real_data_allowed=false` visible and participant understands it | users may think real data is allowed |
| Patient identity | `docs/V18_PATIENT_IDENTITY_AND_CONTEXTUAL_HELP_PLAN.md`, Patient API, AppointmentForm | OIB optional; appointment creation uses resolved patient search | user selects a resolved patient and does not enter real OIB in demo | ambiguous patient selection or real OIB confusion |
| Fiscalization warning | Invoice UI and release notes | Implemented as noop/stub and human check reported no confusion | noop/stub warning visible and participant understands it | users may think fiscalization is real |
| Demo reset safety | `backend/app/demo/reset.py`, runbook | Implemented | reset refuses production | reset can run in production |
| Audit visibility | Audit log/timeline | Human check passed | participant can review who/what/when | audit trail missing or confusing for core flow |
| Material workflow | Appointment detail/backend tests | Human check passed; backend tests passed | participant completes with correct stock movement | stock mismatch or workflow blocked |
| Invoice/payment workflow | Invoice UI/backend tests | Human check passed; backend tests passed | participant issues invoice and records payment | invoice/payment workflow blocked or misleading |
| Purchase receiving workflow | Purchase Orders UI/backend tests | Human check passed; backend tests passed | participant receives valid line and stock updates | receiving blocked or stock mismatch |

Release decision:

- Go: all Go conditions met and no P0/P1 open.
- Deferred: structured human pilot evidence incomplete and not waived.
- No-Go: any No-Go condition met.
- Waiver: maintainer may waive human pilot only by updating ADR 0001 and release notes with explicit risk.

Current decision state: Go candidate for explicit maintainer tag decision after final validation checks.
