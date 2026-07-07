# Program 1 Phase B12 - Snapshot Implementation Gate

Status: documentation-only implementation gate

## 1. Svrha

Ovaj dokument definira sto mora biti odluceno prije implementacije Clinical Readiness Snapshot persistencea, capture endpointa ili UI-ja.

Ovaj dokument ne implementira:

- migraciju
- model
- schema
- service
- endpoint
- frontend capture button
- snapshot history UI
- audit event
- permission enforcement
- RBAC seed

B12 implementation gate postoji zato da snapshot ne postane prerani clinical approval ili workflow engine shortcut.

## 2. Required before implementation

Prije implementacije moraju biti maintainer-approved:

- final table shape
- final index strategy
- final JSON payload fields
- final immutable payload rule
- final permission names
- permission seed strategy
- role mapping
- required reason semantics
- audit event names
- audit payload shape
- capture endpoint route
- idempotency behavior
- supersession behavior
- rollback strategy
- test plan
- UI disclaimer text
- history UI minimal fields

Ako bilo koja od ovih odluka ostane nejasna, implementacija mora stati.

## 3. Minimum future implementation sequence

Buduca implementacija treba ici u malim commitovima:

1. Migration only

   Dodati tablicu i indekse bez endpointa, UI-ja ili capture logike.

2. Model/schema only

   Dodati ORM model i response schema bez runtime capturea.

3. Service capture logic

   Implementirati server-side preview rebuild i immutable payload copy u service sloju.

4. Audit event integration

   Dodati `clinical_readiness_snapshot_captured` u istoj transakciji sa snapshot saveom.

5. Endpoint

   Dodati `POST /api/appointments/{appointment_id}/clinical-readiness-snapshots` tek nakon permission/reason/audit testova.

6. Frontend history display

   Prikazati read-only snapshot history prije capture buttona.

7. Capture button only after permission/reason UI

   Capture button smije doci tek kada UI moze prikupiti reason i jasno prikazati disclaimer.

8. Regression gate

   Dodati backend i frontend regression coverage za sve no-go granice.

## 4. Hard No-Go before implementation

Implementacija ne smije krenuti ako:

- permission model nije jasan
- audit payload nije jasan
- table immutability nije jasna
- reason requirement nije jasan
- snapshot moze biti zamijenjen za approval
- snapshot moze stvoriti task
- snapshot moze stvoriti Outcome Evidence
- snapshot moze promijeniti appointment status
- rollback rizik nije dokumentiran
- source-linked official knowledge pravila nisu zadrzana
- Patient Clinical Summary moze postati source of truth
- unreviewed AI moze uci kao official source

## 5. Required future tests

Buduca code faza mora imati testove za:

- unauthorized capture denied
- missing permission denied
- missing reason denied
- AI agent denied
- API key denied by default
- capture writes snapshot and audit in same transaction
- audit failure rolls back snapshot
- snapshot immutable
- supersession creates new snapshot or supersession marker without editing old payload
- preview load does not capture
- capture does not alter appointment status
- capture does not create Task
- capture does not create Outcome Evidence
- capture does not create ClinicalPlan
- capture does not create Episode
- capture does not use Patient Clinical Summary as source truth
- capture does not use unreviewed AI as official knowledge
- limitations remain visible
- open questions remain warnings, not tasks
- template version is stored in payload
- reason appears in snapshot history
- disclaimer appears in API/UI

## 6. UI implementation gate

Buduci UI ne smije dodati capture button dok ne postoje:

- backend permission enforcement
- reason modal/input
- clear preview-only disclaimer
- snapshot history read-only display
- audit event
- regression smoke coverage

UI mora izbjegavati label-e:

- "Odobri"
- "Pacijent spreman"
- "AI cleared"
- "Procedure approved"
- "Override"

Preporuceni label:

`Spremi snapshot previewa`

Preporuceni disclaimer:

`Snapshot je zapis preview prikaza, ne clinical approval.`

## 7. B12 implementation gate odluka

Prva buduca code faza smije biti samo usko ogranicena migracija ili migration draft.

Preporuceni sljedeci task:

`Program 1 Phase B13 - Snapshot Persistence Migration Draft`

B13 smije dodati DB migraciju samo ako ostane:

- bez endpointa
- bez frontend UI-ja
- bez capture buttona
- bez audit event implementationa ako nije dio iste odobrene faze
- bez Outcome Evidencea
- bez Task enginea
- bez overridea
- bez appointment status promjene
