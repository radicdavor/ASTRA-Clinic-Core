# Program 1 - Review Pass 1: Architectural Consistency Audit

Status: dokumentacijski audit arhitektonske konzistentnosti, bez implementacije

## 1. Svrha audita

Ovaj audit provjerava je li Program 1 - ASTRA Clinical Workflow dosljedan postojećim arhitektonskim temeljima ASTRA Clinic Core projekta.

Audit provjerava:

- usklađenost s ASTRA Architecture Bible
- usklađenost s workspace arhitekturom
- očuvanje Patient Clinical Knowledge Layera kao primarnog kliničkog smjera
- odvajanje postojećeg demo/pilot Readiness Modela od budućeg Clinical Readiness Gatea
- proširenje Operational Evidence Loopa prema kliničkom evidence loopu
- unutarnju terminološku konzistentnost Program 1 dokumenata

Ovaj audit nije implementacija.

Ovaj audit nije compliance odobrenje.

Ovaj audit nije produkcijsko odobrenje.

Ovaj audit ne dopušta stvarne pacijentove podatke.

Ovaj audit ne tvrdi da je ASTRA certificirani EMR ili medicinski uređaj.

## 2. Dokumenti uključeni u pregled

### Core platform documents

- `README.md`
- `docs/ASTRA_ARCHITECTURE_BIBLE.md`
- `docs/ASTRA_WORKSPACE_ARCHITECTURE.md`
- `docs/V23_PILOT_RELEASE_CANDIDATE.md`

### Patient knowledge documents

- `docs/ASTRA_PATIENT_CLINICAL_KNOWLEDGE_MODEL.md`
- `docs/PATIENT_CLINICAL_KNOWLEDGE_LAYER_MVP.md`
- `docs/PATIENT_CLINICAL_SUMMARY_MVP.md`

### Readiness/evidence documents

- `docs/ASTRA_READINESS_MODEL.md`
- `docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md`

### Program 1 documents

- `docs/programs/PROGRAM_1_ASTRA_CLINICAL_WORKFLOW.md`
- `docs/programs/PROGRAM_1_PATIENT_JOURNEY_MODEL.md`
- `docs/programs/PROGRAM_1_EPISODE_BASED_CARE_MODEL.md`
- `docs/programs/PROGRAM_1_FINDINGS_LIFECYCLE.md`
- `docs/programs/PROGRAM_1_AI_GOVERNANCE_MODEL.md`
- `docs/programs/PROGRAM_1_IMPLEMENTATION_ROADMAP.md`

## 3. Sažetak nalaza

Program 1 je smjerno usklađen s ASTRA Architecture Bible.

Program 1 čuva:

- završnu odgovornost liječnika
- AI kao pomoćni sloj, ne kao donositelja odluka
- source-linked patient knowledge
- pacijent-centrični klinički tok
- modularnu arhitekturu
- auditabilnost važnih događaja
- evidence loop razmišljanje
- Episode Engine kao budući, deferred organizacijski sloj

Nisu pronađene visoko rizične kontradikcije koje bi blokirale sljedeći arhitektonski korak.

Potrebna su buduća pojašnjenja u tri područja:

- terminološko zaključavanje između `ClinicalDocument`, `Finding`, `Patient Clinical Summary`, `ClinicalPlan` i `Task`
- jasnija granica između postojećeg ASTRA Readiness Modela i budućeg Clinical Readiness Gatea
- precizniji kriteriji za buduće Episode Closure i Outcome Evidence

Preporuka je: Go with corrections za sljedeći arhitektonski korak, ne za produkciju.

## 4. Alignment with Architecture Bible

| Principle | Status | Evidence from Program 1 | Risk or clarification needed |
| --- | --- | --- | --- |
| Čovjek iznad softvera | aligned | Program 1 naglašava da workflow postoji da liječniku da fokusirani prostor za razmišljanje i da pacijentu objasni put skrbi. | Budući UI ne smije pretvoriti klinički workflow u prekomjerne forme. |
| Jedan izvor istine | aligned | Program 1 i Patient Clinical Knowledge Model postavljaju `ClinicalDocument` i source-linked tvrdnje kao temelj službenog znanja. | Treba zaključati da `Finding` nije odvojeni izvor istine nego strukturirani zaključak iz izvora. |
| Jedan jezik kroz sustav | partially aligned | Program 1 koristi zajedničke pojmove: pacijent, termin, dokument, nalaz, audit, epizoda. | Postoji terminološki drift između `Finding`, `Clinical Finding`, `External Finding`, `Patient Clinical Summary` i `Patient Clinical Knowledge`. Potreban je rječnik. |
| Modularnost | aligned | Program 1 tretira gastroenterologiju i estetsku medicinu kao specialty templates na shared core modelu, ne kao duplicirane module. | Budući specialty templates ne smiju zaobići shared core objekte. |
| API-first | needs clarification | Program 1 je arhitektonski model i ne opisuje API contract. Ne proturječi API-first načelu. | Prije implementacije treba definirati API contract za dokumente, review, open questions, patient explanation i budući readiness gate. |
| AI kao pomoćnik | aligned | AI Governance Model jasno kaže: AI proposes, Physician confirms, ASTRA records both. | Treba osigurati da UI nikada ne prikaže AI prijedlog kao službeni plan ili službenu činjenicu. |
| Audit svega važnog | aligned | Findings Lifecycle i AI Governance zahtijevaju audit za AI prijedlog, pregled, prihvaćanje, odbijanje, odluke i komunikaciju pacijentu. | Budući audit događaji trebaju imati konzistentnu semantiku i razlikovati tehnički log od kliničkog evidence traga. |
| Liječnik odlučuje | aligned | Program 1 zabranjuje autonomno dijagnosticiranje, zatvaranje epizoda i slanje medicinskih zaključaka bez potvrde. | Treba pojasniti koje radnje može potvrditi sestra/administracija, a koje isključivo liječnik. |

## 5. Alignment with Workspace Architecture

Program 1 je uglavnom usklađen s workspace arhitekturom jer ne uvodi nasumične nove ekrane kao primarni smjer.

### Patient Workspace

Usklađeno.

Patient Workspace ostaje primarna klinička površina. Program 1 ga koristi za odgovor na pitanja:

- što znamo o pacijentu
- što ostaje nerazriješeno
- koji izvori podupiru tvrdnje
- što zahtijeva liječničku potvrdu

Ovo je usklađeno s odlukom da Patient Clinical Knowledge dolazi prije Episode Enginea.

### Appointment Workspace

Usklađeno uz buduće pojašnjenje.

Program 1 predviđa da Appointment Workspace može prikazati kliničku spremnost, status postupka, materijal, nalaze i audit. To odgovara object-centered pristupu.

Rizik: Clinical Readiness Gate se ne smije implementirati kao zasebni generički dashboard prije nego bude jasno povezan s pacijentom, terminom, uslugom i izvorima.

### Reception Workspace

Usklađeno.

Program 1 jasno kaže da recepcija ne stvara kliničku istinu. Reception Workspace organizira dolazak, identitet i resurse.

### Episode Workspace

Usklađeno, ali treba čuvati granicu.

Workspace Architecture označava Episode Workspace kao `experimental/deferred`. Program 1 Episode-Based Care Model ponavlja da Episode Engine ne smije postati primarni workflow prije stabilnog Patient Clinical Knowledge Layera.

Rizik je terminološki: Program 1 koristi `Episode Closure / Long-term Surveillance` kao fazu idealnog toka. To treba čitati kao budući model, ne kao trenutni implementacijski zahtjev.

### Future Inventory Item Workspace

Usklađeno.

Program 1 spominje materijal/proizvod, batch/lot i potrošnju kao dio kliničkog čina gdje je relevantno. To podržava budući Inventory Item Workspace bez uvođenja novog medicinskog modula.

### Future Purchase Order Workspace

Usklađeno.

Program 1 ne širi nabavu u klinički workflow. Purchase Order Workspace ostaje buduća operativna površina za resurse, ne klinički izvor istine.

## 6. Alignment with Patient Clinical Knowledge Model

Ovo je najvažnija provjera.

Program 1 poštuje trenutnu arhitektonsku odluku:

1. source-linked patient knowledge
2. reviewed clinical summaries
3. unresolved findings / open questions
4. future episode grouping
5. future workflow engine
6. future specialty protocols

Evidence:

- `PROGRAM_1_ASTRA_CLINICAL_WORKFLOW.md` izričito kaže da je trenutni temelj Patient Clinical Knowledge Layer.
- `PROGRAM_1_EPISODE_BASED_CARE_MODEL.md` kaže da Episode-Based Care ne vraća Episode Engine u primarni workflow.
- `PROGRAM_1_IMPLEMENTATION_ROADMAP.md` stavlja Patient Knowledge Stabilization prije Findings Lifecycle, Clinical Readiness Gatea, Episode reintroductiona i Workflow Enginea.
- Patient knowledge dokumenti definiraju `ClinicalDocument` kao source object i zabranjuju unsourced AI statements kao službenu istinu.

Zaključak: Program 1 ne tretira Episode Engine kao trenutni primarni workflow.

Potrebno pojašnjenje: `Episode Closure / Long-term Surveillance` u Patient Journey Modelu treba u budućem glossaryju označiti kao buduću epizodnu sposobnost, ne kao trenutnu funkciju.

## 7. Alignment with Readiness Model

Program 1 uglavnom jasno odvaja dva readiness pojma.

### Existing ASTRA Readiness Model

Postojeći ASTRA Readiness Model je:

- demo/pilot operativna spremnost
- pre-demo cockpit
- release/demo signal
- nije compliance
- nije real-data approval
- nije medicinska certifikacija

### Program 1 Clinical Readiness Gate

Clinical Readiness Gate je:

- pacijent/usluga/postupak specifična spremnost
- dio kliničkog workflowa
- potencijalni utjecaj na to smije li konkretni klinički čin nastaviti
- i dalje nije pravna certifikacija
- zahtijeva liječnički override ili potvrdu gdje je primjenjivo

Zaključak: konceptualna razlika postoji i dobro je zapisana.

Rizik: oba pojma koriste riječ `readiness`. Budući UI i API moraju izbjegavati dvosmislenost nazivima poput `Operational Readiness` za postojeći cockpit i `Clinical Readiness Gate` za pacijent/procedura kontekst.

## 8. Alignment with Operational Evidence Loop

Program 1 uspješno proširuje:

`Readiness -> Workspace -> Action -> Audit -> Pilot/Release evidence`

u kliničku verziju:

`Clinical need/risk -> Workspace -> Physician-confirmed action -> Audit -> Outcome evidence`

Ocjena konceptualne jasnoće:

- audit evidence: aligned; Program 1 zahtijeva rekonstruiranje tko, što, kada, izvor, AI prijedlog i ljudsku potvrdu
- physician confirmation: aligned; jasno je da AI prijedlog nije službena odluka
- patient explanation: aligned; slanje/finalizacija traži potvrdu
- finding review: aligned; nalaz postaje službeni tek nakon pregleda
- outcome evidence: partially aligned; postoje primjeri ishoda, ali treba formalizirati minimalni outcome zapis
- episode closure: partially aligned; opisani su razlozi zatvaranja, ali budući kriteriji trebaju rječnik i status model

Zaključak: Program 1 daje dobar klinički nastavak Operational Evidence Loopa, ali prije implementacije treba zaključati statuse i minimalni evidence payload za ishode.

## 9. Internal consistency of Program 1

Program 1 dokumenti su međusobno uglavnom konzistentni. Najvažnija interna linija je očuvana:

`ClinicalDocument -> reviewed source-linked knowledge -> open questions -> physician-confirmed decision/task -> future episode/workflow`

Terminološki rizici:

| Term | Problem or ambiguity | Preferred canonical term |
| --- | --- | --- |
| Patient | Konzistentan pojam. | `Patient` / `Pacijent` |
| Patient Workspace | Konzistentan kao primarna klinička površina. | `Patient Workspace` |
| ClinicalDocument | Jasan kao source object, ali treba ga zaključati kao primarni izvor za dokumentirane tvrdnje. | `ClinicalDocument` |
| Finding | Koristi se široko za nalaz, zaključak, dokumentirani događaj i izvod iz dokumenta. | `Finding` kao source-linked reviewed clinical finding |
| Clinical Finding | Nije dosljedno odvojen od `Finding`. | Izbjegavati dok se ne definira; koristiti `Finding` |
| External Finding | Može se miješati s vanjskim dokumentom. | `External ClinicalDocument` plus `Finding` izveden iz njega |
| Internal Finding | Može se miješati s internim dokumentom. | `Internal ClinicalDocument` plus `Finding` izveden iz njega |
| Patient Clinical Knowledge | Konzistentan kao širi sloj znanja. | `Patient Clinical Knowledge` |
| Patient Clinical Summary | Konzistentan kao pregledni sažetak, ali treba jasno ostati izveden iz reviewed dokumenata. | `Patient Clinical Summary` |
| Clinical Episode | Dobro definiran kao budući organizacijski sloj. | `Clinical Episode` |
| Episode-Based Care | Jasno označen kao budući model. | `Episode-Based Care` |
| ClinicalPlan | Spominje se kao liječnički potvrđena usmjerenost skrbi, ali nije u Program 1 roadmapu razrađen kao trenutni objekt. | `ClinicalPlan` kao budući confirmed care direction |
| Medical Note | Konzistentan kao profesionalni zapis. | `Medical Note` |
| Patient Explanation | Konzistentan kao pacijentu razumljivo objašnjenje. | `Patient Explanation` |
| Clinical Readiness Gate | Jasan, ali ime treba čuvati od miješanja s readiness cockpitom. | `Clinical Readiness Gate` |
| Readiness | Dva značenja. | `Operational Readiness` za cockpit; `Clinical Readiness Gate` za pacijenta/proceduru |
| Task | Djelomično jasan; nastaje iz liječnički potvrđene odluke. | `Task` kao confirmed operational next step |
| Follow-up | Koristi se kao klinički nastavak i potencijalni zadatak. | `Follow-up` kao clinical continuation need |
| Outcome | Primjeri postoje, ali minimalni model nije zaključan. | `Outcome Evidence` |
| Episode Closure | Budući pojam; ne smije djelovati kao sadašnja funkcija. | `Episode Closure` as future confirmed closure event |
| Surveillance | Budući status/nadzor. | `Surveillance` |
| AI Suggestion | Konzistentno draft/proposal. | `AI Suggestion` |
| Physician Review | Konzistentno kao pregled izvora/prijedloga. | `Physician Review` |
| Human Confirmation | Konzistentno, ali treba odvojiti liječničku od administrativne potvrde. | `Physician Confirmation` za kliničke odluke |
| Audit Evidence | Konzistentno kao rekonstrukcija toka. | `Audit Evidence` |

## 10. Contradictions and risks

| Area | Issue | Severity | Why it matters | Recommended correction |
| --- | --- | --- | --- | --- |
| Episode-Based Care | Patient Journey uključuje `Episode Closure / Long-term Surveillance` kao fazu idealnog toka, iako je Episode Engine deferred. | medium | Čitatelj bi mogao pomisliti da je episode closure trenutni implementacijski zahtjev. | U budućem glossaryju označiti `Episode Closure` kao budući epizodni događaj, ne trenutnu MVP funkciju. |
| Terminology | `Finding`, `ClinicalDocument`, `External Finding` i `Internal Finding` mogu se pomiješati. | medium | Bez jasnog jezika sustav može duplicirati izvore ili prikazati izvedenu tvrdnju kao izvor. | Zaključati: `ClinicalDocument` je izvor; `Finding` je reviewana, source-linked klinička tvrdnja izvedena iz izvora. |
| Readiness | `Readiness` i `Clinical Readiness Gate` dijele riječ readiness. | medium | UI/API korisnici mogu pomiješati demo/pilot readiness s kliničkom spremnošću pacijenta. | Koristiti `Operational Readiness` za postojeći cockpit i puni naziv `Clinical Readiness Gate` za klinički kontekst. |
| AI lifecycle | AI Governance definira review statuse, ali veza prema `ClinicalDocument` review statusu i budućem `ClinicalPlan` statusu nije zaključana. | medium | Implementacija bi mogla napraviti tri paralelna lifecyclea koji se razilaze. | U sljedećem glossary/domain passu definirati status mapu: AI Suggestion, Physician Review, Physician Confirmation. |
| Tasks vs ClinicalPlan | Task i ClinicalPlan su povezani, ali granica nije dovoljno oštra. | medium | Sustav bi mogao task prikazati kao klinički plan ili obrnuto. | Definirati: `ClinicalPlan` je confirmed care direction; `Task` je operativni next step koji može proizaći iz plana. |
| Outcome Evidence | Ishodi su opisani primjerima, ali nije definiran minimalni outcome evidence contract. | low | Buduća implementacija može imati nedosljedne ishode po specijalnosti. | Prije implementacije definirati minimalna polja: outcome type, source, confirmed_by, date, related finding/task/episode. |
| Patient Explanation | Dokumenti traže potvrdu prije slanja, što je dobro, ali ne definiraju tko smije potvrditi ne-kliničke administrativne poruke. | low | Administrativne i medicinske poruke mogu imati različitu razinu odgovornosti. | U governance passu odvojiti clinical patient explanation od operational/admin message. |

Nema high-severity kontradikcija u pregledanim dokumentima.

## 11. Recommended terminology lock

Ovo je predloženi početak kanonskog rječnika za budući dokument `PROGRAM_1_GLOSSARY.md`.

| Canonical term | Croatian explanation | Use this for | Avoid using as synonym |
| --- | --- | --- | --- |
| Patient | Osoba oko koje se organiziraju svi klinički i operativni podaci. | Identitet pacijenta, workspace, termini, dokumenti. | Case, episode, account. |
| Patient Workspace | Primarna objektno-centrična površina za pregled pacijenta. | Source-linked znanje, dokumenti, termini, računi, audit. | Dashboard, EMR page, patient file. |
| ClinicalDocument | Izvorni klinički dokument ili zapis iz kojeg se izvode tvrdnje. | Interni/vanjski dokument, patologija, laboratorij, radiologija, upload metadata. | Finding, summary, diagnosis. |
| Finding | Pregledana, source-linked klinička tvrdnja ili nalaz izveden iz izvora. | Ključni nalaz, otvoreno pitanje, relevantan zaključak. | ClinicalDocument, attachment, diagnosis. |
| Patient Clinical Knowledge | Sloj službenog znanja o pacijentu izveden iz pregledanih izvora. | Pitanje što znamo i odakle to znamo. | Episode, plan, diagnosis registry. |
| Patient Clinical Summary | Sažeti pregled pacijentovog source-linked znanja. | Brzu orijentaciju liječnika. | Full EMR, raw document, AI draft. |
| Clinical Episode | Budući organizacijski okvir kliničke priče. | Grupiranje znanja, termina, nalaza, planova i ishoda nakon stabilizacije knowledge sloja. | Diagnosis, appointment, invoice. |
| Episode-Based Care | Budući način organizacije skrbi oko epizoda. | Kasniju organizaciju longitudinalne skrbi. | Current workflow, Workflow Engine. |
| ClinicalPlan | Liječnički potvrđena usmjerenost skrbi. | Budući confirmed care direction i planiranje sljedećih koraka. | AI suggestion, task, diagnosis. |
| Clinical Readiness Gate | Procjena spremnosti konkretnog pacijenta za konkretnu uslugu/postupak. | Kliničku spremnost prije postupka. | Operational Readiness, release readiness. |
| Medical Note | Profesionalni klinički zapis. | Dokumentaciju za liječnika i klinički zapis. | Patient Explanation, AI draft. |
| Patient Explanation | Pacijentu razumljivo objašnjenje nakon liječničke potvrde. | Objašnjenje nalaza, značenja, uputa i alarmnih simptoma. | Medical Note, marketing copy, automated message. |
| Task | Operativni sljedeći korak nastao iz potvrđene odluke. | Radnje pacijenta, liječnika, sestre, recepcije ili sustava. | ClinicalPlan, Finding, Outcome. |
| Outcome Evidence | Dokaz o ishodu ili stanju nakon radnje/skrbnog toka. | Potvrdu poboljšanja, nadzora, pregleda patologije, riješene nuspojave. | Audit log alone, subjective note without source. |
| Episode Closure | Budući potvrđeni događaj zatvaranja ili stavljanja u nadzor. | Zaključivanje kliničke priče uz dokaz i razlog. | Deleting episode, completed appointment. |
| AI Suggestion | AI-generirani prijedlog bez službene snage. | Draft sažetke, extraction, plan prijedloge i objašnjenja. | Official fact, physician decision. |
| Physician Confirmation | Liječnička potvrda kojom prijedlog ili zaključak postaje služben. | Kliničke odluke, planove, objašnjenja i closure. | Admin confirmation, system status. |
| Audit Evidence | Rekonstruktibilan trag važne radnje i odluke. | Tko, što, kada, izvor, AI prijedlog, ljudska potvrda. | UI notification, informal note. |

Preporuka: ne stvarati rječnik u ovom auditu, nego ga izraditi kao sljedeći arhitektonski korak.

## 12. Recommended corrections

Preporučene dokumentacijske korekcije za sljedeći pass:

1. U `PROGRAM_1_PATIENT_JOURNEY_MODEL.md` uz `Episode Closure / Long-term Surveillance` dodati jasnu oznaku da je to budući epizodni sloj, ne trenutna implementacija.
2. U `PROGRAM_1_FINDINGS_LIFECYCLE.md` definirati da je `ClinicalDocument` izvor, a `Finding` izvedena source-linked tvrdnja nakon reviewa.
3. U `PROGRAM_1_AI_GOVERNANCE_MODEL.md` povezati AI review statuse s budućim ClinicalDocument/ClinicalPlan statusima bez dodavanja implementacije.
4. U `PROGRAM_1_ASTRA_CLINICAL_WORKFLOW.md` pojačati naziv `Operational Readiness` za postojeći readiness cockpit.
5. U budućem glossaryju jasno odvojiti `Task`, `ClinicalPlan`, `Follow-up` i `Outcome Evidence`.

U ovom audit passu nisu primijenjene široke izmjene postojećih Program 1 dokumenata.

## 13. Go / No-Go for next architecture step

Recommendation: Go with corrections.

Ovo je preporuka za sljedeći arhitektonski korak, ne za produkciju.

Program 1 je spreman za sljedeći dokumentacijski korak:

`Program 1 - Glossary and Domain Vocabulary Lock`

Razlog:

- temeljni smjer je usklađen s Architecture Bible
- Patient Clinical Knowledge ostaje prije Episode Enginea
- AI governance zadržava liječničku odgovornost
- readiness pojmovi su konceptualno odvojeni, iako terminološki trebaju zaključavanje
- workspace model nije narušen
- nema high-severity kontradikcija

Prije bilo kakve implementacije treba zaključati terminologiju i minimalne lifecycle granice.
