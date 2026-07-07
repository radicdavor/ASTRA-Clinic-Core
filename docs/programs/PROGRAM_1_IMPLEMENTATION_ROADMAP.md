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
