# Program 1 Phase B9 - Clinical Readiness Snapshot Lifecycle Governance

Status: design-only, no implementation

## 1. Svrha

Ovaj dokument definira buduci lifecycle i governance za Clinical Readiness Snapshot.

B9 ne implementira lifecycle state, endpoint, UI ili migraciju. Dokument samo postavlja pravila koja moraju postojati prije buduce implementacije.

## 2. Lifecycle

Buduca konceptualna stanja:

- no snapshot
- preview generated live
- snapshot captured
- snapshot viewed
- snapshot superseded
- snapshot retained

Ova stanja se ne implementiraju u B9.

Trenutni sustav ostaje u stanju:

`preview generated live`

uz metadata:

`snapshot_supported=false`

## 3. Capture action

Buduca capture akcija mora biti eksplicitna.

Mora zahtijevati:

- authenticated user
- reason
- appointment context
- generated preview content
- preview-only disclaimer

Capture ne smije biti automatski na page load.

Capture ne smije nastati samo zato sto je korisnik otvorio Appointment Workspace ili zato sto je API preview procitan.

Ako korisnik ne zna da sprema snapshot, snapshot se ne smije spremiti.

## 4. Supersession

Snapshot se ne smije uredjivati.

Ako novi preview treba biti zabiljezen:

1. kreira se novi snapshot
2. stari snapshot dobiva `superseded_by_snapshot_id`
3. biljezi se `superseded_at`
4. biljezi se `superseded_reason`

Supersession ne smije obrisati povijesni zapis.

Stari snapshot ostaje citljiv jer predstavlja sto je korisnik tada vidio.

## 5. Roles

Konceptualne uloge:

- physician moze captureati clinical-context snapshot
- nurse/admin moze captureati operational preview snapshot samo ako buduci governance to dopusti
- AI ne smije captureati snapshot
- system ne smije auto-captureati snapshot bez eksplicitnog buduceg pravila

Default pravilo:

Ako nije jasno tko smije captureati snapshot, capture nije dopusten.

## 6. Retention

Retention se u B9 definira samo konceptualno.

Buduci retention model mora odgovoriti:

- koliko dugo se snapshot cuva u demo/pilot okruzenju
- kako se oznacava superseded snapshot
- tko smije pregledati povijesni snapshot
- kako se snapshot tretira prije real-data approvala
- kako se backup/restore odnosi prema immutable snapshotima

B9 ne implementira retention.

## 7. No-Go governance

Buduca implementacija ne smije dopustiti:

- automatic capture on preview load
- silent overwrite
- editing snapshot payload
- deleting snapshot for convenience
- using snapshot as procedure approval
- using snapshot as Outcome Evidence
- using snapshot as Task completion
- using snapshot as consent
- using snapshot as medical note
- using snapshot as patient instruction

Snapshot mora ostati zapis prikaza.

Odluka, ishod, task i klijentska/pacijentska komunikacija moraju imati zasebne modele i zasebnu ljudsku odgovornost.
