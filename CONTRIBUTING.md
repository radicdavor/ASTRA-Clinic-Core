# Contributing to ASTRA Clinic Core

ASTRA is currently a controlled synthetic-demo project. Contributions must
preserve human control, one source of truth, shared language, auditability and
safe-by-default handling of clinical data.

## Workflow

1. Start from the current remote default branch in a focused branch.
2. Make one coherent change with proportional tests and documentation.
3. Push the branch and open a pull request; do not push directly to `main`.
4. Keep the pull request Draft while known implementation or review blockers
   remain.
5. Use exact-head CI evidence. A green run for an older SHA is not evidence for
   the current head.
6. Resolve actionable review findings technically before requesting merge.

Do not use force push, squash another contributor's history, bypass repository
governance or enable automerge without explicit owner authorization.

## Data and credentials

- Use synthetic data only.
- Never use or commit real patient, PHI or PII data.
- Never commit production credentials, private keys or production `.env` files.
- Do not copy sensitive production logs, screenshots, dumps or artifacts into
  an issue, pull request or test fixture.

## Scope and architecture

Read [`docs/ASTRA_ARCHITECTURE_BIBLE.md`](docs/ASTRA_ARCHITECTURE_BIBLE.md)
before implementation. Ask whether the change makes ASTRA simpler or merely
larger. Preserve the Clinic Core model and the shared Patient, Appointment,
Service, Invoice and Audit language.

Keep pull requests small and focused. Separate dependency major upgrades,
migrations, security remediation and feature work when they require different
review or rollback decisions.

## Tests

Run checks proportional to the change and report the exact commands/results.

- Backend changes: targeted tests plus the relevant backend suite.
- Frontend changes: `npm test`, typecheck, production build and relevant
  Playwright coverage.
- Migration changes: verify a single Alembic head and test upgrade paths.
- Recovery/evidence changes: run their semantic contracts, mutation tests and
  exact-source validation.
- Documentation/governance changes: validate YAML and internal links.

Never reduce test scope, add skip/xfail, suppress warnings or use
`continue-on-error` merely to obtain a green result.

## Security-sensitive review

Authentication, authorization, clinic/institution scope, audit, migrations,
backup/restore, recovery and evidence changes require explicit security-aware
review. Frontend visibility is not authorization. AI output remains assistive
and human-reviewed.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md). Do not place
sensitive vulnerability details in public issues while no verified private
reporting channel is configured.

## Authorization boundaries

Merge, deployment, production use and real-patient-data use are separate owner
decisions. Neither a merged pull request nor green CI grants deployment,
production, clinical or real-data authorization. Do not describe synthetic
tests as operational proof.
