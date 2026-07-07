# Program 1 Phase B0 - Clinical Readiness Implementation Boundaries

Status: documentation-only implementation boundary

## 1. Why not code yet

Clinical Readiness Gate ne treba implementirati prije operating modela.

Razlog:

Implementacija prije dogovorenog jezika, uloga, override pravila i audit semantike mogla bi proizvesti obican checklist engine ili, jos gore, lazni klinicki decision system.

ASTRA mora prvo jasno znati:

- sto je klinicka spremnost
- tko sto smije potvrditi
- sto je warning
- sto je block
- sto se moze overrideati
- sto mora ostati lijecnicka prosudba
- sto se auditira

Bez toga bi sustav povecao broj funkcija, ali ne i sigurnost ili jednostavnost.

## 2. Future implementation sequence

Siguran buduci redoslijed:

1. documentation model
2. vocabulary lock
3. domain object mapping
4. read-only prototype design
5. API contract design
6. UI contract design
7. audit/override model
8. demo-only implementation
9. regression gate
10. only later: task integration

Ovaj redoslijed cuva ASTRA Architecture Bible nacelo:

Lijecnik odlucuje. Uvijek.

## 3. What first implementation should be

Prva implementacija, ako bude odobrena nakon B0/B1, treba biti:

`read-only readiness preview for Appointment Workspace`

Znacenje:

- prikazuje proposed readiness items
- prikazuje warnings
- prikazuje missing documents
- prikazuje sto zahtijeva physician review
- povezuje se na source documents gdje postoje
- ne blokira akciju dok override/role model nije implementiran
- ne stvara taskove
- ne salje poruke pacijentu
- ne zakljucuje klinicku odluku

Read-only preview je najjednostavniji nacin da korisnici vide vrijednost bez stvaranja lazne sigurnosti.

## 4. What implementation must not do

Buduca implementacija ne smije:

- blokirati postupke bez human governance modela
- stvarati taskove automatski
- slati patient messages
- auto-closeati Open Questions
- auto-createati episode plans
- koristiti unreviewed AI suggestions kao facts
- zahtijevati Clinical Episode
- zamijeniti lijecnicku prosudbu
- tvrditi production readiness
- tvrditi certified EMR ili medical-device status

## 5. Future API naming principles

Preporucena imena trebaju biti kvalificirana:

- `clinical_readiness_status`
- `clinical_readiness_items`
- `clinical_readiness_override`
- `operational_readiness_status`

Izbjegavati:

- generic `readiness`
- `ai_decision`
- `auto_clear`
- `procedure_allowed_by_ai`
- `clinical_clearance` ako sugerira certifikacijski ili regulatorni status

Jezik mora jasno razlikovati operativni demo/pilot readiness od klinicke procedure readiness.

## 6. Required audit rules

Buduca implementacija mora auditirati:

- readiness generated
- item confirmed
- warning overridden
- block overridden
- missing document accepted
- physician review completed
- nurse/admin check completed
- override reason updated
- readiness preview regenerated after new evidence

Audit mora razlikovati:

- AI suggested
- human confirmed
- system displayed
- source evidence reviewed

Nijedan audit event ne smije prikazati AI suggestion kao sluzbenu klinicku odluku.

