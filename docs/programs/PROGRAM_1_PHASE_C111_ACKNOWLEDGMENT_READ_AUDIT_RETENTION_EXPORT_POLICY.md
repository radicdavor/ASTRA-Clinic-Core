# Program 1 Phase C111 - Acknowledgment Read Audit Retention Export Policy

Status: retention/export policy

## Purpose

C111 defines future retention and export expectations for acknowledgment read audit events.

No export feature or runtime audit event is implemented in this phase.

## Retention Class

Acknowledgment read audit should use access/security audit retention, not clinical evidence retention.

Denied-read audit may deserve longer retention than noisy success-read audit because it has stronger security value.

## Export Eligibility

Future export eligibility must be limited to authorized audit reviewers.

Export must not expose more clinical content than the original audit payload stored.

## Who Can Export

Future export should require an explicit audit/export permission.

Normal acknowledgment read permission must not imply export permission.

## Privacy Minimization

Export payload should prefer:

- event name
- actor id/type
- appointment id
- acknowledgment id if applicable
- access type
- result status
- safe error category
- timestamp

Export should exclude clinical reason text unless a later legal/compliance review explicitly approves it.

## Relation To Snapshot Audit Retention

Snapshot capture/supersession audit records track write events.

Acknowledgment read audit tracks access events.

These must remain separate.

## Relation To Acknowledgment Write Audit

Acknowledgment write audit records human review creation.

Acknowledgment read audit records access attempts.

Read audit must not be treated as evidence that a human reviewed or approved anything.

## Restore Implications

Backup/restore runbooks must preserve audit consistency if read audit is implemented later.

Restored read audit records must not rewrite acknowledgment content or snapshot content.

## Production and Legal Review

Production retention/export policy requires legal, privacy and compliance review.

Real patient data remains no-go.

