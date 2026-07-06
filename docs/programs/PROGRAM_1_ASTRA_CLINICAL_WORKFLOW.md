# Program 1 - ASTRA Clinical Workflow

Status: arhitektonski operativni model, bez implementacije u ovom zadatku

## 1. Svrha

ASTRA Clinical Workflow nije novi ekran, nije jedan modul i nije dijagnostički engine.

ASTRA Clinical Workflow je operativni model koji povezuje:

- klinički razlog pacijenta
- predolaznu pripremu
- prijem
- kliničku spremnost
- konzultaciju
- postupak ili tretman
- nalaze
- liječnički potvrđene odluke
- objašnjenje pacijentu
- praćenje
- ishod
- zatvaranje, nadzor ili administrativni završetak
- audit dokaz

Program 1 definira idealni klinički tok prije daljnje implementacije.

## 2. Arhitektonska Teza

ASTRA mora biti klinički operativni sustav, ne još jedan kalendar s bilješkama i ne još jedan EMR clone.

Klinički workflow počinje kada postoji klinički razlog:

- upit pacijenta
- uputnica
- rezervirana usluga
- uploadani dokument
- prethodni nalaz
- zakazani termin
- otvoreno kliničko pitanje

Workflow ne počinje tek fizičkim ulaskom pacijenta u kliniku.

Workflow ne završava odlaskom pacijenta iz ordinacije. Završava kada je kliničko pitanje razriješeno, pacijent stavljen u nadzor, upućen dalje, odustao, izgubljen iz praćenja ili administrativno zatvoren uz razlog.

## 3. Neupitna Načela

Program 1 čuva načela iz Architecture Bible:

- čovjek je iznad softvera
- jedan izvor istine
- jedan jezik kroz sustav
- modularnost
- API-first
- AI je pomoćnik
- sve važno je auditabilno
- liječnik odlučuje

AI smije predlagati, strukturirati, podsjećati i pripremati.

AI ne smije samostalno dijagnosticirati, liječiti, zatvarati epizode, slati kliničke zaključke ili stvarati službenu kliničku istinu.

## 4. Odnos Prema Trenutnom Stanju

Trenutni temelj je Patient Clinical Knowledge Layer.

To ostaje ispravno.

Razlog je jednostavan: stvarna skrb je fragmentirana. Pacijent može imati konzultaciju u ASTRA-i, gastroskopiju drugdje, patologiju iz bolnice, laboratorij iz treće ustanove i kontrolu kasnije.

Ispravan redoslijed je:

1. source-linked patient knowledge
2. pregledani klinički sažeci
3. otvorena pitanja i nerazriješeni nalazi
4. buduće grupiranje u epizode
5. budući workflow engine
6. budući specijalistički protokoli

ASTRA prvo mora znati što je poznato i odakle to dolazi. Tek tada to smije organizirati u epizode i workflowe.

## 5. Cjelovite Faze Workflowa

Program 1 koristi ove faze:

1. Pre-arrival / Pre-contact intelligence
2. Check-in / Arrival
3. Clinical Readiness Gate
4. Consultation / Physician Encounter
5. Procedure / Treatment Execution
6. Medical Note and Patient Explanation
7. Findings Lifecycle
8. Plan, Tasks and Follow-up
9. Outcome and Monitoring
10. Episode Closure / Long-term Surveillance

Detalji faza definirani su u:

- `PROGRAM_1_PATIENT_JOURNEY_MODEL.md`
- `PROGRAM_1_FINDINGS_LIFECYCLE.md`
- `PROGRAM_1_EPISODE_BASED_CARE_MODEL.md`

## 6. Clinical Readiness Gate

Clinical Readiness Gate je pacijent/usluga/postupak specifična spremnost.

To nije isto što i postojeći ASTRA Readiness Model.

Postojeći readiness:

- čita demo/pilot operativnu spremnost
- pomaže release i pilot odluci
- nije compliance
- nije medicinska certifikacija

Clinical Readiness Gate:

- procjenjuje je li konkretan pacijent spreman za konkretan klinički čin
- dio je kliničkog workflowa
- nije pravna/compliance certifikacija
- može imati liječnički override uz dokumentiran razlog

Statusi:

- `ready`
- `ready_with_warning`
- `not_ready`
- `needs_physician_review`
- `needs_nurse_action`
- `needs_missing_document`
- `needs_consent`
- `needs_rescheduling`

Primjeri gastroenterologije:

- natašte status
- kvaliteta pripreme crijeva
- antikoagulansi/antiagregacijski lijekovi
- alergije
- pratnja za sedaciju
- prethodna kolonoskopija i patologija
- pristanak za endoskopiju/sedaciju/polipektomiju
- potreba za bolničkim okruženjem kod višeg rizika

Primjeri estetske medicine:

- trudnoća/dojenje
- aktivna infekcija ili herpes
- antikoagulansi
- raniji filleri i nepoznati materijal
- nerealna očekivanja
- ranije komplikacije
- potreba za fotografijama
- pristanak za injektabilni ili energy-based tretman
- batch/lot dokumentacija

## 7. Shared Core, Specialty Templates

I gastroenterologija i estetska medicina koriste isti workflow core:

- pacijent
- razlog dolaska
- dokumenti i izvori
- spremnost
- termin
- pružatelj
- soba
- usluga
- klinički čin
- materijal/proizvod
- nalaz
- preporuka
- follow-up
- audit

Razlike pripadaju predlošcima i protokolima, ne dupliciranoj arhitekturi.

## 8. Dva Izlaza Svakog Kliničkog Čina

Svaki završeni klinički čin treba moći proizvesti:

1. Medical Note

   Profesionalna, strukturirana, klinički i pravno korisna dokumentacija.

2. Patient Explanation

   Jasno objašnjenje pacijentu: što je učinjeno, što je nađeno, što to znači, što treba napraviti, što se čeka, kada se javiti i koji su alarmni simptomi.

AI može pripremiti oba izlaza.

Liječnik ih mora potvrditi prije finalizacije ili slanja.

Patient Explanation je strateška razlika ASTRA-e: sustav ne smije samo proizvoditi dokument, nego mora pomagati pacijentu da razumije put liječenja.

## 9. Clinical Evidence Loop

Program 1 proširuje Operational Evidence Loop u klinički tok:

`Clinical risk / clinical need -> Workspace -> physician-confirmed action -> Audit -> outcome evidence`

Primjer:

Patologija stigla -> Patient Workspace pokazuje otvoreno pitanje -> liječnik pregleda izvor -> potvrdi zaključak ili plan -> audit -> pacijent dobije objašnjenje -> follow-up ili nadzor.

## 10. Anti-Patterns

ASTRA ne smije postati:

- generički EMR clone
- groblje PDF-ova
- kalendar s bilješkama
- form-heavy sustav koji krade vrijeme liječniku
- AI liječnik
- autonomni dijagnostički engine
- billing-first sustav
- episode engine bez source-linked patient knowledge
- workflow engine koji ignorira vanjske nalaze
- sustav koji zatvara skrb dok patologija/lab/radiologija ostaju nerazriješeni
- sustav koji šalje medicinske zaključke pacijentu bez liječničke potvrde

## 11. Sigurnost I Granice

Program 1 ne uvodi stvarne pacijentove podatke.

ASTRA Clinic Core ostaje demo/pilot sustav:

- nije certificirani EMR
- nije medicinski uređaj
- nije production-ready za stvarnu kliničku uporabu
- nema stvarnu hrvatsku fiskalizaciju

## 12. Dokumentacijski Paket

Program 1 čine:

- `PROGRAM_1_ASTRA_CLINICAL_WORKFLOW.md`
- `PROGRAM_1_PATIENT_JOURNEY_MODEL.md`
- `PROGRAM_1_EPISODE_BASED_CARE_MODEL.md`
- `PROGRAM_1_FINDINGS_LIFECYCLE.md`
- `PROGRAM_1_AI_GOVERNANCE_MODEL.md`
- `PROGRAM_1_IMPLEMENTATION_ROADMAP.md`

Ovaj paket je arhitektura-first. Ne implementira nove modele, migracije, API-je, React stranice ni UI komponente.
