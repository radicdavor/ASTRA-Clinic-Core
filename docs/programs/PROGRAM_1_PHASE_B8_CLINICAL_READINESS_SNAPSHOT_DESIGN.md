# Program 1 Phase B8 - Clinical Readiness Snapshot Design

Status: design-first, demo/pilot only

## 1. Svrha

B8 definira buduci koncept Clinical Readiness Snapshota prije implementacije.

Ovaj dokument je namjerno design-first. Ne uvodi:

- DB tablicu
- Alembic migraciju
- persistent snapshot
- Outcome Evidence
- enforcement
- klinicku odluku
- produkcijsko odobrenje

Svrha je unaprijed razjasniti sto bi buduci immutable zapis smio zabiljeziti, bez stvaranja lazne sigurnosti da je pacijent spreman, postupak odobren ili odluka donesena.

## 2. Definicija

Clinical Readiness Snapshot je buduci immutable zapis onoga sto je read-only Clinical Readiness Preview prikazao u odredenom trenutku.

Snapshot bi u buducnosti mogao zabiljeziti:

- appointment id
- patient id
- service id
- generated timestamp
- template key
- template label
- template version
- binding status
- preview status
- preview items
- limitations
- source warnings
- source references
- preview-only disclaimers

Snapshot ne smije znaciti:

- postupak je odobren
- pacijent je cleared
- lijecnik je potvrdio spremnost
- zadatak je dovrsen
- outcome je dokumentiran
- medicinska odluka je donesena
- klinicka smjernica je primijenjena

Snapshot je zapis prikaza, ne zapis odluke.

## 3. Zasto snapshot postoji

Buduci snapshot postoji radi:

- traceabilityja
- reprodukcije previewa koji je korisnik vidio
- demo/pilot evidencea
- debugiranja template ponasanja
- usporedbe promjena previewa kroz vrijeme
- buduce audit podrske

To je korisno jer je trenutni preview live prikaz. Ako se template, binding, source dokumenti ili ogranicenja promijene, korisnik kasnije vise ne moze jednostavno znati sto je tocno bilo prikazano u prethodnom trenutku.

## 4. Sto snapshot nije

Clinical Readiness Snapshot nije:

- zamjena za AuditLog
- Outcome Evidence
- ClinicalDocument
- Patient Clinical Summary
- Task
- Episode closure
- consent
- medical note
- patient instruction
- production readiness

Snapshot ne smije postati novi izvor klinicke istine. On moze upucivati na izvore, ali ne zamjenjuje pregledane ClinicalDocuments ni source-linked Patient Clinical Knowledge.

## 5. Future snapshot shape

Buduci konceptualni oblik snapshota moze ukljuciti:

- `snapshot_id`
- `appointment_id`
- `patient_id`
- `service_id`
- `created_at`
- `created_by_user_id`
- `is_preview`
- `status`
- `summary`
- `template_key`
- `template_label`
- `template_version`
- `template_binding_status`
- `template_binding_warning`
- `items_json`
- `limitations_json`
- `source_warnings_json`
- `source_refs_json`
- `disclaimer`
- `schema_version`

B8 ne implementira DB model, ORM model, API endpoint ili migraciju za ova polja.

## 6. Snapshot lifecycle

Buduci lifecycle trebao bi biti:

1. Preview se generira live.
2. Korisnik kasnije moze eksplicitno zabiljeziti snapshot.
3. Snapshot je immutable.
4. Snapshot se moze pregledati.
5. Kasniji snapshot moze supersedeati raniji snapshot.
6. Snapshot se ne moze uredjivati.
7. Snapshot ne moze clearati readiness.
8. Snapshot ne moze odobriti postupak.

Ovaj lifecycle se sada ne implementira.

B8 samo postavlja granicu: prije persistencea treba znati sto se sprema, zasto se sprema i sto taj zapis ne smije tvrditi.
