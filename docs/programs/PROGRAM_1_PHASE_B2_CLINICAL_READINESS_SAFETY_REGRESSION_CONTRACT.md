# Program 1 Phase B2 - Clinical Readiness Safety Regression Contract

Status: documentation-only safety contract

## 1. Svrha

Ovaj dokument definira buduce regression gates prije bilo kakve implementacije Clinical Readiness Previewa.

Ne dodaje testove, kod, UI, API ili migracije u B2.

## 2. Required future backend tests

Kada implementacija pocne, backend testovi moraju dokazati:

1. preview is read-only
2. preview does not change appointment status
3. preview does not create tasks
4. preview does not create episode or clinical plan
5. preview does not use unreviewed AI extraction
6. preview does not use rejected/superseded documents
7. preview does not use Patient Clinical Summary as source of truth
8. preview can show Open Questions as warnings
9. preview does not treat Open Questions as tasks
10. preview does not require Clinical Episode
11. preview remains distinct from `/api/readiness`
12. missing template returns limitation, not error if appointment is otherwise valid

Ovi testovi moraju postojati prije nego sto preview postane vidljiv u demo/pilot flowu.

## 3. Required future frontend smoke

Buduci frontend smoke mora dokazati:

- Appointment Workspace loads preview section
- Preview label is visible
- Operational Readiness is not confused with Clinical Readiness
- no `Mark ready` button exists
- no `AI cleared` text exists
- source badges are visible when source exists
- limitations are visible
- Open Questions are shown as warnings, not tasks
- missing document is shown as missing evidence, not clinical decision

Smoke ne smije ovisiti o krhkim timestampovima.

## 4. No-Go conditions

Implementacija mora stati ako:

- preview blocks workflow
- preview creates tasks
- preview changes appointment
- preview uses unreviewed AI as fact
- preview hides source/limitations
- preview implies production readiness
- preview appears in Readiness Cockpit as if operational readiness
- preview requires Clinical Episode
- preview creates ClinicalPlan
- preview creates Outcome Evidence
- preview sends patient-facing messages

Ako bilo koji No-Go uvjet postane potreban kao buduca funkcija, mora proci zaseban architecture decision i governance contract.

