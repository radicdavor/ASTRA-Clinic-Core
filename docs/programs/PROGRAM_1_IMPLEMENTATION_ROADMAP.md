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
