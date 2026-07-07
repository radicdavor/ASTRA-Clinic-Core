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
