# Program 1 Phase C74 - Acknowledgment Read Service Contract

Status: read service contract

## Svrha

C74 definira internal read service koji moze podrzati appointment-scoped read-only API.

## Service Functions

Proposed functions:

- `list_clinical_readiness_review_acknowledgments(db, appointment_id=...)`
- `get_clinical_readiness_review_acknowledgment(db, appointment_id=..., acknowledgment_id=...)`

## List Behavior

List mora:

- ucitati samo acknowledgments za trazeni appointment
- sortirati newest-first by `created_at desc`, `id desc`
- ne pisati audit by default
- ne mijenjati stanje

## Detail Behavior

Detail mora:

- ucitati acknowledgment po id-u
- potvrditi da pripada appointmentu
- vratiti `None` ili not-found signal ako ne pripada appointmentu
- ne pisati audit by default
- ne mijenjati stanje

## Scope Validation

Route layer ili service layer mora potvrditi da appointment postoji.

Acknowledgment koji pripada drugom appointmentu ne smije biti dostupan kroz pogresan appointment route.

## Snapshot Relation

Ako `snapshot_id` postoji, read response smije prikazati id kao referencu.

Read service ne smije mijenjati snapshot payload ili supersession metadata.

## Advisory Signal Key

`advisory_signal_key` je referenca na signal koji je covjek pregledao.

Read service ne smije zakljuciti da je signal resolved.

## No-Go

Read service ne smije:

- create/update/delete acknowledgment
- write success audit by default
- mutate appointment
- create Task
- create Outcome Evidence
- send patient message
- approve, clear or override readiness

