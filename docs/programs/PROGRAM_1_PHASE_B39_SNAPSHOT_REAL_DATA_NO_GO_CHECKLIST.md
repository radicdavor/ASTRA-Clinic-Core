# Program 1 Phase B39 - Snapshot Real-Data No-Go Checklist

Status: real patient data remains no-go

## Purpose

This checklist documents what blocks Clinical Readiness Snapshot use with real patient data.

It does not enable real patient data.

## Required Before Real Patient Data

Real patient data remains no-go until all items below are reviewed and explicitly approved by maintainers.

## Checklist

### GDPR / DPIA Review

- DPIA completed
- legal basis documented
- data processor roles documented
- patient rights process documented
- deletion/rectification process documented

### Access-Control Review

- role matrix reviewed
- snapshot read/write/supersede permissions reviewed
- API key runtime write denied or explicitly governed
- audit access limited
- admin accounts hardened

### Audit Retention Review

- retention period defined
- export policy defined
- audit review process defined
- immutable audit policy reviewed
- incident audit process documented

### Backup/Restore Drill

- backup scope includes snapshots and audit logs
- restore drill completed
- DB immutability trigger restored
- supersession relationships validated
- idempotency metadata validated

### Security Review

- authentication reviewed
- CORS reviewed
- JWT secret reviewed
- database credentials reviewed
- dependency scan completed
- network exposure reviewed

### Role Training

- staff trained that snapshot is not clinical approval
- staff trained that supersession is not deletion
- staff trained that audit is event history, not Outcome Evidence
- staff trained on demo/pilot limitations

### Legal Wording

- disclaimers reviewed
- user-facing wording reviewed
- documentation reviewed
- no production/certification claims approved without legal review

### Data Minimization

- snapshot payload reviewed for minimization
- export fields reviewed
- log payload fields reviewed
- patient identifiers reviewed

### Incident Response

- suspected breach workflow defined
- audit review workflow defined
- backup restore contact defined
- access revocation process defined

### Production Deployment Policy

- deployment target approved
- HTTPS enforced
- backups configured
- monitoring configured
- CI gate required
- rollback plan documented

### Maintainer Approval

- named maintainer approval required
- approval date required
- scope of approval required
- review expiry required

## Explicit No-Go

No-go remains for:

- real patient data
- production
- clinical enforcement
- automated readiness decisions
- patient messaging
- Outcome Evidence
- Task engine

## Recommended Next Task

`Program 1 Phase B40 - Snapshot Production Governance Closure Matrix`
