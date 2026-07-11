# Program 1 Synthetic Read-Only UI Track Phase A - UI Purpose, Boundary, and Architecture Review

Status: complete.

This phase opens the Program 1 Synthetic Read-Only UI Track after the Local Production Readiness Track final closure. It is not Phase I of the Local Production Readiness Track and does not reopen any previous execution, deployment, real-data, or clinical-use path.

Purpose: provide one isolated clinician-facing synthetic review workspace that is understandable in the existing React frontend while preserving local/demo-only, synthetic-only, read-only boundaries.

User: a local evaluator or clinician reviewing repository-controlled synthetic scenarios.

Non-user: real patients, patient-facing staff workflow users, production operators, EHR/EMR users, or anyone entering real patient data.

Allowed capabilities:

- frontend-only route: `/program1/synthetic-review`
- navigation label: `Program 1 Demo`
- repository-controlled synthetic fixtures
- transient in-memory scenario selection, filtering, tabs, and comparison
- safety labels, limitations, prohibited interpretations, and documentation

Prohibited capabilities:

- real-data UI, PHI/PII handling, backend Program 1 data calls, database access, persistence, export, patient messaging, appointment mutation, clinical writeback, diagnosis, treatment recommendation, triage, production deployment, clinical use, or go-live authorization

Architecture boundary:

- The workspace is implemented under `frontend/src/program1/`.
- It is behind the existing authenticated application shell.
- It does not add backend routes, backend services, migrations, RBAC changes, or API permissions.
- It does not call Program 1 backend endpoints and does not use browser storage.

Risk register:

| Risk | Mitigation | Status |
| --- | --- | --- |
| User confuses demo with clinical workspace | Persistent synthetic safety banner and prohibited interpretation section | Controlled |
| UI appears production-ready | README, roadmap, and page copy state local/demo-only and not for clinical use | Controlled |
| Fixture content appears like real patient data | Obvious synthetic IDs and no real identifiers | Controlled |
| Comparison implies ranking | Descriptive comparison only; no score, winner, priority, or action | Controlled |

Entry criteria for implementation were satisfied by clean branch state, final Local Production Readiness Track closure, and explicit authorization in the request.
