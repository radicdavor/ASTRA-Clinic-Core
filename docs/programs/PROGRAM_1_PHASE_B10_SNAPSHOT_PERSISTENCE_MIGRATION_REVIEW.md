# Program 1 Phase B10 - Snapshot Persistence Migration Review

Status: documentation-only migration review

## 1. Svrha

B10 pregledava buducu migraciju za persistent Clinical Readiness Snapshot prije pisanja koda ili Alembic migracije.

Ovaj dokument ne implementira:

- backend model
- frontend UI
- Alembic migraciju
- snapshot capture endpoint
- snapshot history UI
- runtime persistence
- audit event
- Outcome Evidence
- Task engine
- override
- promjenu statusa termina

Svrha je provjeriti tablicu, nazive, indekse, JSON payload, rollback i sigurnosne granice prije bilo kakve implementacije.

## 2. Predlozeni DB model

Predlozeni buduci ORM model:

`ClinicalReadinessSnapshot`

Predlozena buduca tablica:

`clinical_readiness_snapshots`

Model predstavlja immutable kopiju onoga sto je `Clinical Readiness Preview` prikazao u trenutku eksplicitnog capturea.

Model ne predstavlja:

- clinical approval
- procedure allowed decision
- physician confirmation
- Outcome Evidence
- Task
- override
- appointment status
- consent
- medical note

## 3. Obavezna polja

Minimalna obavezna polja za buducu migraciju:

- `id`
- `appointment_id`
- `patient_id`
- `service_id`
- `created_at`
- `created_by_user_id`
- `schema_version`
- `preview_generated_at`
- `preview_status`
- `preview_summary`
- `template_key`
- `template_label`
- `template_version`
- `template_binding_status`
- `is_preview_snapshot`
- `items_json`
- `limitations_json`
- `source_warnings_json`
- `source_refs_json`
- `disclaimer`
- `snapshot_reason`

Opcionalna polja:

- `template_binding_warning`
- `superseded_by_snapshot_id`
- `superseded_at`
- `superseded_reason`

Preporuka:

`is_preview_snapshot` mora biti `true` u prvoj verziji kako bi bilo jasno da snapshot nije final clinical readiness decision.

## 4. Foreign key odnosi

Predlozeni FK odnosi:

- `appointment_id -> appointments.id`
- `patient_id -> patients.id`
- `service_id -> services.id`
- `created_by_user_id -> users.id`
- `superseded_by_snapshot_id -> clinical_readiness_snapshots.id`

Važna pravila:

- `appointment_id`, `patient_id` i `service_id` se spremaju kao explicit references radi citljivosti i queryja.
- `patient_id` i `service_id` moraju odgovarati appointment kontekstu u trenutku capturea.
- Buduci capture service mora validirati da appointment ima pacijenta i uslugu prije capturea.
- `superseded_by_snapshot_id` smije pokazivati samo na noviji snapshot za isti appointment.

Brisanje povezanih objekata ne smije kaskadno obrisati snapshot bez zasebne odluke maintainera.

## 5. JSON snapshot payload odluka

Snapshot mora spremiti copied JSON payload:

- `items_json`
- `limitations_json`
- `source_warnings_json`
- `source_refs_json`

Odluka:

Payload se sprema kao immutable kopija preview response sadrzaja, a ne kao podatak koji se kasnije recomputea.

Razlog:

- template content se moze promijeniti
- template version se moze povuci
- service binding se moze promijeniti
- reviewed ClinicalDocuments se mogu promijeniti
- Open Questions se mogu promijeniti
- Patient Clinical Knowledge se moze osvjeziti

Ako se snapshot recomputea, prestaje biti povijesni zapis onoga sto je korisnik vidio.

## 6. Indeksiranje

Predlozeni indeksi:

- `appointment_id`
- `patient_id`
- `service_id`
- `created_at`
- `created_by_user_id`
- `template_key`
- `template_version`
- `preview_status`
- `superseded_by_snapshot_id`

Potencijalni kompozitni indeksi:

- `(appointment_id, created_at)`
- `(patient_id, created_at)`
- `(template_key, template_version)`

JSON payload ne treba indeksirati u prvoj verziji.

Razlog:

Prva verzija snapshot persistencea treba podrzati pregled povijesti, traceability i audit, ne analitiku nad JSON itemima.

## 7. Rollback strategija

Prije migracije treba definirati rollback:

1. Ako migracija samo dodaje tablicu i nema podataka, rollback moze dropati tablicu.
2. Ako snapshot podaci postoje, rollback ne smije tiho obrisati auditabilnu povijest bez maintainer odluke.
3. Prije rollbacka treba exportati snapshot zapise ako su nastali u demo/pilot okruzenju.
4. Audit event names moraju ostati citljivi i ako snapshot tablica bude uklonjena.
5. Rollback ne smije mijenjati appointment status, ClinicalDocument, ClinicalPlan ili Patient Clinical Summary.

Preporuka:

Prva implementacija mora imati feature flag ili runtime guard koji omogucuje iskljucenje capture endpointa bez rollbacka tablice.

## 8. Migracijski rizici

Glavni rizici:

- snapshot tablica moze izgledati kao klinicki dokaz ako se lose nazove ili prikaze
- JSON payload moze narasti ako se nekontrolirano sprema cijeli preview response
- FK prema appointmentu moze zbuniti ako se appointment kasnije promijeni
- supersession moze biti pogresno shvacen kao brisanje starog zapisa
- audit event i snapshot content mogu divergirirati
- preview-only disclaimer moze biti izostavljen
- netko moze pokusati koristiti snapshot kao Outcome Evidence
- migration rollback moze obrisati vazan pilot evidence bez odluke

Mitigacije:

- naziv tablice ostaje `clinical_readiness_snapshots`
- payload polja su jasna i preview-only
- `disclaimer` je obavezan
- `is_preview_snapshot` je obavezan
- snapshot capture pise audit event u buducem tasku
- regression gate mora dokazati da nema taska, Outcome Evidencea, overridea ili appointment status promjene

## 9. Zasto nema recomputea

Snapshot ne smije recomputeati povijesni sadrzaj jer mora odgovoriti na pitanje:

`Sto je korisnik vidio u trenutku capturea?`

Ne smije odgovoriti na pitanje:

`Sto bi sustav danas prikazao za isti appointment?`

Ta dva odgovora mogu biti razlicita ako se promijene:

- template
- template version
- binding
- reviewed sources
- open questions
- limitations
- service metadata

Snapshot je povijesni zapis prikaza, ne zivi clinical readiness calculation.

## 10. Sigurnosne granice

Snapshot ne znaci:

- clinical approval
- pacijent je spreman
- postupak je dopusten
- lijecnik je potvrdio sva upozorenja
- readiness je clearan
- override je napravljen

Snapshot ne stvara:

- task
- Outcome Evidence
- ClinicalPlan
- ClinicalEpisode
- consent
- medical note
- promjenu appointment statusa

Snapshot samo sprema preview prikaz uz razlog capturea.

## 11. Audit implikacije

Buduća migracija sama po sebi ne dodaje audit event.

Buduci capture endpoint mora pisati audit event:

`clinical_readiness_snapshot_captured`

Audit mora sadrzati:

- snapshot id
- appointment id
- patient id
- service id
- template key
- template version
- preview status
- capture reason
- actor

Audit event ne smije znaciti clinical approval.

Snapshot ne zamjenjuje AuditLog. AuditLog ne zamjenjuje snapshot content.

## 12. Otvorene odluke prije implementacije

Prije B10 migracije u kodu treba odluciti:

1. Tocan `schema_version` format.
2. Hoce li `patient_id` i `service_id` biti not-null u prvoj migraciji.
3. Hoce li `snapshot_reason` imati minimalnu duljinu.
4. Hoce li `disclaimer` biti generiran iz konstante ili spremljen iz responsea.
5. Treba li soft-delete ili samo supersession.
6. Treba li feature flag za capture endpoint.
7. Treba li zasebna permission, npr. `clinical_readiness.snapshots.write`.
8. Treba li view permission za snapshot history.
9. Treba li ograniciti capture na physician role u prvoj verziji.
10. Treba li retention policy za demo/pilot podatke prije real-data approvala.

## 13. B10 odluka

B10 preporuka:

Ne pisati Alembic migraciju dok se ne napravi zaseban endpoint design i dok maintainer ne potvrdi table shape, indekse, rollback i permission model.

Sljedeci korak:

`Program 1 Phase B11 - Snapshot Capture Endpoint Design`
