# Program 1 Phase B27 - Regression Notes

Status: snapshot end-to-end regression hardening

## Implemented

B27 ne dodaje novu funkcionalnost. Dodaje regresijsku zastitu za cijeli Clinical Readiness Snapshot tok.

Implementirano:

- end-to-end backend regresija:
  - live preview GET ne persistira snapshot
  - capture stvara snapshot i audit
  - idempotent retry vraca isti snapshot i ne pise drugi capture audit
  - history prikazuje captured snapshot
  - detail vraca copied payload
  - supersession stvara novi snapshot
  - stari snapshot je oznacen kao zamijenjen
  - stari copied payload ostaje nepromijenjen
  - novi snapshot se pojavljuje prvi u historyju
  - capture i supersession audit eventovi postoje
  - appointment status ostaje nepromijenjen
  - Task, Outcome Evidence, ClinicalPlan, ClinicalEpisode i patient messaging side effecti se ne stvaraju
- permission matrix regresija:
  - read permission moze history/detail read, ali ne capture
  - write permission moze capture, ali ne supersession
  - supersede permission je potreban za supersession
  - API key je odbijen za capture i supersession
  - limited user je odbijen
  - admin ostaje dozvoljen prema seedanoj permission matrici
- frontend smoke hardening:
  - preview section
  - history section
  - detail panel action
  - capture modal safe wording
  - supersession modal safe wording
  - forbidden wording absence

## Not Implemented

B27 nije implementirao:

- nove API endpointove
- nove UI akcije
- snapshot edit/delete
- approval
- clearance
- override
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production governance
- real AI/OCR
- real patient data

## Behavioral Decision

Snapshot lifecycle je sada pokriven regresijski kao preview-history tok, a ne kao clinical enforcement tok.

Supersession ostaje additive:

- stari snapshot ostaje spremljen
- stari payload ostaje nepromijenjen
- novi snapshot se stvara iz trenutnog server-side previewa
- audit biljezi supersession
- supersession ne znaci da je stari snapshot bio pogresan
- supersession ne znaci da je pacijent spreman
- supersession ne odobrava postupak

## Tests Run

Tijekom B27 pass-a pokrenuto je:

- `docker compose build backend`
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_snapshots.py`
- `npm run smoke`
- `git diff --check`

Zavrsni full regression commands trebaju se pokrenuti nakon B27 roadmap commita.

## Remaining Risks

- DB-level immutability triggeri nisu implementirani
- permission UX je jos osnovan
- production governance ostaje nepotpun
- real patient data ostaje no-go
- clinical enforcement ostaje no-go

## Recommended Next Task

`Program 1 Phase B28 - Program 1 Phase B Snapshot Closure Gate`
