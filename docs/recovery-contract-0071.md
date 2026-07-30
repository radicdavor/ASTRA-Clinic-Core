# Recovery contract for Alembic 0071

Status: draft pre-production recovery contract.

This runbook is not production authorization. The repository workflow accepts
only synthetic data, disposable PostgreSQL databases, and allowlisted local CI
hosts. Production recovery, production deployment, and real patient data
require separate owner authorization and deployment-specific validation.

## Architectural intent

Recovery is a critical action. It is fail-closed, operator-confirmed, auditable
through evidence, and designed to preserve the system's single source of truth.
The workflow prefers roll-forward and never reconstructs access or clinical
trust removed by a security correction.

## Supported revisions and application pair

The recovery tools in a given Git commit support:

- an empty database migrated by that commit;
- `0062_signed_report_addendum_integrity`;
- `0069_legacy_document_trust`;
- `0070_membership_correction`;
- `0071_membership_taxonomy`.

The only final application/schema pair validated by this contract is the
recovery PR commit with `0071_membership_taxonomy`. An older supported backup
is restored at its recorded revision and then rolled forward with the Alembic
history from the recovery PR commit.

Running an old application artifact against `0071` is not supported.

## Irreversible security corrections

Recovery and application rollback must not restore:

- legacy clinical-document trust without verified review provenance;
- unsafe automatic clinic membership;
- another privilege removed by a security correction.

Schema downgrade is not a mechanism for reconstructing these states. If an
application deploy fails after a schema migration, keep the verified schema and
roll the application forward or restore a previously verified backup into a
new environment.

## Prerequisites

- PostgreSQL 16 client and server tooling;
- the exact recovery source Git SHA;
- a supported Alembic revision;
- `ASTRA_RECOVERY_ENVIRONMENT=synthetic-test`;
- source and target URLs supplied only through named environment variables;
- target host in `localhost`, `127.0.0.1`, or the CI service name `postgres`;
- database names visibly containing `test`, `ci`, `synthetic`, `recovery`, or
  `restore`;
- an empty disposable target database and empty target storage directory;
- no production secrets or production network route.

URLs are never accepted as command-line values and are not printed. Logs show
only redacted host/database identity and non-sensitive evidence.

## Backup manifest

Every backup directory contains:

- `database.dump`, a custom-format `pg_dump`;
- `manifest.json`;
- `files.manifest.json`;
- `storage/`, containing only referenced canonical document objects.

Manifest version 2 records:

- source Git SHA and `synthetic-test` environment;
- source Alembic revision;
- PostgreSQL and tool versions;
- creation timestamp;
- safe fixed backup filename, size, and SHA-256;
- file-manifest SHA-256;
- complete public-table inventory;
- row counts and ordered canonical SHA-256 projections for critical tables;
- invariant results for Alembic rows, foreign keys, memberships, and document
  institution provenance;
- the synthetic marker and `forbidden_production: false`.

The manifest contains no database URL, credential, patient identifier, or
clinical content.

## Dry-run and backup

Set:

```text
ASTRA_RECOVERY_ENVIRONMENT=synthetic-test
RECOVERY_SOURCE_DATABASE_URL=<disposable synthetic PostgreSQL URL>
ASTRA_APPLICATION_COMMIT=<exact 40-character Git SHA>
```

Run preflight:

```text
python scripts/backup_postgres.py --dry-run --output <new-safe-directory> --storage-root <synthetic-storage>
```

Run backup with the same arguments without `--dry-run`. The destination must
not exist. Publication is an atomic directory rename; overwrite is not
supported. The semantic snapshot and `pg_dump` share one exported PostgreSQL
repeatable-read snapshot, so the manifest and database archive describe the
same committed database state.

## Restore and explicit revision validation

Set:

```text
ASTRA_RECOVERY_ENVIRONMENT=synthetic-test
RECOVERY_TARGET_DATABASE_URL=<empty disposable PostgreSQL URL>
```

Run dry-run first:

```text
python scripts/restore_postgres.py --dry-run \
  --artifact <backup-directory> \
  --target-storage <empty-target-storage> \
  --expected-manifest-sha256 <out-of-band-manifest-sha256> \
  --expected-source-revision <supported-revision>
```

For an actual synthetic restore add:

```text
--confirm-destructive RESTORE_SYNTHETIC_DISPOSABLE_DATABASE
```

For `0062`, `0069`, or `0070` also add `--upgrade-head`.

The restore must prove:

1. exactly one `alembic_version` row exists in the source manifest;
2. the restored revision equals both manifest metadata and the explicitly
   expected source revision;
3. an older restore is upgraded through the official Alembic chain;
4. exactly one final revision exists and equals
   `0071_membership_taxonomy`.

Missing, multiple, unknown, or mismatched revisions stop recovery.

## Restore integrity and TOCTOU control

Before `pg_restore`, the dump is opened as a non-symlink regular file, hashed,
and copied through the same open file descriptor into a private temporary file.
`pg_restore --exit-on-error` consumes only that verified copy.

The operator-supplied manifest SHA-256 is checked before any target database
mutation and binds the selected manifest to the restore decision.

The restore rejects:

- missing or unsupported manifests;
- wrong dump, file-manifest, or object hashes;
- path traversal and symlink inputs;
- unsupported revisions or environments;
- non-empty targets, including user schemas, tables, partitioned/foreign
  tables, views, materialized views, sequences, routines, domains, enums, and
  standalone composite types; system and extension-owned objects are excluded
  using PostgreSQL catalog ownership rather than a broad name allowlist;
- missing destructive confirmation;
- incomplete table inventory or semantic projections;
- row-count, checksum, foreign-key, uniqueness, membership, provenance, trust,
  or audit mismatches.

An interrupted restore leaves `_astra_recovery_incomplete`. `/ready` remains
fail-closed while that marker exists. The marker is removed only after revision,
semantic, storage, and invariant checks succeed.

## Membership, document, and audit semantics

The recovery matrix verifies that:

- manual, unrelated, and legitimate single-candidate memberships survive;
- unsafe automatic membership is not reconstructed;
- corrected assignment provenance and ambiguity/no-candidate/inactive/invalid
  taxonomy survive;
- institution isolation and uniqueness remain enforced;
- unclassified documents remain untrusted and rediscoverable;
- classified state is preserved without trust elevation;
- document institution provenance and stored-object hashes remain consistent;
- audit counts and critical sentinel events remain unchanged;
- restore tooling does not create false user-action audit events.

## Application compatibility smoke

After final revision validation, the current application checks:

- `/health` and `/ready`;
- authentication/session behavior;
- clinic membership projection;
- clinic-scoped access;
- document review queue;
- episode operational projection when the fixture is present.

The test uses only synthetic identities and content.

## Failure decisions

- Corrupt or malicious backup: reject; do not retry without a newly verified
  artifact.
- Interrupted migration/restore: keep the incomplete marker, isolate the
  target, and restart from a new empty target.
- Failed application deploy with valid `0071`: do not downgrade security
  corrections; roll forward the application.
- Required rollback: restore a previously verified supported backup into a new
  target, validate its recorded revision, then roll forward to `0071`.

Never restore over a persistent or non-empty database in this workflow.

## Cleanup and operator sign-off

Disposable source, target, failed-restore databases, temporary verified dumps,
storage staging directories, and test processes must be removed. Workspace
cleanup is verified before the scenario result is written. Evidence is valid
only when cleanup reports `completed`; deletion errors or a surviving
workspace fail the run, and a primary recovery failure plus cleanup failure
preserves both exceptions.

The operator must record:

- incident/change identifier;
- exact Git SHA and workflow run;
- source, restored, and final revisions;
- manifest and backup hashes;
- executed test IDs;
- cleanup result;
- explicit owner decision.

## CI and evidence

`.github/workflows/recovery.yml` runs for recovery-sensitive changes on both
push and pull-request events. The workflow checks out the event-derived source
SHA (`pull_request.head.sha` for pull requests, otherwise `github.sha`) by
explicit `ref` and immediately compares it with `git rev-parse HEAD` before
runtime setup or repository code execution. The verified value is exported as
`REMEDIATION_CHECKOUT_SHA`; backup, evidence production, and final validation
must use that value rather than independently deriving a source identity.

The workflow rechecks source integrity immediately before the recovery matrix,
evidence production, evidence upload, artifact intake, and final evidence
validation. Each canonical recheck fails unless:

- `HEAD` still equals the initially verified SHA;
- the Git repository root equals `GITHUB_WORKSPACE`;
- tracked files and the index still equal `HEAD`;
- no merge, rebase, cherry-pick, revert, or bisect state is active.

The semantic workflow contract uses the same safe PyYAML model as the primary
CI contract. It rejects duplicate YAML keys, later checkouts, redefinition of
the verified SHA, non-canonical verification/recheck commands, artifact
downloads into the repository root, and repository-mutating or unknown Git
subcommands after verification. Its shell-token model is deliberately limited;
it does not claim to interpret arbitrary Bash. Unsupported or unknown Git forms
fail closed, while the mandatory runtime recheck remains the final authority
for actual repository state.

Untracked files are not globally forbidden because recovery legitimately
creates `.recovery-evidence` output. Trust is instead bounded by tracked
source/index equality, fixed evidence paths, exact-SHA binding, local
validation, and artifact checksums.

The recovery evidence record carries the canonical filename and SHA-256 of
`scenario-result.json`. Final validation re-reads that downloaded file and
requires its timestamps, PostgreSQL version, migration result, scenarios,
test IDs, and cleanup status to exactly match the evidence record. A rehashed
change to a scenario backup or manifest checksum therefore cannot detach the
record from the recovery matrix result that produced it.

The workflow uses PostgreSQL 16 and executes:

- recovery unit and negative tests;
- empty database to `0071`;
- `0062`, `0069`, and `0070` restore plus roll-forward;
- current `0071` backup/restore;
- semantic, membership, provenance, trust, audit, application-smoke, corrupt
  backup, interrupted restore, and non-empty-target checks;
- exact-SHA recovery evidence production and independent final validation.

The evidence validator rejects wrong SHA/run, stale or failed evidence, skipped
tests, revision gaps, hash gaps, missing semantic checksums, conflicting
scenarios, and incomplete cleanup. Timestamps must be timezone-aware and are
normalized to UTC. `completed_at` must be no older than the configured maximum
age and no more than five minutes ahead of the validator's single captured
clock value.

## Verified database and storage prerequisites

Recovery accepts only an explicit PostgreSQL URI whose authority and path name
a local disposable recovery database. Libpq parses the connection string before
use. Target-selecting or unknown URI parameters, duplicates, keyword DSNs,
services, service files, host-address overrides, multi-host targets, and
arbitrary options are rejected. The only supported query parameter is a
documented `sslmode` value.

The connection URI is rebuilt from the validated host, port, database, user,
password, and optional SSL mode. PostgreSQL subprocess environments are created
from those components after inherited `PG*` overrides are removed. The original
query string is never reused by `pg_restore` or Alembic.

After connecting, but before the incomplete-recovery marker or any database
mutation, recovery compares `connection.info` and server-reported current
database/user/port with the authorized descriptor. Mismatch stops recovery
without logging the DSN or credentials.

The target storage descriptor is then checked before the marker, restore, or
migration. Non-empty or unsafe targets, unsafe parents, and existing staging
paths fail before database mutation. Checks that depend on restored content
remain post-restore invariants. Preflight is repeated at the copy boundary to
reduce TOCTOU exposure.

## Canonical test IDs and workflow inputs

Evidence schema version 1 requires the ordered, versioned
`RECOVERY_TEST_IDS` tuple from `scripts/recovery_common.py`. The producer emits
that list and the validator rejects wrong collection types, non-string or empty
values, duplicates, omissions, additions, and reordered lists. Rehashing a
non-canonical list does not make it valid.

The semantic workflow contract derives directly executed fixture scripts from
the Python AST and requires both push and pull-request path filters to cover:

- `scripts/validate_0057_clinic_membership_transition.py`
- `scripts/validate_0063_document_provenance.py`

Comments, step names, and similar-but-wrong paths do not satisfy the contract.

## Deployment decisions

- Proposed development/test target: RPO 24 h (maximum 24 h), RTO 2 h
  (maximum 4 h).
- Proposed synthetic pre-production target: RPO 4 h (maximum 8 h), RTO 2 h
  (maximum 4 h).
- Proposed production-candidate target: RPO 15 min (maximum 1 h), RTO 2 h
  (maximum 4 h).
- Owner acceptance of these policy targets: `true` (accepted 2026-07-30).
- Observed production RPO: not measured (`null`).
- Observed production RTO: not measured (`null`).
- A synthetic functional restore is not evidence that a production RPO or RTO
  has been achieved.
- RPO/RTO policy targets are accepted; achieved production measurements remain
  unproven and require a separately authorized production-scale drill.
- encryption/KMS: deployment validation required
- off-site retention: owner and infrastructure decision required
- production topology and credentials: not covered by this PR
- production recovery: not authorized
- production deployment: not authorized
- credential rotation: not authorized
- real patient data: not authorized
