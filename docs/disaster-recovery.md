# Disaster recovery procedure

## Trigger and authority

Declare recovery only through the installation's incident authority. Freeze
writes, preserve incident evidence and identify the exact application commit,
backup artifact and target environment. Do not restore over the damaged system.

RPO and RTO are not chosen by this repository. The clinic and infrastructure
owner must approve them, provision backup frequency/capacity and test them on
the real deployment platform.

## Recovery sequence

1. Isolate the failed environment and rotate exposed credentials.
2. Select the newest verified artifact consistent with the approved RPO.
3. Provision a new empty PostgreSQL database and empty document storage.
4. Restore using `docs/backup-and-restore.md`.
5. If required, explicitly migrate a known older revision to the current head.
6. Verify database/file hashes and domain relationships.
7. Confirm all old active browser sessions are revoked.
8. Start the matching application image without automatic migration or seed.
9. Pass `/health`, `/ready` and the security-aware application smoke.
10. Obtain clinical/operational approval before DNS or traffic cutover.
11. Monitor authentication, audit, database and source-download errors.
12. Retain or destroy failed environments and artifacts according to policy.

## Required invariants

- Institution to Clinic and User to ClinicMembership links are unchanged.
- Global Patient identity and clinic associations are unchanged.
- Appointments, journeys and activities keep clinic/patient provenance.
- Signed report rendered/structured content and SHA-256 remain exact.
- Each addendum retains its exact signed-report version link.
- Each source document retains classification, object path, size and SHA-256.
- Invoice lines, payments and journey/patient links remain exact.
- Audit rows remain present without adding raw clinical text to recovery logs.
- Cross-institution access remains denied.
- Pre-recovery browser session cookies no longer authenticate.

## Failure handling

Checksum, missing/extra object, unknown revision, non-empty target and
PostgreSQL-tool failures terminate non-zero. A failure after target mutation
leaves `_astra_recovery_incomplete`; readiness fails. Never drop that marker to
make a partial target appear healthy. Discard the partial target, investigate
the operation-ID logs, correct the cause and retry from a new empty target.

## Recovery exercise

The automated synthetic gate runs:

```bash
docker build -f backend/Dockerfile.recovery -t astra-recovery-test .
docker run --rm --network host \
  -e RECOVERY_ADMIN_DATABASE_URL \
  -e ASTRA_APPLICATION_COMMIT \
  astra-recovery-test scripts/run_recovery_integration.py
```

It creates and removes isolated PostgreSQL databases and temporary files. It
must never target a database containing real or valuable development data.
The local development database recorded at revision 0061 remains untouched.

## Production limitations

The automated gate proves application-level recovery mechanics, not operational
HA or deployment certification. Still required: managed encrypted backup
storage, off-site copy, key escrow/rotation, approved retention, alerting,
operator access audit, platform-specific restore drills, measured RPO/RTO,
capacity tests and production-host benchmarks.
