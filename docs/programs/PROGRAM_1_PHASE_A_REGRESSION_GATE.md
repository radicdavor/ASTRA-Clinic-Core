# Program 1 - Phase A Regression Gate

## 1. Svrha

Ovaj dokument definira regresijski gate prije bilo kakvog buduceg sirenja Program 1 razvoja.

Gate cuva Patient Knowledge Foundation nakon Phase A hardeninga. Njegova svrha nije dodati novu funkcionalnost, nego sprijeciti tihe regresije u klinickom znanju, source-linked pravilima, AI suggestion granicama, readiness semantici i deferred episode scopeu.

Ovaj dokument nije:

- nova funkcionalnost
- produkcijsko odobrenje
- real-data odobrenje
- compliance odobrenje
- tvrdnja da je ASTRA certificirani EMR
- tvrdnja da je ASTRA medicinski uredaj

ASTRA u ovoj fazi ostaje demo/pilot sustav. Stvarni pacijentovi podaci nisu dopusteni.

## 2. Zasticeni invariants

Regression gate stiti ove invariants:

1. `ClinicalDocument` je source object.
2. `Finding` jos nije zaseban domain object.
3. AI extraction je prijedlog, ne sluzbena istina.
4. Official Patient Clinical Knowledge zahtijeva reviewed source documents.
5. `PatientClinicalSummaryRecord` je samo summary view.
6. Open Questions su source-linked upozorenja, ne taskovi.
7. ClinicalDocument Detail odvaja raw source, AI suggestion i physician review.
8. Clinical Evidence Timeline je read-only audit view.
9. Operational Readiness nije Clinical Readiness Gate.
10. Episode-Based Care ostaje deferred.
11. Nema real AI/OCR providera.
12. Nema stvarnih pacijentovih podataka.

## 3. Gate checks

Minimalni regression gate ukljucuje:

- backend testove
- frontend typecheck
- frontend build
- frontend smoke
- `git diff --check`
- opcionalno `make test` gdje je dostupan

Targeted backend gate mora posebno cuvati:

- official knowledge source rules
- summary view semantics
- open question source rules
- AI rejection behavior
- evidence timeline read-only behavior
- operational readiness semantics
- deferred Episode Engine behavior
- demo/real-data guardrails

## 4. No-Go triggers

Buduci Program 1 rad ne smije proci gate ako se dogodi bilo sto od sljedeceg:

- unreviewed AI output se prikaze kao official knowledge
- summary stvara official facts bez source documents
- open questions se pojave bez reviewed sourcea
- odbijanje AI prijedloga odbije ili sakrije raw document source
- evidence timeline stvara odluke, taskove ili outcomes
- readiness se ponasa kao Clinical Readiness Gate
- Episode/Task/Workflow scope udje u Phase A bez posebne odluke
- stvarni pacijentovi podaci se pojave u seedu ili testovima
- produkcijske ili certifikacijske tvrdnje se pojave u dokumentaciji ili UI-ju

Ako se neki gate mora promijeniti, promjena mora biti eksplicitno obrazlozena i odobrena kroz dokumentaciju prije implementacije.

## 5. Buduca upotreba

Svaki buduci Program 1 implementation prompt mora:

- sacuvati ovaj regression gate
- pokrenuti relevantne gate provjere
- dokumentirati rezultate
- jasno navesti ako se gate mijenja

Ako buduca funkcionalnost zahtijeva promjenu gatea, prompt mora objasniti zasto se invariant mijenja, koji je novi invariant i kako ce se stititi testovima ili smoke provjerama.
