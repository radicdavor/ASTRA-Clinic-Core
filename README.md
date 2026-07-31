# ASTRA Clinic Core

ASTRA Clinic Core is a modular clinic-operations foundation for controlled,
synthetic demonstration and development. It connects scheduling, patient
journeys, clinical documents, reception, inventory, invoicing, payments and
audit through one FastAPI API and one shared domain language.

> **Controlled synthetic demo only.** Do not enter real patient, PHI, PII,
> production credential or production infrastructure data.

## What ASTRA is

- A pre-1.0 clinic-operations codebase built around Patient, Appointment,
  PatientJourney, Service, Invoice and Audit objects.
- A React/TypeScript frontend backed by FastAPI, SQLAlchemy, Alembic and
  PostgreSQL.
- A technical environment for synthetic workflow, authorization, recovery and
  release-evidence validation.
- An API-first system in which backend authorization is authoritative and AI
  remains an assistive, human-reviewed capability.

## What ASTRA is not

ASTRA is not a certified EMR, certified medical device, clinical decision
system or GDPR-certified solution. It is not authorized for deployment,
production use, a patient pilot or real patient data. Green CI and generated
evidence prove only the technical scope stated by their exact commit and run;
they do not grant deployment, production or real-data authorization.

The repository is licensed under the
[Apache License 2.0](LICENSE), including its explicit patent grant. Licensing
does not grant deployment, production, clinical or real-patient-data
authorization.

## Current status

Current stage: **controlled synthetic demo**.

- Implemented: patient and appointment workflows, coordinated patient journeys,
  documents, reception, encounter notes, inventory, local invoicing/payment,
  RBAC and audit.
- Synthetic/demo: seeded accounts and data, deterministic summaries, local
  document handling, noop fiscalization and recovery drills.
- Not authorized: real data, production deployment, public booking, live
  providers, real fiscalization, payment terminals or clinical use.
- Next human gate: moderated synthetic usability evaluation. Automated browser
  tests are not a substitute for human usability evidence.

Authoritative current-state sources:

- [Current product state](docs/CURRENT_PRODUCT_STATE.md)
- [Current architecture](docs/CURRENT_ARCHITECTURE.md)
- [Current operational limitations](docs/CURRENT_OPERATIONAL_LIMITATIONS.md)
- [Production-readiness backlog](docs/PRODUCTION_READINESS_BACKLOG.md)
- [Documentation index](docs/README.md)

## Architecture

```text
React + TypeScript + Vite
          |
       REST API
          |
FastAPI + SQLAlchemy + Alembic
          |
      PostgreSQL
```

Browser users authenticate with revocable httpOnly cookie sessions and CSRF
protection. Bearer JWT and API keys support controlled CLI and integration
clients. All modes use shared permission-based authorization. Important
mutations are audited. Original clinical documents remain the source of truth;
derived OCR or AI output never silently replaces them.

The highest architectural authority is the
[ASTRA Architecture Bible](docs/ASTRA_ARCHITECTURE_BIBLE.md). New work must
preserve human control, one source of truth, shared language, modular Clinic
Core boundaries, API-first behavior, auditability and demo-data safety.

## Prerequisites

- Docker with Docker Compose
- Git
- For direct development: Python 3.12 and Node.js compatible with the checked-in
  frontend toolchain

## Quick start

Copy the development environment template, review every value, then start the
local stack:

```bash
cp .env.example .env
docker compose up --build
```

Run migrations and seed synthetic demo data:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.demo.seed
```

Reset only the local synthetic demo when required:

```bash
docker compose exec backend python -m app.demo.reset
```

Development defaults are not production configuration. Never place production
secrets or real records in `.env`, fixtures, logs, screenshots or artifacts.

## Backend development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt -r scripts/test-requirements.txt
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Frontend development

```bash
cd frontend
npm ci
npm run dev
```

`package-lock.json` is the reproducible frontend dependency source. Use
`npm ci` in validation and do not use `npm audit fix --force`.

## Tests

Run checks proportional to the change. Run the backend gate commands below
from the repository root; the wrapper establishes the backend working directory
and import path without requiring an inherited `PYTHONPATH`.

```bash
# Backend fast suite
python scripts/run_test_gate.py fast

# Governance and evidence contracts
python -m pytest scripts/tests/test_repository_governance.py \
  scripts/tests/test_release_evidence.py -q

# Frontend unit and contract tests
cd frontend
npm ci
npm test
npm run typecheck
npm run build

# Alembic single-head check
cd ../backend
test "$(alembic heads | wc -l)" -eq 1
```

PostgreSQL integration, DB-backed Playwright, recovery and evidence checks run
in GitHub Actions. Their success is valid only for the exact checked-out SHA.
See the [test strategy](docs/test-strategy.md) and
[release evidence contract](docs/release-evidence-contract.md).

## Security and data handling

- Use synthetic data only.
- Never commit secrets, private keys, production `.env` files or credentials.
- Backend authorization, not hidden UI controls, enforces access.
- AI output is a suggestion and requires human review.
- Critical actions require explicit controls and audit evidence.
- Report security concerns according to [SECURITY.md](SECURITY.md). Private
  vulnerability reporting is enabled; submit sensitive reports through the
  linked GitHub Security Advisory flow, never through a public issue.

## Dependencies

Dependency declarations are maintained in `backend/requirements.txt`,
`frontend/package.json`, `frontend/package-lock.json` and GitHub Actions
workflow references. Dependabot proposes bounded updates but never merges them
automatically. See [dependency management](docs/dependency-management.md).

Known advisories remain visible until a compatible update and relevant tests
close them. Static reachability analysis can inform urgency but does not replace
eventual remediation.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before making changes. Work through a
focused branch and pull request, keep data synthetic, preserve exact-head CI and
request security-sensitive review for authentication, authorization, tenant
scope, audit, migrations, recovery and evidence changes.

Repository ownership rules are recorded in
[`.github/CODEOWNERS`](.github/CODEOWNERS). They support review routing but do
not replace GitHub branch protection or an explicit owner decision.

## Release and production boundaries

These are separate decisions:

1. A commit or pull request may have complete technical evidence.
2. An owner may authorize merge after review.
3. A separate process may authorize deployment to a defined environment.
4. Production use and real patient data require additional legal, privacy,
   security, operational and clinical governance evidence.

No current CI artifact grants steps 3 or 4. Review the
[release checklist](docs/RELEASE_CHECKLIST.md),
[operational limitations](docs/CURRENT_OPERATIONAL_LIMITATIONS.md) and
[production-readiness backlog](docs/PRODUCTION_READINESS_BACKLOG.md).

## Documentation

Start with [docs/README.md](docs/README.md). It separates current canonical
documents from historical implementation evidence. Historical closure reports
remain useful for reconstructing a past commit or run, but they do not override
current code, configuration or canonical current-state documents.
