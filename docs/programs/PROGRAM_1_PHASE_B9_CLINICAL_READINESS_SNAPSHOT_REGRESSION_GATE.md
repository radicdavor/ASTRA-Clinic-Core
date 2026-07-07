# Program 1 Phase B9 - Clinical Readiness Snapshot Regression Gate

Status: future regression contract, no implementation

## 1. Svrha

Ovaj dokument definira testove koje buduca implementacija mora proci prije nego sto snapshot persistence moze biti prihvacen.

B9 ne dodaje testove i ne dodaje kod. Ovo je contract za buducu B10 ili kasniju fazu.

## 2. Future backend tests

Buduci backend testovi moraju dokazati:

1. snapshot capture je eksplicitan
2. preview load ne kreira snapshot
3. snapshot sprema immutable copied payload
4. snapshot se ne recomputea nakon promjene templatea
5. snapshot ne mijenja appointment status
6. snapshot ne kreira task
7. snapshot ne kreira episode
8. snapshot ne kreira ClinicalPlan
9. snapshot ne kreira Outcome Evidence
10. snapshot capture pise audit event
11. snapshot view ne mijenja snapshot
12. snapshot supersession kreira novi snapshot
13. snapshot supersession ne brise stari snapshot
14. unreviewed AI se ne koristi kao official source
15. Patient Clinical Summary se ne koristi kao source truth

Dodatno, testovi trebaju dokazati da snapshot sadrzi:

- appointment id
- patient id
- service id
- template key
- template version
- preview status
- limitations payload
- source warnings payload
- preview-only disclaimer

## 3. Future frontend smoke

Buduci frontend smoke mora dokazati:

- Appointment Workspace prikazuje snapshot section samo nakon implementacije
- nema capture buttona dok governance ne postoji
- capture zahtijeva reason
- snapshot history prikazuje preview-only disclaimer
- nema `Mark ready` buttona
- nema `AI cleared` teksta
- nema `Procedure approved` teksta
- nema `Outcome Evidence` labela

Smoke ne smije ovisiti o krhkim timestampovima.

Smoke mora provjeriti korisnicki jezik, ne samo prisutnost komponente.

## 4. No-Go failures

Implementacija mora stati ako:

- snapshot auto-captures on preview load
- snapshot mijenja workflow status
- snapshot djeluje kao approval
- snapshot kreira taskove
- snapshot skriva limitations
- snapshot izostavlja template version
- snapshot izostavlja preview-only disclaimer
- snapshot koristi unreviewed AI kao official source
- snapshot koristi Patient Clinical Summary kao source truth
- snapshot zamjenjuje AuditLog
- snapshot se moze urediti nakon capturea
- snapshot se moze tiho prepisati

Ako bilo koji No-Go uvjet izgleda potreban, to nije bug u gateu nego signal da treba novi architecture decision prije implementacije.
