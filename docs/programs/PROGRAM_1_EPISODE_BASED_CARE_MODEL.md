# Program 1 - Episode-Based Care Model

Status: budući model, Episode Engine ostaje experimental/deferred

## 1. Svrha

Episode-Based Care opisuje kako ASTRA kasnije može organizirati skrb oko kliničke priče.

Ovaj dokument ne vraća Episode Engine u primarni workflow.

Primarni temelj ostaje Patient Clinical Knowledge Layer.

## 2. Zašto Epizoda Ne Smije Doći Prerano

Epizoda bez pouzdanog patient knowledge sloja postaje samo spremnik termina.

To je opasno jer stvarna skrb često dolazi izvan klinike:

- vanjska endoskopija
- bolnička patologija
- privatni laboratorij
- uputnica
- otpusno pismo
- fotografije
- skenirani dokumenti
- pacijentovi uploadi

Ako ASTRA prvo ne zna izvore i kliničke činjenice, epizoda može stvoriti lažni osjećaj reda.

## 3. Ispravan Redoslijed

1. Source-linked patient knowledge
2. Pregledani Clinical Documents
3. Patient Clinical Summary
4. Open questions / unresolved findings
5. Buduće episode grouping
6. Budući workflow engine
7. Budući specialty protocols

Epizoda je organizacijski sloj iznad znanja, ne izvor istine.

## 4. Što Je Klinička Epizoda

Klinička epizoda je vremenski i klinički okvir oko problema, cilja, tretmana, nadzora ili follow-up procesa.

Epizoda nije:

- termin
- dijagnoza
- račun
- dokument
- AI plan
- workflow engine

Epizoda može kasnije povezati:

- pregledane dokumente
- termine
- postupke
- planove
- zadatke
- nalaze
- račune
- materijalnu potrošnju
- ishode
- komunikaciju pacijentu

## 5. Minimalni Budući Model Epizode

Epizoda bi trebala imati:

- pacijent
- naslov
- tip
- status
- prioritet
- početak
- završetak
- razlog otvaranja
- kliničko pitanje
- cilj skrbi
- sažetak
- odgovorni provider
- povezani izvori
- otvorena pitanja
- aktualni plan
- ishod
- razlog zatvaranja
- audit

## 6. Budući Statusi

Predloženi statusi:

- `open`
- `active`
- `waiting_for_result`
- `follow_up_needed`
- `stable`
- `completed`
- `surveillance`
- `referred`
- `declined`
- `lost_to_follow_up`
- `administratively_closed`

Status ne smije biti samo dekoracija. Mora odgovarati stvarnom stanju skrbi.

## 7. Primjeri Gastroenterologije

### GERB/refluks

Izvori:

- konzultacija
- vanjska gastroskopija
- H. pylori status
- terapijska preporuka

Otvorena pitanja:

- odgovor na terapiju
- potreba za kontrolom
- alarmni simptomi

Zatvaranje:

- simptomi stabilni
- plan kontrole dogovoren
- pacijent informiran

### Nadzor Polipa Debelog Crijeva

Izvori:

- kolonoskopija
- patologija
- kvaliteta pripreme
- broj/veličina/tip polipa

Otvorena pitanja:

- patologija pending
- interval nadzora nije potvrđen

Zatvaranje ili surveillance:

- patologija pregledana
- surveillance interval potvrđen
- pacijent dobio objašnjenje

## 8. Primjeri Estetske Medicine

### Filler / Biostimulator

Izvori:

- konzultacija
- fotografije
- pristanak
- proizvod i batch/lot
- tretirana regija
- komplikacije ako postoje

Otvorena pitanja:

- kontrola fotografije
- touch-up
- nuspojava

Zatvaranje:

- tretman završen
- kontrola obavljena
- pacijent zadovoljan ili daljnji plan dokumentiran

## 9. Odnos Prema ClinicalPlan

ClinicalPlan ostaje liječnički potvrđena usmjerenost skrbi.

AI smije predložiti plan.

Liječnik potvrđuje, uređuje ili odbija.

Epizoda ne smije promijeniti službeni plan bez liječničke potvrde.

## 10. Odnos Prema Findings Lifecycle

Nalaz može:

- otvoriti novo pitanje
- promijeniti status epizode
- stvoriti follow-up potrebu
- potvrditi ishod
- omogućiti zatvaranje

Ali samo pregledani nalaz i liječnički potvrđena odluka smiju promijeniti službeni smjer skrbi.

## 11. Kada Reaktivirati Episode Engine

Episode Engine se može vratiti iz deferred statusa tek kada:

- ClinicalDocument lifecycle bude stabilan
- Patient Clinical Summary bude koristan i pregledan
- open questions budu jasno modelirana
- Findings Lifecycle bude auditabilan
- Clinical Readiness Gate bude konceptualno jasan
- liječničke odluke imaju lifecycle

## 12. Anti-Patterns

Ne smije se dogoditi:

- epizoda kao nova forma za administraciju
- epizoda kao dijagnoza
- epizoda koja ignorira vanjske nalaze
- epizoda koja zatvara skrb dok patologija čeka pregled
- epizoda koju AI zatvara autonomno
- epizoda koja postaje primarni izvor istine umjesto source-linked dokumenta
