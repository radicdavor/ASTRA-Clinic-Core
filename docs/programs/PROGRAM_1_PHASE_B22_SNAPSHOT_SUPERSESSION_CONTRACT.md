# Program 1 Phase B22 - Snapshot Supersession Contract

Status: documentation-only contract

## Purpose

Supersession defines how ASTRA will later show that one Clinical Readiness Snapshot has been followed by a newer snapshot.

This document does not implement backend code, frontend code, endpoint, service, migration or schema change.

Supersession is not approval, clearance, override, Outcome Evidence, Task creation or appointment status change.

## Lifecycle

Future lifecycle:

1. Existing snapshot remains stored.
2. User captures a new snapshot with required reason.
3. User explicitly marks old snapshot as superseded by the new snapshot.
4. Old snapshot receives supersession metadata only.
5. Old copied payload remains unchanged.
6. Audit event records the relationship.

## Old Snapshot Behavior

The old snapshot:

- remains stored
- remains readable
- keeps original copied payload
- keeps original disclaimer
- keeps original capture reason
- keeps original created timestamp
- may receive supersession metadata only

The old snapshot must not be deleted.

The old snapshot payload must not be edited.

Supersession does not mean the old snapshot was wrong.

## New Snapshot Behavior

The new snapshot:

- is captured through the normal reason-required capture flow
- has its own immutable copied payload
- has its own disclaimer
- has its own audit capture event
- may become the target of old snapshot supersession metadata

The new snapshot does not approve the procedure.

The new snapshot does not clear readiness.

## Required Reason

Supersession requires a human-entered reason.

Examples:

- "New snapshot after reviewed external pathology."
- "New preview after template version change."
- "New capture after additional source document review."

Empty reasons are not allowed.

AI must not silently generate final supersession reason.

## Allowed Roles

Future default:

- Physician: allowed with `clinical_readiness.snapshots.supersede`
- Nurse: deferred and only if governance allows operational supersession
- Reception: not allowed by default
- Admin: not automatically allowed unless governance explicitly grants it
- AI/API/system: not allowed by default

Default must be deny.

## Relationship To Idempotency

Idempotency protects duplicate capture attempts.

Supersession links an old snapshot to a new snapshot.

Idempotency key must not be used as supersession reason.

Supersession must reference concrete snapshot ids.

## Relationship To History UI

History UI may later show:

- old snapshot
- new snapshot
- superseded label
- supersede reason
- superseded timestamp

History UI must keep old snapshot visible.

History UI must not hide, delete or rewrite old payload.

## Relationship To Detail View

Detail view must show original copied payload.

If superseded, detail view may show supersession metadata separately.

Supersession metadata must not replace original content.

## No Approval Or Clearance Semantics

Supersession does not mean:

- patient is ready
- procedure is approved
- warning is overridden
- task is completed
- Outcome Evidence exists
- appointment status changed
- old snapshot was invalid

Supersession is a historical relationship between immutable preview records.
