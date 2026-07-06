# Program 1 - Findings Lifecycle

Status: arhitektonski lifecycle, bez implementacije u ovom zadatku

## 1. Svrha

Nalaz u ASTRA-i nije mrtvi privitak.

Nalaz je aktivni klinički događaj koji može promijeniti ono što znamo o pacijentu, otvoriti pitanje, potvrditi plan, tražiti follow-up ili omogućiti zatvaranje skrbi.

## 2. Što Se Smatra Nalazom

Findings uključuju:

- interne konzultacijske bilješke
- interne proceduralne izvještaje
- vanjske endoskopske izvještaje
- patologiju
- laboratorij
- radiologiju/slikovne nalaze
- otpusna pisma
- uputnice
- fotografije
- skenirane dokumente
- pacijentove uploadane dokumente
- pacijentove izvještaje o simptomima ili tijeku

## 3. Osnovni Lifecycle

1. Received / created
2. Classified
3. Linked to patient
4. Linked to appointment and/or future episode where appropriate
5. Raw source preserved
6. AI extraction proposed
7. Physician reviews extraction
8. Accepted findings become official source-linked patient knowledge
9. Unresolved items become open clinical questions
10. Physician-confirmed decision or task is generated
11. Patient is informed where appropriate
12. Audit evidence is written
13. Finding is closed, superseded, or remains open

## 4. Received / Created

Nalaz može nastati:

- u ASTRA-i tijekom konzultacije
- u ASTRA-i tijekom postupka
- uploadom pacijenta
- skeniranjem
- unosom recepcije ili sestre
- ručnim unosom liječnika
- budućom integracijom iz vanjskog sustava

U demo/pilot modu ne smiju se koristiti stvarni pacijentovi podaci.

## 5. Classified

Nalaz se klasificira po tipu:

- consultation
- procedure
- endoscopy
- pathology
- laboratory
- radiology
- discharge
- referral
- photograph
- other

Klasifikacija pomaže workflowu, ali ne stvara kliničku istinu.

## 6. Linked To Patient

Svaki nalaz mora pripadati poznatom pacijentu.

Nalaz bez pacijenta je operativni problem, ne klinička činjenica.

Identitet pacijenta mora biti provjerljiv kroz ime, prezime, datum rođenja, OIB ako postoji, telefon ili e-mail.

## 7. Raw Source Preserved

Izvor se mora očuvati.

AI sažetak nije zamjena za izvor.

Korisnik mora moći otvoriti originalni dokument ili zapis koji podupire tvrdnju.

## 8. AI Extraction Proposed

AI smije predložiti:

- sažetak
- ključne nalaze
- preporuke
- otvorena pitanja
- rizike
- relevantnost za postojeći klinički kontekst

AI ne smije:

- izmišljati podatke
- prešutjeti nesigurnost
- označiti nalaz pregledanim
- stvoriti službenu dijagnozu
- zatvoriti pitanje ili epizodu

## 9. Physician Review

Liječnik može:

- prihvatiti ekstrakciju
- urediti ekstrakciju
- odbiti ekstrakciju
- označiti dio kao klinički nerelevantan
- odgoditi pregled
- otvoriti kliničko pitanje
- pretvoriti zaključak u plan ili zadatak

Tek nakon liječničkog pregleda nalaz smije doprinositi službenom patient knowledge sloju.

## 10. Source-Linked Patient Knowledge

Službena tvrdnja mora imati izvor.

Primjer:

Tvrdnja: `Tubularni adenom prethodno dokumentiran`

Izvori:

- patologija 10.07.2026.
- kolonoskopija 06.07.2026.

Ako tvrdnja nema izvor, ne smije se prikazivati kao službena klinička činjenica.

## 11. Open Clinical Questions

Nalaz može otvoriti pitanje:

- patologija pending
- H. pylori status nepoznat
- interval nadzora nije potvrđen
- vanjski nalaz kontradiktoran
- estetski materijal nepoznat
- nuspojava zahtijeva kontrolu

Open question nije task sam po sebi. Task nastaje tek kada liječnik ili ovlašteni korisnik potvrdi sljedeći korak.

## 12. Decisions And Tasks

Nalaz može dovesti do liječnički potvrđene odluke:

- kontrola za 3 godine
- ponoviti laboratorij
- čekati patologiju
- uputiti u bolnicu
- naručiti kontrolnu fotografiju
- napraviti touch-up
- zatvoriti pitanje kao klinički nerelevantno

Zadaci moraju proizlaziti iz potvrđene odluke, ne iz sirovog AI prijedloga.

## 13. Patient Communication

Kada je nalaz relevantan za pacijenta, ASTRA treba podržati razumljivo objašnjenje.

Patient Explanation mora reći:

- što je nađeno
- što to znači
- što se čeka
- što pacijent treba učiniti
- kada se javiti
- koji su alarmni simptomi

AI smije draftati objašnjenje.

Liječnik potvrđuje prije slanja ili finalizacije.

## 14. Audit Evidence

Audit mora moći rekonstruirati:

- tko je zaprimio nalaz
- kada je nalaz zaprimljen
- koji izvor postoji
- što je AI predložio
- tko je pregledao
- što je prihvaćeno ili odbijeno
- koji plan ili zadatak je nastao
- je li pacijent informiran

Audit nije samo tehnički log. To je dokaz kliničkog toka.

## 15. Closure States

Nalaz može završiti kao:

- reviewed
- rejected
- superseded
- clinically_irrelevant
- open_question
- action_required
- action_completed
- archived

Zatvaranje nalaza ne smije zatvoriti skrb ako postoje nerazriješena povezana pitanja.

## 16. Gastroenterološki Primjeri

Patologija nakon polipektomije:

- received
- classified as pathology
- linked to patient
- AI extracts adenoma information
- physician reviews
- surveillance interval confirmed
- patient explanation generated
- recall or follow-up planned
- finding closed as action_completed

H. pylori:

- nalaz navodi pozitivan status
- liječnik potvrđuje plan
- test of cure needed postaje otvoreno pitanje
- zatvara se tek nakon negativnog testa

## 17. Estetski Primjeri

Fotografija kontrole:

- received
- linked to tretman
- liječnik pregleda
- ishod se označi kao satisfied, touch_up_needed ili complication_follow_up

Nepoznati filer:

- vanjski podatak zaprimljen
- AI upozorava na rizik
- liječnik potvrđuje da je potreban oprez ili odgoda
- patient explanation pripremljen

## 18. Granice

Ovaj dokument ne implementira OCR.

Ovaj dokument ne uvodi stvarni AI provider.

Ovaj dokument ne stvara diagnosis engine.

On definira lifecycle koji buduća implementacija mora poštovati.
