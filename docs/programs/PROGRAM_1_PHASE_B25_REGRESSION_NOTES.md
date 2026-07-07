# Program 1 Phase B25 - Regression Notes

Status: snapshot supersession UI reason modal

## Implemented

B25 dodaje konzervativni frontend supersession workflow u Appointment Workspace.

Implementirano:

- frontend supersession request/response tipovi
- API client metoda `supersedeClinicalReadinessSnapshot(...)`
- reason-required modal za zamjenu snapshota novim preview zapisom
- safe action label: `Spremi novi snapshot i oznaci ovaj kao zamijenjen`
- validation za prazan razlog
- 403 permission error poruka
- refresh snapshot history nakon uspjeha
- refresh otvorenog detail panela ako je stari snapshot otvoren
- smoke coverage za safe label, modal i forbidden controls

## Not implemented

B25 nije implementirao:

- edit/delete
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

Supersession UI je dostupan samo kao reason-required action iz snapshot detail panela.

UI tekst mora ostati povijesni i preview-only. Zamjena snapshota ne znaci da je stari snapshot pogresan, da je pacijent spreman ili da je postupak odobren.

## Tests Run

Tijekom B25 pass-a pokrenuto je:

- `npm run typecheck`
- `npm run build`
- `npm run smoke`
- `git diff --check`

Zavrsni puni testovi navedeni su u finalnom izvjestaju cijelog B24-B28 passa.

## Remaining Risks

- permission UX je osnovan
- supersession UI treba kasniji usability review
- nema production governancea
- DB-level immutability triggeri nisu implementirani

## Recommended Next Task

`Program 1 Phase B26 - Snapshot Governance and Safety Label Stabilization`
