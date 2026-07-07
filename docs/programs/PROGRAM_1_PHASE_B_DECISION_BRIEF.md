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
