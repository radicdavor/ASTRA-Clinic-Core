# Program 1 Phase B26 - Regression Notes

Status: snapshot governance and safety label stabilization

## Implemented

B26 stabilizira jezik i guardrails oko snapshot capture/history/detail/supersession UI-ja.

Implementirano:

- governance stabilization document
- canonical safe label rules
- UI helper tekstovi koji naglasavaju da snapshot nije klinicka odluka
- active/superseded labeli:
  - `Nije zamijenjen`
  - `Zamijenjen novijim preview zapisom`
- smoke coverage za safe label presence
- smoke coverage za forbidden wording absence

## Not implemented

B26 nije implementirao:

- nove runtime akcije
- edit/delete
- approval
- clearance
- override
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production governance

## Behavioral Decision

Snapshot history i detail UI moraju ostati historical/preview-only.

Supersession nije correction, deletion, invalidation, approval ili clearance.

## Tests Run

Tijekom B26 pass-a pokrenuto je:

- `git diff --check`
- `npm run typecheck`
- `npm run build`
- `npm run smoke`

## Remaining Risks

- korisnicki tekst jos treba real-world usability review
- DB-level immutability triggeri nisu implementirani
- production governance ostaje nepotpun

## Recommended Next Task

`Program 1 Phase B27 - Snapshot End-to-End Regression Hardening`
