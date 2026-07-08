# Program 1 Phase C12 - Enforcement UI Copy and Safety Labels

Status: design-only UI wording rules

## Allowed Labels

- Advisory signal
- Review required
- Missing input
- Source-linked warning
- Clinician review needed
- Non-blocking readiness signal
- Demo/pilot only

## Forbidden Labels

- Approve
- Clear
- Override
- Mark ready
- Procedure approved
- Patient ready
- Clearance
- Outcome Evidence
- Create task

## Helper Text Examples

Safe helper text:

- `Ovo je savjetodavni signal za ljudski pregled.`
- `Signal ne mijenja status termina.`
- `Signal nije klinicko odobrenje.`
- `Provjerite izvor prije odluke.`

## Error Text Examples

Safe error text:

- `Signal trenutno nije dostupan.`
- `Nije moguce ucitati savjetodavni prikaz.`

## Button Wording Rules

Future buttons must avoid approve/clear/override wording.

Allowed future wording may include:

- `Dodaj biljesku pregleda`
- `Oznaci da je pregledano`

Only if a future phase explicitly implements acknowledgment.

## Croatian And English

Both Croatian and English UI text must avoid clearance and approval semantics.

## Recommended Next Task

`Program 1 Phase C13 - Enforcement Readiness CI and Test Gate`
