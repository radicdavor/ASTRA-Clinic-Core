# Program 1 Phase B21 - Snapshot Canonical Disclaimer and Immutability

Status: safety hardening contract

## Purpose

This document defines canonical disclaimer and immutability rules for Clinical Readiness Snapshots before any supersession work.

It is not production approval, clinical approval, readiness clearance, compliance approval or certified EMR/medical-device claim.

## Canonical Backend Disclaimer

The canonical backend disclaimer is:

`Snapshot je zapis Clinical Readiness Preview prikaza. Ne predstavlja clinical approval, readiness clearance, Outcome Evidence ili odluku da se postupak smije provesti.`

This disclaimer is stored with each snapshot at capture time.

The stored disclaimer is part of the copied snapshot record.

## UI Display Rule

The UI must display the stored disclaimer verbatim.

The UI must not ad-hoc replace clinical terms in stored snapshot or audit disclaimer text.

If Croatian-only display wording is required later, backend must provide a documented canonical Croatian display field or a new versioned disclaimer.

Frontend string replacement is not an acceptable governance layer.

## Immutable Payload Rule

Snapshot payload fields must not be edited after capture:

- `items_json`
- `limitations_json`
- `source_warnings_json`
- `source_refs_json`
- `preview_summary`
- `template_key`
- `template_label`
- `template_version`
- `template_binding_status`
- `template_binding_warning`
- `snapshot_reason`
- `disclaimer`

Read endpoints may expose payload.

They must not mutate payload.

## No Update/Delete Rule

There must be no snapshot update endpoint.

There must be no snapshot delete endpoint.

There must be no frontend edit/delete/supersede button in B21.

## Future Supersession Rule

Future supersession must be additive, not destructive.

Allowed future pattern:

1. Create a new snapshot.
2. Mark the old snapshot as superseded by the new snapshot.
3. Store supersession metadata and audit event.
4. Keep old payload unchanged.

Supersession must not mean:

- old snapshot was wrong
- patient is ready
- procedure is approved
- warning was overridden
- task was completed
- outcome evidence was created

## B21 Decision

Before supersession, ASTRA must protect the meaning of saved snapshot records:

- disclaimer is canonical
- payload is immutable by route discipline
- read surfaces are read-only
- future supersession is additive only
