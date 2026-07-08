# Program 1 Phase C89 - Acknowledgment UI Snapshot Advisory Relationship

Status: relationship contract

## Relationship Rules

Acknowledgment references an advisory signal through `advisory_signal_key`.

Acknowledgment may reference a snapshot through `snapshot_id`.

## Snapshot Rules

Snapshot remains immutable.

Acknowledgment does not rewrite:

- snapshot payload
- snapshot disclaimer
- snapshot supersession metadata
- historical preview content

Supersession remains additive.

## Advisory Signal Rules

Acknowledgment display must not imply:

- advisory signal is resolved
- readiness issue is cleared
- procedure is approved
- appointment can proceed

## UI Labels

Allowed:

- `Savjetodavni signal`
- `Povezano sa snapshot zapisom`
- `Zapis ljudskog pregleda`

Forbidden:

- rijeseno
- odobreno
- clearance
- override
- Outcome Evidence

## Zakljucak

Acknowledgment UI is traceability for human review context, not clinical decision display.

