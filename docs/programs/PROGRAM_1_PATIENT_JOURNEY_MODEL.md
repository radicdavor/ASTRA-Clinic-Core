# Program 1 - Patient Journey Model

Status: arhitektonski model, bez implementacije u ovom zadatku

## 1. Svrha

Patient Journey Model definira puni put pacijenta kroz ASTRA Clinical Workflow.

Put pacijenta ne počinje fizičkim dolaskom u kliniku i ne završava izlaskom iz ordinacije.

Počinje kada postoji klinički razlog, a završava kada je taj razlog razriješen, prebačen, stavljen u nadzor ili administrativno zatvoren.

## 2. Phase 0 - Pre-arrival / Pre-contact Intelligence

Svrha: pripremiti klinički kontekst prije dolaska.

Ulazi:

- razlog naručivanja
- odabrana usluga
- prethodni interni podaci
- vanjski nalazi
- dokumenti koje je pacijent učitao
- uputnica
- lijekovi
- alergije
- antikoagulansi/antiagregacijski lijekovi
- komorbiditeti
- raniji postupci ili tretmani
- očekivanja pacijenta
- red flags

AI smije:

- sažeti postojeći kontekst
- prepoznati nedostajuće informacije
- predložiti intake pitanja
- upozoriti na moguće rizike
- predložiti koji dokumenti trebaju liječnički pregled

Liječnik ne mora potvrditi svaki intake podatak.

Liječnik potvrđuje samo klinički relevantne AI zaključke ili odluke.

Administracija i sestra smiju:

- provjeriti identitet
- prikupiti dokumente
- provjeriti osnovnu spremnost
- poslati pripremne upute gdje je primjenjivo

## 3. Phase 1 - Check-in / Arrival

Svrha: evidentirati da je pacijent fizički prisutan i provjeriti može li planirana usluga sigurno početi.

Mora uključiti:

- arrival status
- provjeru identiteta
- potvrdu termina i usluge
- status pripreme
- status pristanka
- nedostajuće dokumente
- sigurnosne zastavice
- naplatnu pripremu samo gdje je relevantno
- link na Patient Workspace
- link na Appointment Workspace

Recepcija ne stvara kliničku istinu.

Recepcija organizira dolazak, identitet i resurse.

## 4. Phase 2 - Clinical Readiness Gate

Svrha: procijeniti spremnost pacijenta za konkretan klinički čin.

Statusi:

- `ready`
- `ready_with_warning`
- `not_ready`
- `needs_physician_review`
- `needs_nurse_action`
- `needs_missing_document`
- `needs_consent`
- `needs_rescheduling`

Clinical Readiness Gate je odvojen od demo/pilot Readiness Modela.

Primjeri gastroenterologije:

- natašte status
- priprema crijeva
- antikoagulansi/antiagregansi
- alergije
- pratnja za sedaciju
- pristanak za endoskopiju/sedaciju/polipektomiju
- raniji nalazi relevantni za današnji postupak

Primjeri estetske medicine:

- trudnoća/dojenje
- aktivna infekcija ili herpes
- prethodni filleri
- antikoagulansi
- nerealna očekivanja
- fotografije prije tretmana
- pristanak
- batch/lot potreba

Liječnik može potvrditi nastavak uz upozorenje ako je to medicinski opravdano i dokumentirano.

## 5. Phase 3 - Consultation / Physician Encounter

Svrha: dati liječniku fokusirani prostor za razmišljanje.

Patient Workspace mora odgovoriti:

- zašto je pacijent danas ovdje
- što znamo
- što ostaje nerazriješeno
- koji dokumenti to podupiru
- koji rizici su relevantni
- koji je vjerojatni plan
- što treba liječničku potvrdu

AI smije predložiti:

- strukturirana anamnestička pitanja
- relevantne prethodne nalaze
- diferencijalna razmatranja
- nedostajuće podatke
- draft kliničke bilješke
- draft plana
- draft objašnjenja pacijentu
- follow-up prijedloge

Liječničke radnje nad prijedlogom:

- prihvati
- uredi
- odbij
- označi kao klinički nerelevantno
- odgodi
- pretvori u plan
- pretvori u uputu pacijentu

## 6. Phase 4 - Procedure / Treatment Execution

Svrha: dokumentirati što je stvarno učinjeno, zašto, kako, s kojim materijalom i s kojim neposrednim rezultatom.

Zajednička jezgra:

- indikacija
- pacijent
- termin
- usluga
- provider
- soba
- početak/kraj
- klinički kontekst
- readiness status u trenutku postupka
- potvrda pristanka
- izvedeni postupak/tretman
- nalazi
- materijal/proizvod
- batch/lot/rok gdje je relevantno
- komplikacije
- neposredna preporuka
- follow-up plan
- dokumenti generirani tijekom postupka
- audit

Gastroenterologija:

- gastroskopija
- kolonoskopija
- biopsija
- polipektomija
- H. pylori testiranje
- patologija naručena
- kvaliteta pripreme
- BBPS
- dosegnuti segment
- withdrawal time
- polip lokacija/veličina/morfologija
- metoda resekcije
- retrieval status
- interval nadzora nakon potvrde patologije

Estetska medicina:

- filler
- botulinum toxin
- polinukleotidi / PDRN / PN-HPT
- biostimulator
- mezoterapija
- energy-based tretman
- tretirana regija
- proizvod
- količina
- tehnika
- dubina
- kanila/igla
- fotografije prije/poslije
- nuspojave
- touch-up plan
- maintenance plan

## 7. Phase 5 - Medical Note And Patient Explanation

Svrha: odvojiti profesionalni zapis od razumljivog objašnjenja pacijentu.

Medical Note:

- profesionalan
- strukturiran
- klinički i pravno koristan
- namijenjen liječniku i medicinskom zapisu

Patient Explanation:

- razumljiv
- kratak
- izvediv
- ne infantilizira pacijenta
- objašnjava nalaz, značenje, što učiniti, što se čeka, alarmne simptome i kontrolu

AI smije draftati oba izlaza.

Liječnik potvrđuje prije finalizacije ili slanja.

## 8. Phase 6 - Findings Lifecycle

Nalazi su aktivni klinički događaji, ne mrtvi privitci.

Detaljan model je u `PROGRAM_1_FINDINGS_LIFECYCLE.md`.

## 9. Phase 7 - Plan, Tasks And Follow-up

Svrha: pretvoriti liječnički potvrđene odluke u sljedeće korake.

Task owners:

- pacijent
- liječnik
- sestra
- recepcija/administracija
- sustav/AI assistant

Primjeri zadataka pacijenta:

- uzeti terapiju
- napraviti laboratorij
- učitati nalaz
- doći na kontrolu
- javiti simptome
- poslati fotografiju
- slijediti pripremu

Primjeri zadataka klinike:

- pregledati patologiju
- nazvati pacijenta
- poslati objašnjenje
- naručiti follow-up
- pripremiti pristanak
- pripremiti materijal
- provjeriti neplaćeni račun
- naručiti inventar

Zadaci trebaju nastati iz liječnički potvrđenih odluka, ne iz sirovog AI prijedloga.

## 10. Phase 8 - Outcome And Monitoring

Svrha: znati je li skrb stvarno završena.

Gastroenterološki ishodi:

- H. pylori eradikacija potvrđena negativnim testom
- patologija pregledana
- interval nadzora potvrđen
- simptomi poboljšani
- pacijent upućen u bolnicu
- kontrola propuštena

Estetski ishodi:

- kontrolna fotografija učinjena
- pacijent zadovoljan
- nuspojava riješena
- touch-up učinjen
- maintenance plan kreiran
- tretman odgođen ili napušten

Ishod mora biti strukturiran, ali ne prekomjerno administrativan.

## 11. Phase 9 - Episode Closure / Long-term Surveillance

Svrha: zatvoriti krug skrbi.

Statusi buduće epizode:

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

Razlozi zatvaranja:

- problem riješen
- tretman završen
- pacijent stavljen u nadzor
- pacijent upućen eksterno
- pacijent odbio liječenje
- pacijent izgubljen iz praćenja
- duplikat/administrativna korekcija
- nedovoljno dokaza za završetak

Zatvaranje treba stvoriti:

- finalni sažetak
- ključne dokaze
- donesene odluke
- status komunikacije pacijentu
- sljedeći recall ako treba
- audit entry

## 12. Granica Ovog Dokumenta

Ovaj dokument ne implementira workflow engine.

On definira operativni model koji buduća implementacija mora poštovati.
