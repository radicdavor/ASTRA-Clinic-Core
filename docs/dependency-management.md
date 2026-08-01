# Dependency management

## Sources of truth

- Backend direct dependencies: `backend/requirements.txt`.
- Frontend direct dependency intent: `frontend/package.json`.
- Reproducible frontend dependency graph: `frontend/package-lock.json`.
- CI tooling dependencies: `scripts/test-requirements.txt`.
- GitHub Actions runtimes: pinned major references in `.github/workflows/`.

Do not infer a supported dependency from a developer's global environment.

## Reproducible installation

Use `pip install -r backend/requirements.txt -r scripts/test-requirements.txt`
for the current Python model and `npm ci` for frontend validation. Changes to
direct requirements or the npm lockfile belong in a focused dependency pull
request with a reviewed diff.

The Python requirements currently pin direct versions but do not provide a
hash-locked transitive dependency graph. Adopting an SBOM and hash-locked Python
model is future governance work; this document does not select Poetry, uv,
pip-tools or another packaging migration.

## Automated proposals

### Canonical Dependabot inventory

| Ecosystem | Directory | Tracked surface/manifests | Interval | Day |
| --- | --- | --- | --- | --- |
| `npm` | `/frontend` | `frontend/package.json`; `frontend/package-lock.json` | Weekly | Monday |
| `pip` | `/backend` | `backend/requirements.txt` | Weekly | Monday |
| `github-actions` | `/` | `.github/workflows/*.yml` | Weekly | Monday |
| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |

This inventory mirrors `.github/dependabot.yml`; each row describes a configured
update surface, not an approval. Compatible patch/minor proposals may be grouped.
Major upgrades require a separate pull request and explicit compatibility review.

Dependabot never merges automatically. Each proposal needs exact-head CI and
human review. Repository governance settings must not treat a bot-authored
update as pre-approved.

## Security advisories

Keep advisories visible until a compatible fix is merged and validated. Static
reachability analysis informs severity and scheduling but must not become a
permanent substitute for upgrading.

For each advisory record:

1. affected package and dependency path;
2. runtime, build or test reachability;
3. compatible fixed version;
4. breaking-change risk;
5. required regression suites;
6. production impact and remaining exposure.

Do not run `npm audit fix --force`, silently ignore an advisory or suppress its
warning to make a gate green.

## Required validation

Frontend dependency changes require clean install, audit review, unit tests,
typecheck, production build and relevant browser/DB-backed Playwright tests.
Backend changes require clean installation, targeted and broad backend tests,
PostgreSQL integration when database behavior is affected, and an Alembic
single-head check.

GitHub Actions upgrades require semantic workflow-contract tests and exact-SHA
execution. Platform or transitive warnings remain documented until an upstream
release removes them.

## Future decisions

- Generate and retain a reviewable SBOM for release candidates.
- Select a hash-locked Python dependency workflow.
- Define alert ownership and remediation response expectations.
- Enable GitHub Dependabot alerts/security updates after owner review of the
  repository settings and notification workflow.
