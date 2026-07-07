# Program 1 Phase B - Decision Brief

Status: preporuka smjera, bez implementacije

## 1. Svrha

Ovaj dokument predlaze sljedecu fazu Programa 1 nakon zatvaranja Phase A.

Ne implementira novu funkcionalnost, ne uvodi nove modele, ne otvara produkciju i ne odobrava stvarne podatke pacijenata.

## 2. Recommended Phase B direction

Preporuka:

`Phase B - Clinical Readiness Design, not implementation`

Razlog:

Prije gradnje taskova, workflowa ili automatizacije epizoda, ASTRA mora definirati sto znaci da je pacijent klinicki spreman za odredeni termin, uslugu ili postupak.

Phase B treba prvo biti design/spec faza. Tek nakon odobrenog operating modela moze se odluciti hoce li i kada krenuti implementacija.

## 3. Why not Task Engine yet

Task engine jos nije pravi sljedeci korak.

Razlozi:

- Open Questions jos nemaju lifecycle, owner ili due date
- Outcome Evidence ne postoji
- Clinical Readiness Gate jos nije definiran
- taskovi bez readiness i closure semantike stvarali bi operativni sum
- taskovi trebaju nastati iz potvrdenih klinickih odluka, ne iz sirovih nerazrijesenih stavki

Ako ASTRA prerano uvede taskove, korisnici ce dobiti vise posla, a ne jasniji klinicki tok.

## 4. Why not Episode-Based Care yet

Episode Engine postoji, ali ostaje deferred.

Patient Clinical Knowledge je sada jaci temelj, ali Episode-Based Care treba pricekati dok se ne definiraju:

- clinical readiness semantics
- task lifecycle
- closure semantics
- odnos epizode prema pregledanim source dokumentima
- odnos epizode prema otvorenim pitanjima

Epizoda ne smije postati izvor klinicke istine. Ona kasnije moze organizirati pregledane cinjenice.

## 5. Why not real AI/OCR yet

Real AI/OCR nije spreman za Phase B implementaciju.

Razlozi:

- file/security pravila nisu produkcijski definirana
- real-data readiness nije odobren
- OCR moze stvoriti lazni osjecaj tocnosti ako nema stabilnog review procesa
- AI provider moze stvoriti lazni osjecaj klinicke sigurnosti ako readiness i source rules nisu formalizirani

Postojeci placeholder lifecycle dovoljan je za demo/pilot dokaz principa:

AI proposes. Physician confirms. ASTRA records both.

## 6. Phase B candidate scope

Phase B treba definirati:

- Clinical Readiness Gate model
- readiness statuse
- patient/service/procedure-specific readiness rules
- override semantics
- uloge lijecnika, medicinske sestre i administracije
- odnos prema Operational Readiness
- odnos prema ClinicalDocument evidence
- odnos prema buducem Task engineu
- gastroenteroloske primjere
- estetske medicine primjere
- no-code-first pristup, osim ako maintainer posebno odobri implementaciju

## 7. Phase B no-go

Phase B ne smije odmah implementirati:

- Task engine
- Workflow Engine
- autonomni AI
- production real-data workflows
- episode automation
- Outcome Evidence object
- patient-facing automation

## 8. Recommended next Codex task

Preporuceni sljedeci task:

`Program 1 Phase B0 - Clinical Readiness Gate Operating Model`

Ovaj task treba biti documentation-first.

Ocekivani izlaz:

- definicija Clinical Readiness Gate pojma
- razlika izmedu Operational Readiness i Clinical Readiness
- status model
- override pravila
- primjeri za gastroenterologiju i estetsku medicinu
- jasni No-Go uvjeti prije implementacije

## 9. Phase B0 outcome

Phase B0 je documentation-only operating model.

Novi B0 dokumenti:

- `PROGRAM_1_PHASE_B0_CLINICAL_READINESS_GATE_OPERATING_MODEL.md`
- `PROGRAM_1_PHASE_B0_CLINICAL_READINESS_ROLES.md`
- `PROGRAM_1_PHASE_B0_CLINICAL_READINESS_SPECIALTY_EXAMPLES.md`
- `PROGRAM_1_PHASE_B0_CLINICAL_READINESS_IMPLEMENTATION_BOUNDARIES.md`

B0 zakljucak:

- Clinical Readiness Gate je patient/service/procedure-specific concept
- nije Operational Readiness
- nije Task engine
- nije Workflow Engine
- nije Episode-Based Care
- nije autonomous AI decision
- prva buduca implementacija treba biti read-only preview, ne enforcing blocker

Preporuceni sljedeci task:

`Program 1 Phase B1 - Clinical Readiness Vocabulary and Domain Mapping`

## 10. Phase B1 outcome

Phase B1 je documentation-only vocabulary i domain mapping pass.

Novi B1 dokumenti:

- `PROGRAM_1_PHASE_B1_CLINICAL_READINESS_VOCABULARY.md`
- `PROGRAM_1_PHASE_B1_CLINICAL_READINESS_DOMAIN_MAPPING.md`
- `PROGRAM_1_PHASE_B1_CLINICAL_READINESS_STATUS_TAXONOMY.md`
- `PROGRAM_1_PHASE_B1_CLINICAL_READINESS_SOURCE_EVIDENCE_MAPPING.md`

B1 zakljucak:

- Clinical Readiness vocabulary je zakljucan
- Clinical Readiness domain mapping je definiran
- Clinical Readiness status taxonomy je definirana
- source/evidence mapping je definiran
- Operational Readiness i Clinical Readiness ostaju odvojeni
- nema implementacije Clinical Readiness Gatea

Preporuceni sljedeci task:

`Program 1 Phase B2 - Clinical Readiness API and UI Contract`

B2 treba ostati contract/design first.

## 11. Phase B2 outcome

Phase B2 je documentation-only API/UI contract pass.

Novi B2 dokumenti:

- `PROGRAM_1_PHASE_B2_CLINICAL_READINESS_API_CONTRACT.md`
- `PROGRAM_1_PHASE_B2_CLINICAL_READINESS_UI_CONTRACT.md`
- `PROGRAM_1_PHASE_B2_CLINICAL_READINESS_PREVIEW_DATA_CONTRACT.md`
- `PROGRAM_1_PHASE_B2_CLINICAL_READINESS_SAFETY_REGRESSION_CONTRACT.md`

B2 zakljucak:

- buduci prvi endpoint treba biti read-only appointment-scoped preview
- buduca prva UI povrsina treba biti Appointment Workspace
- preview ne smije blokirati workflow
- preview ne smije kreirati taskove
- preview ne smije clearati readiness
- preview ne smije koristiti unreviewed AI kao source
- preview ne smije koristiti Patient Clinical Summary kao source of truth
- preview mora ostati odvojen od `/api/readiness`

Preporuceni sljedeci task:

`Program 1 Phase B3 - Clinical Readiness Read-Only Preview Prototype`

B3 smije biti code task samo ako ostane demo/pilot-only, non-blocking i read-only.

## 12. Phase B3 outcome

Phase B3 je prvi ograniceni code prototype za Clinical Readiness.

Implementirano:

- `GET /api/appointments/{appointment_id}/clinical-readiness-preview`
- deterministic read-only preview service
- Appointment Workspace preview section
- regression tests
- smoke coverage

B3 ostaje:

- demo/pilot-only
- read-only
- non-blocking
- bez taskova
- bez overridea
- bez AI clearancea
- bez production/certification claimova
- bez database modela ili migracije

Preporuceni sljedeci task:

`Program 1 Phase B4 - Clinical Readiness Template Design`

## 13. Phase B4 outcome

Phase B4 uvodi demo/pilot-only static template model za read-only Clinical Readiness Preview.

Implementirano:

- `PROGRAM_1_PHASE_B4_CLINICAL_READINESS_TEMPLATE_DESIGN.md`
- staticne backend template definicije
- deterministic service-name matching
- generic fallback template
- template-generated preview itemi u appointment-scoped endpointu
- regression tests i smoke coverage

B4 ostaje:

- read-only
- appointment-scoped
- non-blocking
- demo/pilot-only
- bez DB template modela
- bez template editora
- bez overridea
- bez taskova
- bez Workflow Enginea
- bez AI clearancea
- bez production/certification claimova

Preporuceni sljedeci task:

`Program 1 Phase B5 - Clinical Readiness Template Binding Design`

B5 treba definirati kako se templatei kasnije sigurno vezu na katalog usluga bez pretvaranja u produkcijska pravila.

## 14. Phase B5 outcome

Phase B5 definira buduci binding model i governance prije bilo kakvog DB bindinga ili editora.

Implementirano:

- `PROGRAM_1_PHASE_B5_CLINICAL_READINESS_TEMPLATE_BINDING_DESIGN.md`
- `PROGRAM_1_PHASE_B5_CLINICAL_READINESS_TEMPLATE_GOVERNANCE.md`
- template selection metadata u preview responseu
- template binding transparency u Appointment Workspaceu
- regression coverage za metadata i no-go kontrole

B5 ostaje:

- read-only
- non-blocking
- appointment-scoped
- demo/pilot-only
- bez DB binding fielda
- bez migracija
- bez template editora
- bez explicit service binding persistencea
- bez production governance workflowa
- bez enforcementa

Preporuceni sljedeci task:

`Program 1 Phase B6 - Clinical Readiness Explicit Service Binding Prototype`

B6 smije ici samo kao demo/pilot-only prototype i treba preferirati non-migrating configuration pristup prije bilo kakvog DB fielda.

## 15. Phase B6 outcome

Phase B6 uvodi prvi demo/pilot explicit service binding prototype bez migracije.

Implementirano:

- `PROGRAM_1_PHASE_B6_EXPLICIT_SERVICE_BINDING_PROTOTYPE.md`
- staticni demo service binding config
- explicit binding precedence prije keyword fallbacka
- `template_binding_status="explicit"` kada binding dolazi iz demo konfiguracije
- regression coverage za explicit binding i safety granice

B6 ostaje:

- read-only
- appointment-scoped
- non-blocking
- demo/pilot-only
- bez DB binding fielda
- bez migracija
- bez template editora
- bez persistent binding workflowa
- bez enforcementa

Preporuceni sljedeci task:

`Program 1 Phase B7 - Clinical Readiness Template Versioning Design`

B7 treba definirati verzioniranje template contenta i bindinga prije DB modela ili editora.

## 16. Phase B7 outcome

Phase B7 uvodi design i demo runtime transparency za template versioning.

Implementirano:

- `PROGRAM_1_PHASE_B7_CLINICAL_READINESS_TEMPLATE_VERSIONING_DESIGN.md`
- staticni demo template version metadata
- `template_version` i `template_version_warning` u preview responseu
- prikaz verzije u Appointment Workspaceu
- regression coverage za versioning metadata

B7 ostaje:

- read-only
- appointment-scoped
- non-blocking
- demo/pilot-only
- bez DB versioning tablica
- bez migracija
- bez template editora
- bez persistent snapshot modela
- bez enforcementa

Preporuceni sljedeci task:

`Program 1 Phase B8 - Clinical Readiness Snapshot Design`

B8 treba biti design-first i ne smije stvoriti Outcome Evidence objekt ili workflow enforcement.

## 17. Phase B8 outcome

Phase B8 definira buduci Clinical Readiness Snapshot prije implementacije persistencea.

Implementirano:

- `PROGRAM_1_PHASE_B8_CLINICAL_READINESS_SNAPSHOT_DESIGN.md`
- `PROGRAM_1_PHASE_B8_CLINICAL_READINESS_SNAPSHOT_BOUNDARIES.md`
- snapshot non-implementation metadata u preview responseu
- Appointment Workspace snapshot warning
- regression coverage za read-only i non-persistent ponasanje

B8 ostaje:

- read-only
- appointment-scoped
- non-blocking
- demo/pilot-only
- bez persistent snapshot modela
- bez DB tablice
- bez migracije
- bez capture endpointa
- bez snapshot history UI-ja
- bez Outcome Evidencea
- bez enforcementa
- bez overridea
- bez Task enginea
- bez Workflow Enginea
- bez real AI/OCR
- bez real patient data
- bez production/certification claimova

Preporuceni sljedeci task:

`Program 1 Phase B9 - Clinical Readiness Snapshot Persistence Design`

B9 treba ostati persistence design, ne implementacija, dok se ne definiraju schema, immutability, audit capture event i governance.

## 18. Phase B9 outcome

Phase B9 definira persistence design za buduci Clinical Readiness Snapshot bez implementacije.

Implementirano:

- `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_PERSISTENCE_MODEL.md`
- `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_AUDIT_MODEL.md`
- `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_LIFECYCLE_GOVERNANCE.md`
- `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_REGRESSION_GATE.md`

B9 ostaje:

- documentation-only
- bez DB tablice
- bez migracije
- bez capture endpointa
- bez snapshot history UI-ja
- bez audit event implementationa
- bez Outcome Evidencea
- bez enforcementa
- bez overridea
- bez Task enginea
- bez Workflow Enginea
- bez real AI/OCR
- bez real patient data
- bez production/certification claimova

B9 decision:

Buduci snapshot persistence mora spremiti immutable copy onoga sto je preview prikazao, uz audit capture event i preview-only disclaimer. Ne smije recomputeati povijesni sadrzaj i ne smije znaciti clinical approval.

Preporuceni sljedeci task:

`Program 1 Phase B10 - Snapshot Persistence Migration Review`

## 19. Phase B10 outcome

Phase B10 pregledava buducu snapshot persistence migraciju prije implementacije.

Implementirano:

- `PROGRAM_1_PHASE_B10_SNAPSHOT_PERSISTENCE_MIGRATION_REVIEW.md`

B10 definira:

- predlozeni model `ClinicalReadinessSnapshot`
- predlozenu tablicu `clinical_readiness_snapshots`
- obavezna polja
- FK odnose
- JSON payload odluku
- indeksiranje
- rollback strategiju
- migracijske rizike
- audit implikacije
- otvorene odluke prije implementacije

B10 ostaje:

- documentation-only
- bez backend koda
- bez frontend koda
- bez DB tablice
- bez Alembic migracije
- bez capture endpointa
- bez snapshot history UI-ja
- bez audit event implementationa
- bez Outcome Evidencea
- bez enforcementa
- bez overridea
- bez Task enginea
- bez appointment status promjene

B10 decision:

Snapshot persistence mora spremiti immutable copied JSON payload onoga sto je preview prikazao. Snapshot ne smije recomputeati povijesni sadrzaj i ne smije znaciti clinical approval.

Preporuceni sljedeci task:

`Program 1 Phase B11 - Snapshot Capture Endpoint Design`

## 20. Phase B11 outcome

Phase B11 definira buduci capture endpoint za Clinical Readiness Snapshot bez implementacije.

Implementirano:

- `PROGRAM_1_PHASE_B11_SNAPSHOT_CAPTURE_ENDPOINT_DESIGN.md`

B11 definira:

- predlozeni endpoint `POST /api/appointments/{appointment_id}/clinical-readiness-snapshots`
- tko smije captureati snapshot
- ulazne parametre
- response shape
- error states
- idempotency odluku
- transaction boundary
- buduci audit event `clinical_readiness_snapshot_captured`
- sigurnosne napomene
- odnos prema preview endpointu
- UI implikacije za buduci snapshot history

B11 ostaje:

- documentation-only
- bez backend koda
- bez frontend koda
- bez DB migracije
- bez endpoint implementacije
- bez persistencea
- bez audit event implementationa
- bez Outcome Evidencea
- bez Task enginea
- bez overridea
- bez appointment status promjene

B11 decision:

Capture mora biti eksplicitna write akcija s razlogom, permissionom, server-side preview rebuildom, immutable copied payloadom i audit eventom. Capture ne smije znaciti clinical approval.

Preporuceni sljedeci task:

`Program 1 Phase B12 - Snapshot Permission and Audit Contract`

## 21. Phase B12 outcome

Phase B12 definira permission i audit contract za buduci Clinical Readiness Snapshot capture bez implementacije.

Implementirano:

- `PROGRAM_1_PHASE_B12_SNAPSHOT_PERMISSION_CONTRACT.md`
- `PROGRAM_1_PHASE_B12_SNAPSHOT_AUDIT_PAYLOAD_CONTRACT.md`
- `PROGRAM_1_PHASE_B12_SNAPSHOT_PERMISSION_AUDIT_NO_GO_MATRIX.md`
- `PROGRAM_1_PHASE_B12_SNAPSHOT_IMPLEMENTATION_GATE.md`
- `PROGRAM_1_PHASE_B12_REGRESSION_NOTES.md`

B12 definira:

- buduce permissions `clinical_readiness.snapshots.read`, `clinical_readiness.snapshots.write`, `clinical_readiness.snapshots.supersede` i `clinical_readiness.snapshots.audit_read`
- role mapping za physician, nurse, reception/admin, clinic admin, AI agent, API key/integration i system job
- required reason za capture i supersession
- buduce audit evente `clinical_readiness_snapshot_captured`, `clinical_readiness_snapshot_viewed` i `clinical_readiness_snapshot_superseded`
- capture/supersede audit payload shape
- permission/audit no-go matrix
- implementation gate prije migracije, endpointa ili UI-ja

B12 ostaje:

- documentation-only
- bez backend koda
- bez frontend koda
- bez RBAC seed promjene
- bez DB migracije
- bez endpoint implementacije
- bez audit runtime implementacije
- bez snapshot history UI-ja
- bez Outcome Evidencea
- bez Task enginea
- bez overridea
- bez appointment status promjene

B12 decision:

Buduci snapshot capture mora biti explicit user action, permission-gated, reason-required, auditiran u istoj transakciji sa snapshot saveom i jasno preview-only. AI agent, system job i API key nemaju capture pravo by default.

Preporuceni sljedeci task:

`Program 1 Phase B13 - Snapshot Persistence Migration Draft`

## 22. Phase B13 outcome

Phase B13 dodaje migration/model-only persistence draft za buduci Clinical Readiness Snapshot.

Implementirano:

- SQLAlchemy model `ClinicalReadinessSnapshot`
- Alembic migracija `0014_clinical_readiness_snapshots.py`
- tablica `clinical_readiness_snapshots`
- persistence-shape regression coverage
- B13 regression notes

B13 definira runtime foundation:

- snapshot sprema copied preview payload
- snapshot ima required reason
- snapshot ima preview-only marker
- snapshot ima disclaimer
- snapshot ima template metadata
- snapshot ima future supersession fields

B13 ostaje:

- bez capture endpointa
- bez capture servicea
- bez frontend UI-ja
- bez permission enforcementa
- bez audit write runtimea
- bez snapshot history UI-ja
- bez Outcome Evidencea
- bez Task enginea
- bez overridea
- bez appointment status promjene

B13 decision:

DB schema smije postojati prije capturea, ali runtime ne smije spremati snapshot dok ne postoji odobren service koji rebuilda preview, validira reason, cuva permission/audit granice i ne mijenja workflow objekte.

Preporuceni sljedeci task:

`Program 1 Phase B14 - Snapshot Capture Service Prototype`

## 23. Phase B14 outcome

Phase B14 dodaje interni backend service prototype za Clinical Readiness Snapshot capture.

Implementirano:

- `backend/app/services/clinical_readiness_snapshots.py`
- `capture_clinical_readiness_snapshot(...)`
- server-side rebuild previewa
- immutable copied preview payload persistence
- audit event `clinical_readiness_snapshot_captured`
- rollback ako audit write ne uspije
- regression coverage
- B14 regression notes

B14 ostaje:

- bez capture endpointa
- bez frontend UI-ja
- bez capture buttona
- bez snapshot history UI-ja
- bez route-level permission enforcementa
- bez idempotency persistencea
- bez Outcome Evidencea
- bez Task enginea
- bez overridea
- bez appointment status promjene

B14 decision:

Capture logic sada postoji samo kao interni service. Ne smije se koristiti iz UI-ja ili eksternog API-ja dok B15 ne doda permission-gated, reason-required endpoint.

Preporuceni sljedeci task:

`Program 1 Phase B15 - Snapshot Capture Endpoint Prototype`
