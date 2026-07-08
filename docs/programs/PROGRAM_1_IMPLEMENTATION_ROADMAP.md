# Program 1 - Implementation Roadmap

Status: arhitektonski roadmap, bez implementacije u ovom zadatku

## 1. Svrha

Ovaj roadmap prevodi Program 1 - ASTRA Clinical Workflow u redoslijed buduće implementacije.

Roadmap ne ovlašćuje automatsku implementaciju svih stavki.

Buduće implementacijske faze moraju koristiti kanonski rječnik definiran u `PROGRAM_1_GLOSSARY.md` i mapiranje postojećeg sustava iz `PROGRAM_1_DOMAIN_OBJECT_MAPPING.md`.

Prije svakog sprinta treba ponovno provjeriti:

- je li promjena u skladu s Architecture Bible
- povećava li jednostavnost ili samo broj funkcija
- čuva li Patient Clinical Knowledge Layer kao primarni smjer
- uvodi li stvarne podatke, compliance tvrdnje ili medicinsku automatizaciju
- može li se auditirati

## 2. Neupitne Granice

U Programu 1 ne smije se:

- omogućiti unos stvarnih pacijentovih podataka u demo/pilot režimu
- tvrditi da je ASTRA certificirani EMR
- tvrditi da je ASTRA medicinski uređaj
- implementirati stvarnu hrvatsku fiskalizaciju
- učiniti Episode Engine primarnim workflowom
- učiniti appointment epizodu obveznom
- uvesti autonomni AI decision making
- uvesti Workflow Engine prije stabilnog patient knowledge sloja
- uvesti nove kliničke module prije stabilnog shared core modela

## 3. Faza 0 - Dokumentacijsko Usklađenje

Cilj:

- Program 1 dokumenti postoje
- README ih povezuje
- Episode Engine je dokumentiran kao deferred/experimental gdje je relevantno
- Patient Clinical Knowledge Layer ostaje primarni smjer

Ishod:

- tim zna koji je klinički operativni model
- nema novih modela, migracija, API-ja ili UI komponenti

## 4. Faza 1 - Patient Knowledge Stabilization

Cilj:

- pacijentov workspace prvo odgovara na pitanje: što znamo o pacijentu
- svaki sažetak ima izvore
- nepregledani dokumenti su jasno vidljivi
- otvorena pitanja su odvojena od zadataka

Budući scope:

- poboljšati ClinicalDocument status model
- učvrstiti physician review tok
- prikazati source badges u svim kliničkim sažecima
- dodati jasnije stanje `awaiting_review`
- dodati readiness upozorenje za nepregledane dokumente

Izvan scopea:

- OCR engine
- stvarni AI provider
- workflow automations
- epizodni engine kao primarni tok

Phase A planning reference: `PROGRAM_1_PHASE_A_PATIENT_KNOWLEDGE_STABILIZATION_PLAN.md`.

Phase A closure update:

- Phase A je zatvorena uz guardrails kroz `PROGRAM_1_PHASE_A_CLOSURE_REPORT.md`
- Patient Knowledge Regression Gate je uspostavljen
- backend route modularization pass je zavrsen, ukljucujuci A16, A17 i A18 split
- `core.py` je povucen kao aktivni backend route modul
- Phase A ne odobrava produkciju, stvarne podatke pacijenata ili certificirani EMR / medical-device status
- immediate Task engine, Workflow Engine, Episode-Based Care kao primarni workflow i real AI/OCR ostaju No-Go

Preporuka nakon Phase A:

`Program 1 Phase B0 - Clinical Readiness Gate Operating Model`

Phase B treba poceti kao dokumentacijski operating model, ne kao implementacija.

Phase B0 update:

- Clinical Readiness Gate operating model je dokumentiran kao patient/service/procedure-specific gate
- Operational Readiness i Clinical Readiness moraju ostati odvojeni
- B0 je documentation-only i ne uvodi backend, frontend, API, DB model ili UI
- prva buduca implementacija, ako bude odobrena, treba biti read-only preview u Appointment Workspaceu
- preporuceni sljedeci task je `Program 1 Phase B1 - Clinical Readiness Vocabulary and Domain Mapping`

Phase B1 update:

- Clinical Readiness vocabulary je zakljucan kroz `PROGRAM_1_PHASE_B1_CLINICAL_READINESS_VOCABULARY.md`
- domain mapping je definiran kroz `PROGRAM_1_PHASE_B1_CLINICAL_READINESS_DOMAIN_MAPPING.md`
- status, severity, category i item taxonomy definirani su kroz `PROGRAM_1_PHASE_B1_CLINICAL_READINESS_STATUS_TAXONOMY.md`
- source/evidence pravila definirana su kroz `PROGRAM_1_PHASE_B1_CLINICAL_READINESS_SOURCE_EVIDENCE_MAPPING.md`
- B1 je documentation-only i ne uvodi implementaciju
- preporuceni sljedeci task je `Program 1 Phase B2 - Clinical Readiness API and UI Contract`
- B2 takoder treba poceti kao contract/design, ne kao code implementation

Phase B2 update:

- Clinical Readiness API contract je dokumentiran kroz `PROGRAM_1_PHASE_B2_CLINICAL_READINESS_API_CONTRACT.md`
- Clinical Readiness UI contract je dokumentiran kroz `PROGRAM_1_PHASE_B2_CLINICAL_READINESS_UI_CONTRACT.md`
- preview data contract je dokumentiran kroz `PROGRAM_1_PHASE_B2_CLINICAL_READINESS_PREVIEW_DATA_CONTRACT.md`
- safety/regression contract je dokumentiran kroz `PROGRAM_1_PHASE_B2_CLINICAL_READINESS_SAFETY_REGRESSION_CONTRACT.md`
- B2 je documentation-only API/UI contract i ne uvodi endpoint, UI, model ili migraciju
- buduca prva code faza, ako bude odobrena, treba biti `Program 1 Phase B3 - Clinical Readiness Read-Only Preview Prototype`
- B3 mora ostati demo/pilot-only, non-blocking i bez task/override/AI-clear ponasanja

Phase B3 update:

- read-only appointment-scoped preview endpoint je implementiran
- deterministic preview service je implementiran
- Appointment Workspace prikazuje `Klinicka spremnost - preview`
- regression tests i smoke coverage cuvaju non-blocking/read-only granice
- B3 ne uvodi enforcement, taskove, override, AI clearance, production claims, DB model ili migraciju
- preporuceni sljedeci task je `Program 1 Phase B4 - Clinical Readiness Template Design`

Phase B4 update:

- Clinical Readiness template design je dokumentiran kroz `PROGRAM_1_PHASE_B4_CLINICAL_READINESS_TEMPLATE_DESIGN.md`
- staticne demo/pilot template definicije postoje u backend service sloju
- preview koristi service-name matching i generic fallback
- template-generated itemi su preview-only i ne provode workflow blokade
- regression coverage cuva da templatei ne mijenjaju appointment status, ne stvaraju taskove, epizode ili ClinicalPlan i ne koriste unreviewed AI ili Patient Clinical Summary kao source truth
- B4 ne uvodi DB template model, template editor, override, enforcement, real AI/OCR, real patient data ili produkcijske tvrdnje
- preporuceni sljedeci task je `Program 1 Phase B5 - Clinical Readiness Template Binding Design`

Phase B5 update:

- Clinical Readiness template binding design je dokumentiran kroz `PROGRAM_1_PHASE_B5_CLINICAL_READINESS_TEMPLATE_BINDING_DESIGN.md`
- template governance model je dokumentiran kroz `PROGRAM_1_PHASE_B5_CLINICAL_READINESS_TEMPLATE_GOVERNANCE.md`
- preview response sada izlaže template selection metadata: `template_key`, `template_label`, `template_binding_status`, `template_binding_warning`
- Appointment Workspace prikazuje template label, binding status i binding warning
- runtime binding statusi ostaju samo `keyword_fallback` i `generic_fallback`
- B5 ne uvodi DB binding field, migraciju, template editor, explicit service binding persistence, enforcement ili override
- preporuceni sljedeci task je `Program 1 Phase B6 - Clinical Readiness Explicit Service Binding Prototype`

Phase B6 update:

- explicit service binding prototype je dokumentiran kroz `PROGRAM_1_PHASE_B6_EXPLICIT_SERVICE_BINDING_PROTOTYPE.md`
- staticna demo explicit service binding konfiguracija postoji u backend service sloju
- runtime selection sada koristi explicit demo binding prije keyword fallbacka
- preview response moze prikazati `template_binding_status="explicit"`
- regression coverage cuva precedence, read-only ponasanje i zabranu workflow objekata
- B6 ne uvodi DB binding field, migraciju, template editor, persistent binding, enforcement ili override
- preporuceni sljedeci task je `Program 1 Phase B7 - Clinical Readiness Template Versioning Design`

Phase B7 update:

- Clinical Readiness template versioning design je dokumentiran kroz `PROGRAM_1_PHASE_B7_CLINICAL_READINESS_TEMPLATE_VERSIONING_DESIGN.md`
- staticni demo template version metadata postoji u backend template definicijama
- preview response sada izlaže `template_version` i `template_version_warning`
- Appointment Workspace prikazuje verziju templatea
- regression coverage cuva da version metadata ne mijenja appointment status i ne stvara workflow objekte
- B7 ne uvodi DB versioning, migraciju, template editor, persistent snapshot ili enforcement
- preporuceni sljedeci task je `Program 1 Phase B8 - Clinical Readiness Snapshot Design`

Phase B8 update:

- Clinical Readiness snapshot design je dokumentiran kroz `PROGRAM_1_PHASE_B8_CLINICAL_READINESS_SNAPSHOT_DESIGN.md`
- granice izmedju snapshota, audita, outcome evidencea, taska i klinicke odluke dokumentirane su kroz `PROGRAM_1_PHASE_B8_CLINICAL_READINESS_SNAPSHOT_BOUNDARIES.md`
- preview response sada sadrzi `snapshot_supported`, `snapshot_status` i `snapshot_warning`
- Appointment Workspace prikazuje da snapshot nije implementiran i da se live preview ne sprema kao trajni zapis
- regression coverage cuva da preview read ne stvara snapshot, audit, task, epizodu, ClinicalPlan ili Outcome Evidence i ne mijenja appointment status
- B8 ne uvodi DB tablicu, migraciju, capture endpoint, snapshot history, persistence, enforcement ili override
- preporuceni sljedeci task je `Program 1 Phase B9 - Clinical Readiness Snapshot Persistence Design`

Phase B9 update:

- snapshot persistence model design je dokumentiran kroz `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_PERSISTENCE_MODEL.md`
- snapshot audit model design je dokumentiran kroz `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_AUDIT_MODEL.md`
- snapshot lifecycle governance design je dokumentiran kroz `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_LIFECYCLE_GOVERNANCE.md`
- snapshot future regression gate je dokumentiran kroz `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_REGRESSION_GATE.md`
- B9 je documentation-only i ne uvodi DB tablicu, migraciju, capture endpoint, history UI, audit evente, Outcome Evidence, enforcement ili override
- preporuceni sljedeci task je `Program 1 Phase B10 - Snapshot Persistence Migration Review`

Phase B10 update:

- snapshot persistence migration review je dokumentiran kroz `PROGRAM_1_PHASE_B10_SNAPSHOT_PERSISTENCE_MIGRATION_REVIEW.md`
- B10 definira predlozeni DB model `ClinicalReadinessSnapshot` i tablicu `clinical_readiness_snapshots`
- B10 potvrduje da snapshot mora spremiti immutable JSON kopiju preview sadrzaja i ne smije recomputeati povijesni prikaz
- B10 dokumentira FK odnose, indeksiranje, rollback strategiju, migracijske rizike, audit implikacije i otvorene odluke
- B10 je documentation-only i ne uvodi DB tablicu, migraciju, endpoint, runtime persistence, audit event, Outcome Evidence, task, override ili appointment status promjenu
- preporuceni sljedeci task je `Program 1 Phase B11 - Snapshot Capture Endpoint Design`

Phase B11 update:

- snapshot capture endpoint design je dokumentiran kroz `PROGRAM_1_PHASE_B11_SNAPSHOT_CAPTURE_ENDPOINT_DESIGN.md`
- B11 predlaze buduci endpoint `POST /api/appointments/{appointment_id}/clinical-readiness-snapshots`
- B11 definira tko smije captureati snapshot, ulazne parametre, response shape, error states, idempotency, transaction boundary, audit event i UI implikacije
- B11 potvrduje da capture sprema ono sto server-side preview prikaze u trenutku capturea i da ne radi clinical approval
- B11 je documentation-only i ne uvodi endpoint, backend kod, frontend kod, persistence, audit event, Outcome Evidence, task, override ili appointment status promjenu
- preporuceni sljedeci task je `Program 1 Phase B12 - Snapshot Permission and Audit Contract`

Phase B12 update:

- snapshot permission contract je dokumentiran kroz `PROGRAM_1_PHASE_B12_SNAPSHOT_PERMISSION_CONTRACT.md`
- snapshot audit payload contract je dokumentiran kroz `PROGRAM_1_PHASE_B12_SNAPSHOT_AUDIT_PAYLOAD_CONTRACT.md`
- permission/audit no-go matrix je dokumentirana kroz `PROGRAM_1_PHASE_B12_SNAPSHOT_PERMISSION_AUDIT_NO_GO_MATRIX.md`
- snapshot implementation gate je dokumentiran kroz `PROGRAM_1_PHASE_B12_SNAPSHOT_IMPLEMENTATION_GATE.md`
- B12 zakljucava da buduci snapshot capture mora biti permission-gated, reason-required, auditiran, atomican i preview-only
- B12 potvrduje default deny za AI agente, system job i API key capture
- B12 je documentation-only i ne uvodi backend kod, frontend kod, RBAC seed, DB migraciju, endpoint, audit runtime, snapshot history UI, Outcome Evidence, task, override ili appointment status promjenu
- preporuceni sljedeci task je `Program 1 Phase B13 - Snapshot Persistence Migration Draft`

Phase B13 update:

- SQLAlchemy model `ClinicalReadinessSnapshot` je dodan
- Alembic migracija `0014_clinical_readiness_snapshots.py` dodaje tablicu `clinical_readiness_snapshots`
- persistence-shape regression coverage dokazuje da JSON payload moze biti spremljen i da preview GET ne stvara snapshot
- B13 uvodi samo DB persistence shape; runtime preview ostaje read-only i non-persistent
- B13 ne uvodi capture service, capture endpoint, frontend UI, permission enforcement, audit write, Outcome Evidence, Task engine, override ili appointment status promjenu
- preporuceni sljedeci task je `Program 1 Phase B14 - Snapshot Capture Service Prototype`

Phase B14 update:

- interni capture service je dodan kroz `backend/app/services/clinical_readiness_snapshots.py`
- service rebuilda server-side Clinical Readiness Preview i sprema immutable copied payload u `clinical_readiness_snapshots`
- service pise audit event `clinical_readiness_snapshot_captured`
- snapshot save i audit write su atomicni u service funkciji
- regression coverage cuva reason/actor requirement, payload copy, audit payload, rollback na audit failure i zabranu workflow side effecta
- B14 ne uvodi capture endpoint, frontend UI, capture button, snapshot history UI, route-level permission enforcement, Outcome Evidence, Task engine, override ili appointment status promjenu
- idempotency persistence ostaje deferred jer B13 nije dodao idempotency storage
- preporuceni sljedeci task je `Program 1 Phase B15 - Snapshot Capture Endpoint Prototype`

Phase B15 update:

- capture request/response schemas su dodane
- endpoint `POST /api/appointments/{appointment_id}/clinical-readiness-snapshots` je dodan
- endpoint zahtijeva `clinical_readiness.snapshots.write`
- endpoint zahtijeva non-empty reason
- endpoint odbija API key capture
- endpoint poziva B14 service i time rebuilda server-side preview, sprema snapshot i pise audit event
- endpoint regression coverage cuva auth, permission, reason, response safety, audit event i zabranu workflow side effecta
- B15 ne uvodi frontend capture UI, capture button, snapshot history UI, Outcome Evidence, Task engine, override, patient messaging ili appointment status promjenu
- preporuceni sljedeci task je `Program 1 Phase B16 - Snapshot History Read API Prototype`

Phase B16 update:

- snapshot history response schemas su dodane
- endpoint `GET /api/appointments/{appointment_id}/clinical-readiness-snapshots` je dodan
- endpoint zahtijeva `clinical_readiness.snapshots.read`
- history list je appointment-scoped, newest-first i summary-only
- history read ne pise audit by default i ne stvara snapshot
- regression coverage cuva auth, read permission, appointment scope, sorting, warning, response safety i zabranu workflow side effecta
- B16 ne uvodi frontend history UI, capture button, detail endpoint, edit/delete, supersession UI, Outcome Evidence, Task engine, override ili appointment status promjenu
- preporuceni sljedeci task je `Program 1 Phase B17 - Snapshot History UI Read-Only Surface`

Phase B17 update:

- frontend snapshot history tipovi su dodani
- API client read metoda `getClinicalReadinessSnapshotHistory` koristi postojeci B16 endpoint
- Appointment Workspace prikazuje read-only sekciju `Povijest snapshotova klinicke spremnosti`
- history UI ima non-blocking error state i empty state
- smoke coverage cuva da read-only history surface postoji i da nema capture/write/approval kontrola
- B17 ne uvodi capture button, reason modal, frontend POST/capture action, snapshot detail UI, supersession UI, edit/delete, Outcome Evidence, Task engine, override, appointment status promjenu, clinical approval, patient messaging, real AI/OCR ili real patient data
- preporuceni sljedeci task je `Program 1 Phase B18 - Snapshot Capture UI Reason Modal`

Phase B18 update:

- frontend capture request/response tipovi su dodani
- API client metoda `captureClinicalReadinessSnapshot` koristi postojeci B15 endpoint
- Appointment Workspace ima sigurni capture button `Spremi snapshot previewa`
- capture modal zahtijeva razlog i blokira prazan submit
- uspjesan capture zatvara modal, prikazuje poruku i osvjezava snapshot history
- permission error prikazuje poruku bez skrivanja history sekcije
- smoke coverage cuva capture label, modal, reason validation i zabranu approval/clearance/task signala
- B18 ne uvodi clinical approval, readiness clearance, override, Outcome Evidence, Task engine, appointment status change, patient messaging, snapshot edit/delete, supersession UI, production governance, real AI/OCR ili real patient data
- preporuceni sljedeci task je `Program 1 Phase B19 - Snapshot Detail Read-Only View`

Phase B19 update:

- backend snapshot detail response schema je dodana
- endpoint `GET /api/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}` je dodan
- endpoint zahtijeva `clinical_readiness.snapshots.read`
- endpoint provjerava appointment scope i vraca full copied snapshot payload
- frontend client i tip za snapshot detail su dodani
- Appointment Workspace prikazuje read-only detail panel za snapshot history item
- regression coverage cuva auth, permission, appointment scope, full copied payload, read-only side effects i zabranu approval/clearance polja
- B19 ne uvodi snapshot edit/delete, supersession, approval, clearance, override, Outcome Evidence, Task engine, appointment status change, patient messaging, production governance, real AI/OCR ili real patient data
- preporuceni sljedeci task je `Program 1 Phase B20 - Snapshot Idempotency and Duplicate-Capture Guard`

Phase B20 update:

- snapshot idempotency persistence columns su dodane
- Alembic migracija `0015_snapshot_idempotency.py` dodaje key/fingerprint i unique appointment/user/key constraint
- capture service normalizira key i racuna fingerprint iz appointmenta, usera, reasona i schema versiona
- isti key/fingerprint vraca postojeci snapshot bez drugog audit eventa
- isti key s drugim fingerprintom vraca conflict
- frontend generira i salje idempotency key kroz reason modal
- regression coverage cuva duplicate-capture guard i workflow side-effect granice
- B20 ne uvodi supersession, edit/delete, approval, clearance, override, Outcome Evidence, Task engine, appointment status change, patient messaging ili production governance
- preporuceni sljedeci task je `Program 1 Phase B21 - Snapshot Canonical Disclaimer and Immutability Hardening`

Phase B21 update:

- canonical disclaimer and immutability rules su dokumentirani
- frontend vise ne radi ad-hoc rewrite server disclaimer teksta
- Appointment Workspace prikazuje spremljeni disclaimer iz snapshota
- regression coverage cuva da update/delete/supersede rute ne postoje
- regression coverage cuva da detail/history read ne mutira snapshot payload
- regression coverage cuva da novi capture stvara novi row umjesto updatea postojeceg payload
- B21 ne uvodi supersession endpoint/UI, edit snapshot, delete snapshot, approval, clearance, override, Outcome Evidence, Task engine ili appointment status change
- preporuceni sljedeci task je `Program 1 Phase B22 - Snapshot Supersession Contract`

Phase B22 update:

- snapshot supersession contract je dokumentiran
- snapshot supersession audit contract je dokumentiran
- snapshot supersession no-go matrix je dokumentiran
- B22 je documentation-only
- B22 ne uvodi backend kod, frontend kod, endpoint, service, DB schema change, supersession UI, edit/delete, approval, clearance, override, Outcome Evidence, Task engine ili appointment status change
- preporuceni sljedeci task je `Program 1 Phase B23 - Snapshot Supersession Service Prototype`

Phase B23 update:

- capture internali su refactorirani u caller-owned transaction helper bez promjene capture endpoint ponasanja
- interni service `supersede_clinical_readiness_snapshot(...)` je dodan
- supersession service kreira novi server-side preview snapshot, oznacava stari snapshot kao zamijenjen i pise audit event u jednoj transakciji
- audit event `clinical_readiness_snapshot_superseded` biljezi old/new snapshot id, appointment, patient, service, actor, reason, template metadata i preview statuse
- stari snapshot payload ostaje nepromijenjen; mijenjaju se samo supersession metadata polja
- regression coverage cuva reason/actor requirement, appointment scope, already-superseded rejection, rollback na audit failure, history/detail read ponasanje i zabranu workflow side effecta
- B23 ne uvodi supersession endpoint, frontend UI, supersession button, edit/delete, approval, clearance, override, Outcome Evidence, Task engine, appointment status change ili patient messaging
- preporuceni sljedeci task je `Program 1 Phase B24 - Snapshot Supersession Endpoint Prototype`

Phase B24 update:

- supersession request/response schema su dodane
- endpoint `POST /api/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}/supersede` je dodan
- endpoint zahtijeva `clinical_readiness.snapshots.supersede`
- API key supersession je odbijen by default
- admin i physician dobivaju supersede permission u seed modelu; nurse i receptionist ne
- endpoint regression coverage cuva auth, permission, reason, appointment scope, already-superseded conflict, audit i zabranu workflow side effecta
- B24 ne uvodi frontend supersession UI, supersession button, edit/delete, approval, clearance, override, Outcome Evidence, Task engine, appointment status change ili patient messaging
- preporuceni sljedeci task je `Program 1 Phase B25 - Snapshot Supersession UI Reason Modal`

Phase B25 update:

- frontend supersession tipovi i API client metoda su dodani
- Appointment Workspace snapshot detail panel ima reason-required supersession modal
- UI label koristi safe wording: `Spremi novi snapshot i oznaci ovaj kao zamijenjen`
- uspjesan supersession osvjezava snapshot history i otvoreni detail panel
- permission error prikazuje korisniku da nema dozvolu za zamjenu snapshotova
- smoke coverage cuva safe label, modal, reason field i zabranu edit/delete/approval/clearance/task signala
- B25 ne uvodi edit/delete, approval, clearance, override, Outcome Evidence, Task engine, appointment status change ili patient messaging
- preporuceni sljedeci task je `Program 1 Phase B26 - Snapshot Governance and Safety Label Stabilization`

Phase B26 update:

- snapshot governance stabilization rules su dokumentirani
- Appointment Workspace snapshot helper tekstovi naglasavaju da snapshot nije klinicka odluka ni odobrenje postupka
- active/superseded UI labeli su stabilizirani kao `Nije zamijenjen` i `Zamijenjen novijim preview zapisom`
- smoke coverage cuva safe label presence i forbidden wording absence
- B26 ne uvodi nove runtime akcije, edit/delete, approval, clearance, override, Outcome Evidence, Task engine, appointment status change ili patient messaging
- preporuceni sljedeci task je `Program 1 Phase B27 - Snapshot End-to-End Regression Hardening`

Phase B27 update:

- end-to-end backend regresija pokriva preview -> capture -> history -> detail -> idempotent retry -> supersession -> history/detail read
- permission matrix regresija cuva read/write/supersede razdvajanje i odbijanje API key runtime write/supersede akcija
- frontend smoke dodatno cuva preview/history/detail/capture/supersession safe wording
- B27 ne uvodi nove endpointove, UI akcije, edit/delete, approval, clearance, override, Outcome Evidence, Task engine, appointment status change ili patient messaging
- preporuceni sljedeci task je `Program 1 Phase B28 - Program 1 Phase B Snapshot Closure Gate`

Phase B28 update:

- Clinical Readiness Snapshot subphase je zatvoren closure reportom
- go/no-go matrica formalno odvaja demo/pilot use od real-data, production i clinical enforcement no-go statusa
- next-step decision brief preporucuje `Program 1 Phase B29 - Snapshot Production Risk Hardening`
- B28 je documentation-only; ne uvodi backend/frontend runtime promjene
- Clinical Readiness enforcement se ne pokrece dok production risk hardening nije razjasnjen

Phase B29 update:

- production risk hardening plan je dokumentiran
- DB immutability trigger design je dokumentiran
- B29 ostaje documentation-only i ne mijenja runtime ponasanje
- recommended next task je `Program 1 Phase B30 - Snapshot DB Immutability Trigger Prototype`

Phase B30 update:

- dodana je migracija `0016_snapshot_db_immutability`
- `clinical_readiness_snapshots` dobiva DB-level update/delete invariant za protected snapshot content
- narrow first-time additive supersession metadata transition ostaje dozvoljen
- direct payload, capture reason, appointment/patient reassignment, supersession reassignment i delete scenariji su pokriveni regresijskim testovima
- B30 ne uvodi nove endpointove, frontend kontrole, approval, clearance, override, Outcome Evidence, Task engine, appointment status change ili patient messaging
- recommended next task je `Program 1 Phase B31 - Snapshot Audit Review and Retention Runbook`

Phase B31 update:

- dodan je Snapshot Audit Review and Retention Runbook
- dokumentirani su capture i supersession audit eventi
- audit je eksplicitno odvojen od Outcome Evidence koncepta
- retention/export/restore pretpostavke ostaju demo/pilot only
- B31 ne uvodi runtime promjene
- recommended next task je `Program 1 Phase B32 - Snapshot Audit Payload Stabilization`

Phase B32 update:

- capture audit payload shape je regresijski zakljucan
- supersession audit payload shape je regresijski zakljucan
- dodani su neklinicki review metadata: service name, preview summary i template label polja
- testovi potvrduju da payload ne sadrzi approval/clearance/override/outcome/task semantiku
- B32 ne uvodi export endpoint, Outcome Evidence, Task engine, appointment status change ili patient messaging
- recommended next task je `Program 1 Phase B33 - Snapshot Audit Export Contract`

Phase B33 update:

- snapshot audit export contract je dokumentiran
- postojece read-only audit pattern-e treba preferirati prije novog endpointa
- export ostaje demo/pilot only i ne predstavlja clinical decision export
- B33 ne uvodi runtime promjene
- recommended next task je `Program 1 Phase B34 - Snapshot Backup and Restore Consistency Runbook`

Phase B34 update:

- backup/restore consistency runbook je dokumentiran
- pokriveni su snapshot row, audit row, supersession relationship, idempotency metadata i DB trigger validation
- restore validation checklist ostaje demo/pilot hardening, ne production approval
- B34 ne uvodi runtime promjene
- recommended next task je `Program 1 Phase B35 - Snapshot Restore Validation Regression`

Phase B35 update:

- dodana je restore-consistency regresija bez stvarnog dump/restore workflowa
- test provjerava snapshot, supersession, audit reference, idempotency metadata i DB invariant nakon simuliranog restore scenarija
- B35 ne uvodi endpoint, frontend UI, approval, clearance, Outcome Evidence ili Task engine
- recommended next task je `Program 1 Phase B36 - Snapshot Permission UX and Error Wording Review`

Phase B36 update:

- stabilizirani su capture/supersession permission i helper tekstovi
- UI naglasava da je snapshot saved preview record, nije klinicko odobrenje i ne mijenja termin
- smoke test cuva safe wording i forbidden wording absence
- B36 ne uvodi nove UI akcije ili backend ponasanje
- recommended next task je `Program 1 Phase B37 - Snapshot CI Gate Documentation and Script Review`

Phase B37 update:

- dokumentiran je Snapshot CI Gate
- CI workflow sada eksplicitno vrti `tests/test_clinical_readiness_snapshots.py` prije punog backend suitea
- gate cuva preview/capture/history/detail/idempotency/supersession/DB immutability regresije
- B37 ne uvodi runtime ponasanje
- recommended next task je `Program 1 Phase B38 - Snapshot Legal/Compliance Disclaimer Review`

Phase B38 update:

- snapshot disclaimer/legal wording review je dokumentiran
- definirani su required disclaimer meaning, safe wording i forbidden wording
- potvrdeno je da physician remains responsible i real patient data ostaje no-go
- B38 ne uvodi runtime promjene
- recommended next task je `Program 1 Phase B39 - Snapshot Real-Data No-Go Checklist`

Phase B39 update:

- snapshot real-data no-go checklist je dokumentiran
- checklist pokriva GDPR/DPIA, access control, audit retention, backup/restore, security, training, legal wording, data minimization, incident response i maintainer approval
- B39 ne omogucuje real patient data niti production deployment
- recommended next task je `Program 1 Phase B40 - Snapshot Production Governance Closure Matrix`

Phase B40 update:

- snapshot production governance closure matrix objedinjuje B29-B39
- matrica potvrduje demo/pilot allowed with guardrails, real data no-go, production no-go i clinical enforcement no-go
- B40 ne uvodi runtime promjene
- recommended next task je `Program 1 Phase B41 - Program 1 Phase B Snapshot Hardening Closure`

Phase B41 update:

- B31-B41 snapshot hardening closure report je dodan
- zatvoreni su audit/retention/export/restore/governance hardening dokumenti
- runtime promjene ostaju hardening-only: audit payload metadata, UI wording i CI targeted gate
- real data, production i clinical enforcement ostaju no-go
- recommended next task je `Program 1 Phase C0 - Clinical Readiness Enforcement Readiness Design`

## 5. Faza 2 - Findings Lifecycle Foundation

Cilj:

- svaki nalaz ima lifecycle
- nalaz može otvoriti pitanje
- pitanje se može pretvoriti u potvrđeni zadatak ili plan samo ljudskom potvrdom

Budući scope:

- finding statusi
- veza nalaz -> izvor -> pacijent
- otvorena pitanja
- physician review događaji
- audit za AI prijedlog, prihvaćanje, izmjenu i odbijanje

Izvan scopea:

- automatsko zaključivanje dijagnoze
- automatsko zatvaranje skrbi
- slanje zaključaka pacijentu bez potvrde

## 6. Faza 3 - Clinical Readiness Gate

Cilj:

- za konkretan termin/proceduru vidjeti je li pacijent klinički spreman
- readiness nije compliance certifikat
- override je moguć samo uz razlog i audit

Budući scope:

- readiness statusi za pacijent/usluga kontekst
- gastroenterološki readiness template
- estetski readiness template
- prikaz warninga u Appointment Workspaceu

Izvan scopea:

- certificirani preoperative clearance
- automatsko odbijanje postupka bez ljudske odluke

## 7. Faza 4 - Medical Note And Patient Explanation

Cilj:

- svaki klinički čin može dati profesionalni zapis i razumljivo objašnjenje pacijentu
- AI može draftati, čovjek potvrđuje

Budući scope:

- Medical Note draft status
- Patient Explanation draft status
- review, edit, confirm, reject tok
- source-linked zaključci
- audit potvrde

Izvan scopea:

- automatsko slanje pacijentu
- autonomno generiranje službenog nalaza
- stvarni patient portal

## 8. Faza 5 - Episode-Based Care Reintroduction

Cilj:

- epizode se vraćaju tek nakon stabilnog source-linked knowledge sloja
- epizoda grupira poznate činjenice, nalaze, pitanja, termine i odluke
- epizoda ne stvara kliničku istinu sama po sebi

Budući scope:

- Episode kao opcijski organizacijski sloj
- veze prema pregledanim dokumentima
- veze prema otvorenim pitanjima
- vezi prema terminima i zadacima

Izvan scopea:

- obvezno povezivanje svakog termina s epizodom
- episode-first korisnički tok
- automatsko zatvaranje epizode

## 9. Faza 6 - Workflow Engine Tek Nakon Stabilizacije

Cilj:

- tek nakon stabilnih nalaza, pitanja, potvrda i audita može se razmišljati o workflow engineu

Preduvjeti:

- patient knowledge stabilan
- findings lifecycle stabilan
- audit dovoljno granularan
- ljudska potvrda jasno modelirana
- clinical readiness razumljiv korisnicima

Workflow Engine nije dio trenutnog zadatka.

## 10. Prioritetni Redoslijed

1. Dokumentacijsko usklađenje
2. Source-linked patient summary
3. ClinicalDocument review hardening
4. Open questions
5. Findings lifecycle statuses
6. Readiness warning for unreviewed clinical inputs
7. Medical Note / Patient Explanation drafts
8. Clinical Readiness Gate
9. Optional Episode grouping
10. Future Workflow Engine

## 11. Definition Of Ready Za Budući Sprint

Sprint je spreman tek kada ima:

- jasan korisnički problem
- jasnu vezu s Program 1 dokumentima
- jasnu granicu što se ne radi
- audit pravila
- sigurnosne granice
- demo-data only pretpostavku
- testni plan

## 12. Definition Of Done Za Budući Sprint

Sprint je gotov tek kada:

- postoje backend testovi za poslovna pravila
- frontend smoke/typecheck/build prolazi gdje je primjenjivo
- audit događaji postoje za važne promjene
- UI ne prikazuje AI prijedlog kao službenu istinu
- dokumentacija je ažurirana
- postojeći appointment, billing, inventory, readiness i audit tokovi nisu slomljeni

## 13. Zaključak

Program 1 treba graditi ASTRA-u prema kliničkom toku, ali redoslijedom koji poštuje stvarnost medicine.

Prvo znamo što je poznato.

Zatim znamo što je nerazriješeno.

Tek nakon toga organiziramo skrb u epizode i workflowe.

## 14. Program 1 Phase C0-C15 - Clinical Readiness Enforcement Readiness Design

Status: zatvoreno kao design/guardrail pass.

Phase C0-C15 namjerno nije uveo enforcement runtime.

Implementirano:

- enforcement readiness design
- zabranjeni pojmovi i siguran vokabular
- human responsibility model
- enforcement risk register
- no-go matrix
- advisory signal contract
- minimalni `ClinicalReadinessAdvisorySignal` schema prototype
- advisory signal safety regression tests
- preview mapping dokument
- permission model design
- review acknowledgment design
- audit contract
- UI copy and safety labels
- enforcement readiness CI gate
- go/no-go matrix
- closure report i next-step decision brief

Izvan scopea:

- clinical approval
- readiness clearance
- automatic clearance
- override workflow runtime
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production approval
- real patient data
- real AI/OCR
- autonomous decision
- workflow enforcement
- automatic blocking ili rescheduling
- certification/compliance claims

Zakljucak:

Clinical Readiness enforcement nije spreman za runtime implementaciju.

ASTRA smije nastaviti samo s dokumentacijskim i guardrail radom oko ljudskog review acknowledgment modela.

Preporuceni sljedeci task:

`Program 1 Phase C16 - Human Review Acknowledgment Contract`

## 15. Program 1 Phase C16-C26 - Human Review Acknowledgment And Advisory Read-Only Surface

Status: zatvoreno kao guarded prototype/design pass.

Implementirano:

- Human Review Acknowledgment contract
- forbidden semantics matrix
- acknowledgment audit payload contract
- pasivni `ClinicalReadinessReviewAcknowledgment` schema prototype
- acknowledgment safety regression guard
- advisory read-only UI design
- advisory read-only UI prototype u Appointment Workspaceu
- advisory UI smoke hardening
- human review acknowledgment go/no-go matrix
- acknowledgment/advisory CI gate
- closure report i next-step decision brief

Runtime granica:

- nema acknowledgment endpointa
- nema acknowledgment DB modela ili migracije
- nema persistence
- nema acknowledgment action buttona
- nema workflow enforcementa
- nema status promjene termina

Safety zakljucak:

Acknowledgment znaci samo da je covjek pregledao signal.

Ne znaci clinical approval, readiness clearance, override, Task, Outcome Evidence ili dozvolu da se postupak provede.

Preporuceni sljedeci task:

`Program 1 Phase C27 - Human Review Acknowledgment Persistence Design`

## 16. Program 1 Phase C27-C37 - Human Review Acknowledgment Persistence Governance

Status: zatvoreno kao design/governance i no-go hardening pass.

Implementirano:

- acknowledgment persistence design
- persistence no-go matrix
- migration review
- permission governance
- audit governance
- retention and rollback rules
- runtime no-go regression guard
- permission seed no-go hardening
- UI action no-go hardening
- persistence CI gate
- closure report, go/no-go matrix i next-step decision brief

Runtime granica:

- nema acknowledgment DB modela
- nema Alembic migracije
- nema endpointa
- nema write servicea
- nema permission seedanja
- nema UI action buttona
- nema status promjene termina
- nema Task enginea
- nema Outcome Evidencea
- nema patient messaginga

Zakljucak:

Acknowledgment persistence ostaje no-go za runtime.

ASTRA smije nastaviti s endpoint contract designom prije bilo kakve migracije ili write servicea.

Preporuceni sljedeci task:

`Program 1 Phase C38 - Acknowledgment Endpoint Contract Design`

## 17. Program 1 Phase C38-C48 - Human Review Acknowledgment Endpoint Contract

Status: zatvoreno kao contract/governance pass.

Implementirano:

- future endpoint contract design
- passive request/response schemas
- error states contract
- permission boundary
- audit expectations
- idempotency/retry policy
- runtime no-go boundary
- endpoint absence regression guard
- endpoint CI gate
- endpoint go/no-go matrix
- closure report i next-step decision brief

Runtime granica:

- nema FastAPI acknowledgment rute
- nema write servicea
- nema DB modela ili migracije
- nema seed permissiona
- nema frontend API write metode
- nema UI action buttona

Zakljucak:

Acknowledgment endpoint ostaje no-go za runtime.

Pasivne request/response sheme smiju ostati kao contract prototype, ali nisu vezane na rutu.

Preporuceni sljedeci task:

`Program 1 Phase C49 - Acknowledgment Persistence Migration Draft Design`

## 18. Program 1 Phase C49-C59 - Human Review Acknowledgment DB Foundation

Status: zatvoreno kao migration-draft / DB-foundation pass.

Implementirano:

- acknowledgment migration draft design
- pasivni ORM model `ClinicalReadinessReviewAcknowledgment`
- Alembic migracija `0017_acknowledgment_persistence_foundation`
- DB-level non-empty reason constraint
- DB-level false-only decision, clearance i override constraints
- model/migration shape regression tests
- runtime endpoint no-go hardening
- frontend action no-go hardening
- permission seed no-go hardening
- audit/retention boundary
- rollback/restore boundary
- DB foundation CI gate
- go/no-go matrix i closure report

Runtime granica:

- nema POST/PATCH/PUT/DELETE endpointa za acknowledgment
- nema runtime write servicea
- nema frontend write clienta
- nema UI action buttona
- nema permission seeda
- nema appointment status promjene
- nema Task enginea
- nema Outcome Evidencea
- nema patient messaginga

Zakljucak:

DB row, ako se kreira u buducnosti, nije clinical decision record.

Acknowledgment DB foundation ne znaci endpoint approval, production approval ili real patient data approval.

Preporuceni sljedeci task:

`Program 1 Phase C60 - Acknowledgment Write Service Contract Design`

## 19. Program 1 Phase C60-C70 - Human Review Acknowledgment Internal Service Boundary

Status: u tijeku kao service-contract / internal-boundary pass.

Phase C60 update:

- documented internal write service contract for Human Review Acknowledgment
- defined proposed service function, inputs, outputs and validation responsibilities
- documented reason-required and actor-required rules
- documented appointment/patient/snapshot scope checks
- documented audit write requirement and single-transaction boundary
- documented rollback expectation
- confirmed no endpoint, no frontend action, no permission seed and no workflow side effects

Runtime granica:

- nema acknowledgment endpointa
- nema frontend write clienta
- nema UI action buttona
- nema appointment status promjene
- nema Task enginea
- nema Outcome Evidencea
- nema patient messaginga
- nema approval, clearance ili override semantike

Phase C60-C70 closure update:

- write service contract, validation contract, transaction/audit coupling and idempotency contract are documented
- internal-only acknowledgment service prototype exists
- targeted backend tests cover validation, audit, rollback and no workflow side effects
- CI advisory/acknowledgment safety gate includes internal service tests
- runtime endpoint remains no-go
- frontend action remains no-go
- permission seed remains no-go
- real patient data and production remain no-go

Closure documents:

- `PROGRAM_1_PHASE_C70_ACKNOWLEDGMENT_INTERNAL_SERVICE_CLOSURE_REPORT.md`
- `PROGRAM_1_PHASE_C70_NEXT_STEP_DECISION_BRIEF.md`

Recommended next task:

`Program 1 Phase C71 - Acknowledgment Read API Contract Design`

## 20. Program 1 Phase C71-C81 - Human Review Acknowledgment Read Boundary

Status: u tijeku kao read-only API contract / read-boundary pass.

Phase C71 update:

- documented appointment-scoped read API contract
- proposed list/detail routes for read-only acknowledgment access
- documented auth and read permission requirement
- documented sorting, empty state and error states
- confirmed read API must not create, update, delete, approve, clear, override or mutate workflow state

Runtime granica:

- write endpoint remains no-go
- frontend write action remains no-go
- write permission seed remains no-go
- real patient data and production remain no-go

Phase C71-C81 closure update:

- read response schemas were added
- read permission boundary was documented
- read service contract was documented
- appointment-scoped read-only endpoints were implemented
- read-only frontend client/types were added
- runtime write no-go hardening remains active
- read go/no-go matrix and closure report were added

Current read-only endpoints:

- `GET /api/appointments/{appointment_id}/clinical-readiness/acknowledgments`
- `GET /api/appointments/{appointment_id}/clinical-readiness/acknowledgments/{acknowledgment_id}`

Still no-go:

- POST/PATCH/PUT/DELETE acknowledgment endpoint
- frontend action button
- write permission seed
- approval, clearance, override
- Task engine
- Outcome Evidence
- appointment status mutation
- patient messaging

Recommended next task:

`Program 1 Phase C82 - Acknowledgment Read-Only UI Surface Contract`

## 21. Program 1 Phase C82-C92 - Human Review Acknowledgment Read-Only UI Boundary

Status: u tijeku kao read-only UI surface pass.

Phase C82-C83 update:

- read-only UI surface contract documented
- UI copy/state matrix documented
- safe labels, helper text and no-action rules locked before runtime UI changes

Runtime granica:

- no acknowledgment action button
- no write client
- no write endpoint
- no approval, clearance, override or resolution semantics

Phase C82-C92 closure update:

- read-only acknowledgment UI panel added to Appointment Workspace
- loading, empty, permission and read error states are non-blocking
- smoke coverage protects safe wording and no-action boundary
- permission UX and snapshot/advisory relationship were documented
- read UI go/no-go matrix and closure report were added

Still no-go:

- acknowledgment action button
- POST/PATCH/PUT/DELETE acknowledgment client or endpoint
- write permission seed
- approval, clearance, override
- Task engine
- Outcome Evidence
- appointment status mutation
- patient messaging
- production/real-data enablement

Recommended next task:

`Program 1 Phase C93 - Acknowledgment Read UI Usability Review`

## 22. Program 1 Phase C93-C103 - Human Review Acknowledgment Read UI Usability

Status: u tijeku kao read-only usability and safety hardening pass.

Phase C93 update:

- acknowledgment read UI usability review plan documented
- safety wording criteria documented
- empty, loading, error and permission state review criteria documented
- actor, timestamp, reason and snapshot relation review criteria documented

Runtime granica:

- no acknowledgment action button
- no POST/PATCH/PUT/DELETE acknowledgment client or endpoint
- no write permission seed
- no approval, clearance, override or resolution semantics
- no appointment status mutation, Task, Outcome Evidence or patient messaging

Phase C93-C103 closure update:

- read-only acknowledgment panel copy refined for safety and usability
- empty, error and permission states hardened so they do not imply readiness state
- actor, timestamp, reason and snapshot relation display clarified
- accessibility hints added without redesign or new dependency
- frontend smoke expanded for safe wording and no-action guardrails
- backend safety guard review confirms read-only routes and absent write surface remain protected
- go/no-go matrix and closure report added

Still no-go:

- acknowledgment action button
- write client or write endpoint
- write permission seed
- approval, readiness clearance or override
- Task engine
- Outcome Evidence
- appointment status mutation
- patient messaging
- production or real-data enablement

Recommended next task:

`Program 1 Phase C104 - Acknowledgment Read Audit Policy Design`

## 23. Program 1 Phase C104-C114 - Human Review Acknowledgment Read Audit Policy

Status: u tijeku kao audit-policy and governance pass.

Phase C104 update:

- acknowledgment read audit policy documented
- access audit vs clinical evidence boundary documented
- list/detail/denied/failed read categories documented
- audit-noise and privacy risks documented
- preferred future implementation direction is denied-read audit only

Runtime granica:

- no automatic audit of every read
- no write endpoint
- no acknowledgment action button
- no approval, clearance or override
- no appointment status mutation, Task, Outcome Evidence or patient messaging

Phase C104-C114 closure update:

- read audit policy documented
- future event taxonomy documented
- privacy-minimized payload contract documented
- audit-noise control policy documented
- sensitive read boundary documented
- current behavior guard added for no read-audit-by-default behavior
- denied-read audit policy documented as preferred future runtime candidate
- retention/export policy and CI gate documented
- read audit go/no-go matrix and closure report added

Runtime decision:

- no automatic audit of every acknowledgment read
- list/detail success-read audit remains deferred
- denied-read audit is the recommended next prototype
- read audit remains access/security evidence, not Outcome Evidence

Still no-go:

- write endpoint
- acknowledgment action button
- approval, readiness clearance or override
- Task engine
- Outcome Evidence
- appointment status mutation
- patient messaging
- production or real-data enablement

Recommended next task:

`Program 1 Phase C115 - Acknowledgment Denied-Read Audit Prototype`

## 24. Program 1 Phase C115-C125 - Human Review Acknowledgment Denied-Read Audit

Status: implemented as selective denied-read access audit.

Phase C115-C125 closure update:

- denied-read audit prototype design documented
- denied-read audit helper implemented
- permission denied and API key denied acknowledgment reads now write one denied-read audit event
- out-of-scope acknowledgment detail reads now write one privacy-safe denied-read audit event
- successful list/detail reads remain unaudited
- noise and payload privacy guards added
- audit failure policy documented and covered
- CI gate and go/no-go matrix added

Runtime decision:

- selective denied-read audit is implemented
- successful list/detail read audit remains deferred
- denied-read audit is access/security evidence, not clinical evidence

Still no-go:

- acknowledgment write endpoint
- acknowledgment action button
- approval, readiness clearance or override
- Task engine
- Outcome Evidence
- appointment status mutation
- patient messaging
- production or real-data enablement

Recommended next task:

`Program 1 Phase C126 - Acknowledgment Write Endpoint Final No-Go Review`

## 25. Program 1 Phase C126-C136 - Human Review Acknowledgment Final No-Go And D0 Transition

Status: in progress as final no-go / closure / transition pass.

Phase C126 update:

- final C-phase no-go review for the acknowledgment write endpoint is documented
- current acknowledgment stack remains read-oriented and guarded
- write endpoint, write UI action, frontend write client and write permission seed remain absent
- D0 Findings Lifecycle Foundation is identified as the safer next implementation direction

Runtime boundary:

- no POST/PATCH/PUT/DELETE acknowledgment endpoint
- no acknowledgment action button
- no approval, readiness clearance or override
- no Task engine
- no Outcome Evidence
- no appointment status mutation
- no patient messaging
- no production or real-data enablement

Recommended next task:

`Program 1 Phase C127 - Acknowledgment Stack Inventory`

Phase C126-C136 closure update:

- write endpoint final no-go review is documented
- acknowledgment stack inventory is documented
- write endpoint risk register is documented
- runtime boundary regression guards are reviewed
- production and real-data blocker matrix is documented
- write permission and UI action final no-go decisions are documented
- final C-phase go/no-go matrix is documented
- D0 Findings Lifecycle transition decision brief is documented
- Program 1 Phase C acknowledgment closure report is complete

Final Phase C decision:

- acknowledgment read/advisory stack remains allowed for guarded demo/pilot use
- selective denied-read audit remains allowed as access/security evidence
- acknowledgment write endpoint remains no-go
- acknowledgment UI action remains no-go
- write permission seed remains no-go
- production and real patient data remain no-go

Recommended next task:

`Program 1 Phase D0 - Findings Lifecycle Foundation`

## 26. Program 1 Phase D0-D10 - Findings Lifecycle Foundation

Status: in progress as foundation/design pass.

Phase D0 update:

- Findings Lifecycle foundation is opened as documentation-first work
- a finding is defined as a source-linked clinical knowledge unit that may require review and lifecycle governance
- D0 confirms finding is not automatic diagnosis, Task, Outcome Evidence, patient message, clearance, override or appointment status
- D0 connects findings to Patient Clinical Knowledge, ClinicalDocument, Patient Clinical Summary, Open Questions, physician decisions and the acknowledgment/readiness stack

Runtime boundary:

- no findings endpoint
- no findings DB model or migration
- no Task engine
- no Outcome Evidence
- no patient messaging
- no automatic diagnosis or treatment plan
- no appointment status mutation
- no production or real-data enablement

Recommended next task:

`Program 1 Phase D1 - Finding Definition and Boundary Contract`

Phase D0-D10 closure update:

- finding definition and boundary contract documented
- lifecycle status taxonomy documented
- source evidence mapping documented
- review boundary and human responsibility documented
- open question relationship documented
- recommendation/decision boundary documented
- passive finding schema prototype added
- findings safety regression guard added
- no-go matrix and closure report added

Runtime decision:

- no findings endpoint
- no findings DB model or migration
- no findings service
- no Task engine
- no Outcome Evidence
- no patient messaging
- no automatic diagnosis or treatment plan
- production and real-data use remain no-go

Recommended next task:

`Program 1 Phase D11 - Findings Persistence Design`

## 27. Program 1 Phase D11-D21 - Findings Persistence Design

Status: in progress as persistence-design pass.

Phase D11 update:

- proposed `ClinicalFinding` entity and `clinical_findings` table are documented
- persistence remains source-linked and patient-scoped
- finding row is explicitly not diagnosis, treatment plan, Task, Outcome Evidence, patient message, approval, clearance or override

Runtime boundary:

- no findings DB model or migration
- no findings endpoint
- no findings service
- no frontend UI
- no Task engine, Outcome Evidence or patient messaging

Recommended next task:

`Program 1 Phase D12 - Findings Database Shape Review`

Phase D11-D21 closure update:

- findings persistence design documented
- database shape and column policy documented
- source-linking persistence rules documented
- lifecycle status persistence contract documented
- review metadata contract documented
- ORM shape deferred to avoid model-without-migration drift
- migration review gate documented
- persistence no-go matrix and CI gate documented

Runtime decision:

- no findings DB model or migration
- no findings endpoint or service
- no frontend UI
- no Task engine, Outcome Evidence or patient messaging
- production and real-data use remain no-go

Recommended next task:

`Program 1 Phase D22 - Findings Persistence Migration Draft`

## 28. Program 1 Phase D22-D32 - Findings Persistence Migration Draft

Status: in progress as DB-foundation / migration-draft pass.

Phase D22 update:

- findings migration draft design documented
- proposed table remains `clinical_findings`
- proposed model remains `ClinicalFinding`
- migration intent is DB foundation only, not endpoint/service/UI approval

Runtime boundary:

- no findings endpoint
- no findings service
- no frontend UI
- no Task engine
- no Outcome Evidence
- no patient messaging
- no automatic diagnosis/treatment

Recommended next task:

`Program 1 Phase D23 - Passive ClinicalFinding ORM Model`

Phase D22-D32 closure update:

- passive `ClinicalFinding` ORM model added
- Alembic migration `0018_clinical_findings` added for `clinical_findings`
- DB shape, source-linking and lifecycle status regression coverage added
- runtime route/service/permission absence guard added
- migration rollback notes, CI gate and go/no-go matrix documented

Runtime boundary:

- no findings endpoint
- no findings service
- no frontend findings UI
- no Task engine
- no Outcome Evidence
- no patient messaging
- no automatic diagnosis or treatment
- no appointment status mutation
- no production or real-data enablement

Recommended next task:

`Program 1 Phase D33 - Findings Read-Only API Contract`

## 29. Program 1 Phase D33-D43 - Findings Read API Boundary

Status: in progress as read-only API contract/prototype pass.

Phase D33 update:

- findings read-only API contract documented
- proposed patient-scoped list/detail routes documented
- read permission boundary proposed as `clinical_findings.read`
- response shape remains source-linked and no-decision

Runtime boundary:

- no findings write endpoint
- no review endpoint
- no frontend findings UI
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis/treatment
- no production or real-data enablement

Recommended next task:

`Program 1 Phase D34 - Findings Read Response Schema Contract`

Phase D33-D43 closure update:

- findings read response schemas added
- read permission boundary documented and `clinical_findings.read` seeded
- GET-only patient-scoped findings read API added
- read API regression coverage added
- write route absence and source-linking guards added
- CI gate and read API go/no-go matrix documented

Runtime boundary:

- no findings POST/PATCH/PUT/DELETE endpoint
- no review/approve/clear/resolve endpoint
- no frontend findings UI
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment

Phase D82 update:

- passive open question source/preview schemas added
- safe status vocabulary added
- source reference and clinician review requirement are enforced in schema shape
- no open question endpoint, DB model, migration, service, UI or automatic question creation was added

Phase D83 update:

- open question safety regression guard added
- backend tests cover passive schema safety, route absence, DB model/table absence and service absence
- frontend smoke guards absence of open question client/UI labels

Phase D84-D86 update:

- open question runtime no-go matrix added
- open question CI gate documented
- open questions from findings go/no-go matrix added
- runtime endpoints, persistence, automatic question creation, Task, Outcome Evidence and patient messaging remain no-go

Phase D87 update:

- D77-D87 open questions from findings closure report added
- next-step decision brief recommends Program 1 Phase D88 - Open Question Persistence Design
- D88 remains documentation-only before any persistence or runtime workflow
- no appointment status mutation
- production and real-data use remain no-go

Recommended next task:

`Program 1 Phase D44 - Findings Read-Only Workspace Contract`

## 30. Program 1 Phase D44-D54 - Findings Read-Only Workspace Boundary

Status: implemented as read-only workspace boundary after backend verification passed.

Phase D44 update:

- D33-D43 backend verification gate documented
- initial Docker attempt was blocked while Docker Desktop daemon was unavailable
- retry passed targeted findings tests and full backend suite

Phase D45 update:

- read-only findings workspace contract documented
- safe labels, forbidden labels, empty/error/permission states and no-action boundary documented

Phase D46-D54 closure update:

- frontend GET-only findings types/client added
- Patient Workspace read-only findings panel added
- loading, empty and error states added
- smoke/no-action guard added
- permission UX and source relationship documented
- CI gate, go/no-go matrix, closure report and next-step decision brief added

Runtime boundary:

- findings frontend UI is read-only
- frontend findings client is GET-only
- no findings write/review endpoint
- no UI action button
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment

Phase D62 update:

- frontend smoke coverage expanded for findings workspace safe copy, empty/error/permission states, status labels and source fallback
- smoke guards that Patient Workspace findings panel does not expose action, diagnosis, treatment, approval, clearance, override, task, outcome or patient messaging wording

Phase D63 update:

- backend findings read API safety guards reviewed
- existing tests cover GET-only behavior, write route absence, forbidden response fields and workflow side-effect absence
- no duplicate backend test was added

Phase D64 update:

- findings workspace usability go/no-go matrix added
- read-only usability refinements are allowed for demo/pilot
- write/review endpoints, Task, Outcome Evidence, patient messaging, automatic diagnosis/treatment, production and real-data use remain no-go

Phase D55-D65 closure update:

- findings read-only workspace usability hardening completed
- safety copy, empty/error/permission states, lifecycle labels, source-linked metadata display and accessibility were refined
- smoke coverage expanded for safe copy and no-action/no-forbidden wording
- backend safety guards were reviewed without adding duplicate tests

Runtime boundary:

- no findings write/review endpoint
- no frontend write client
- no UI action button
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment
- no production or real-data enablement

Recommended next task:

`Program 1 Phase D66 - ClinicalDocument Finding Extraction Contract`

## 32. Program 1 Phase D66-D76 - ClinicalDocument Finding Extraction Contract

Status: in progress as extraction-contract / runtime no-go pass.

Phase D66 update:

- ClinicalDocument finding extraction contract documented
- extraction, raw extracted text, candidate finding, persisted finding and physician-reviewed finding boundaries defined
- extraction remains source-linked and non-runtime

Runtime boundary:

- no OCR engine or real AI provider
- no extraction endpoint or background job
- no automatic finding creation
- no findings write/review endpoint
- no frontend extraction UI
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment
- production and real-data use remain no-go

Recommended next task:

`Program 1 Phase D67 - Extraction Candidate Boundary Contract`

Phase D67-D70 update:

- extraction candidate boundary documented
- source evidence traceability requirements documented
- confidence and limitations boundary documented
- human review gate documented

Runtime boundary:

- no runtime extraction
- no automatic finding persistence
- no extraction endpoint, service, job or UI
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment

Phase D71 update:

- passive extraction candidate schemas added
- source traceability, limitations, human review requirement and non-persistence boundary are represented in schema shape
- no extraction endpoint, service, job, UI or automatic finding persistence was added

Phase D72 update:

- extraction safety regression guard added
- backend tests cover passive schema safety, source requirement, no runtime route and no service
- frontend smoke guards absence of findings extraction client/UI labels

Phase D73-D75 update:

- extraction runtime no-go matrix added
- extraction CI gate documented
- extraction contract go/no-go matrix added
- runtime extraction, AI/OCR runtime, automatic persistence and real-data/production use remain no-go

Phase D66-D76 closure update:

- ClinicalDocument finding extraction contract closed
- passive extraction source/candidate/batch schemas added with regression coverage
- frontend smoke guards absence of findings extraction client/UI labels
- runtime extraction, automatic candidate persistence, AI/OCR runtime, write/review endpoints, Task, Outcome Evidence and patient messaging remain no-go

Recommended next task:

`Program 1 Phase D77 - Open Questions From Findings Contract`

## 33. Program 1 Phase D77-D87 - Open Questions From Findings Contract

Status: in progress as open-question contract / runtime no-go pass.

Phase D77 update:

- open questions from findings contract documented
- open question, finding, ClinicalDocument, extraction candidate, recommendation and physician decision boundaries defined
- runtime open-question creation remains no-go

Runtime boundary:

- no open question endpoint
- no open question DB model or migration
- no open question write service
- no automatic question creation
- no frontend open question UI
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment
- production and real-data use remain no-go

Recommended next task:

`Program 1 Phase D78 - Open Question Boundary and Forbidden Semantics`

Phase D78-D81 update:

- open question forbidden semantics documented
- source-linking contract documented
- human review responsibility contract documented
- safe lifecycle status taxonomy documented

Runtime boundary:

- no open question endpoint
- no open question persistence
- no automatic creation from findings or extraction candidates
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment
- no appointment status mutation
- production and real-data use remain no-go

Recommended next task:

`Program 1 Phase D55 - Findings Workspace Usability Review`

## 31. Program 1 Phase D55-D65 - Findings Workspace Usability

Status: in progress as read-only usability/safety hardening.

Phase D55 update:

- findings workspace usability review plan documented
- review criteria cover source-linked display, lifecycle labels, empty/error/permission states, accessibility and no-action boundaries

Runtime boundary:

- findings workspace remains read-only
- no findings write/review endpoint
- no UI action button
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment
- production and real-data use remain no-go

Recommended next task:

`Program 1 Phase D56 - Findings Workspace Copy Refinement`

Phase D56-D61 update:

- read-only findings panel copy refined
- empty, error and permission states hardened
- lifecycle statuses now render as safe UI labels
- source metadata is displayed with structured source-linked fields and safe fallbacks
- accessibility pass added list/status semantics without introducing actions

Runtime boundary:

- no findings write/review endpoint
- no findings write client
- no UI action button
- no Task engine, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment
