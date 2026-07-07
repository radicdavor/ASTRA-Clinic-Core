# Program 1 Phase B8 - Clinical Readiness Snapshot Boundaries

Status: design-first, demo/pilot only

## 1. Svrha

Ovaj dokument definira granice izmedju buduceg Clinical Readiness Snapshota, audita, outcome evidencea i klinicke odluke.

Snapshot je koristan samo ako ostane jasno ogranicen: on biljezi sto je preview prikazao, ali ne stvara odluku, ne stvara zadatak i ne zamjenjuje izvorne klinicke dokumente.

## 2. Snapshot vs AuditLog

Snapshot:

- biljezi sadrzaj previewa u odredjenom trenutku
- moze biti user-triggered u buducnosti
- domain-specific je za Clinical Readiness Preview

AuditLog:

- biljezi system/user action
- odgovara na pitanje tko je sto napravio i kada
- ostaje genericka audit infrastruktura

Buduce kreiranje snapshota moze napisati audit dogadjaj, ali snapshot ne zamjenjuje AuditLog.

AuditLog cuva trag akcije. Snapshot cuva sadrzaj prikaza koji je ta akcija mozda zabiljezila.

## 3. Snapshot vs Outcome Evidence

Snapshot nije Outcome Evidence.

Outcome Evidence bi dokumentirao sto se dogodilo nakon akcije ili postupka.

Snapshot samo dokumentira sto je preview prikazao prije odluke ili oko vremena odluke.

Primjer:

- Snapshot moze reci: preview je prikazao da postoji upozorenje o nepregledanom izvoru.
- Outcome Evidence bi kasnije mogao reci: postupak je izveden, rezultat je dokumentiran, odredjeni nalaz je pregledan.

B8 ne implementira Outcome Evidence.

## 4. Snapshot vs Clinical Decision

Snapshot nije lijecnicka odluka.

Ako ASTRA kasnije uvede potvrdu klinicke spremnosti, to mora imati zaseban governance model, audit pravila, uloge i jasnu potvrdu covjeka.

Snapshot ne smije znaciti:

- lijecnik je potvrdio readiness
- pacijent je spreman
- postupak smije poceti
- klinicki rizik je rijesen

Snapshot je zapis prikazanog stanja, ne zapis odgovornosti.

## 5. Snapshot vs Task

Snapshot ne stvara posao.

Readiness itemi zapisani u snapshotu nisu taskovi.

Ako buduci Task engine nastane, task mora imati vlastiti lifecycle, ownera, rok, status i audit. Snapshot ne smije automatski pretvarati upozorenja u zadatke.

B8 ne implementira Task engine.

## 6. Snapshot vs ClinicalDocument

Snapshot nije source document.

Snapshot moze referencirati pregledane ClinicalDocuments, ali nije sam po sebi klinicki dokaz i ne smije uci u Patient Clinical Knowledge kao izvor istine.

ClinicalDocument ostaje source object.

Patient Clinical Knowledge ostaje source-linked znanje iz pregledanih dokumenata.

Snapshot ostaje meta-zapis prikaza Clinical Readiness Previewa.

## 7. Required future guardrails

Buduca implementacija snapshota mora imati:

- eksplicitnu capture akciju
- preview-only disclaimer
- immutable spremljeni sadrzaj
- audit event za snapshot capture
- zabranu workflow blocka
- zabranu readiness clearancea
- zabranu task creationa
- zabranu production claima

Bez tih guardraila snapshot persistence ne smije uci u kod.
