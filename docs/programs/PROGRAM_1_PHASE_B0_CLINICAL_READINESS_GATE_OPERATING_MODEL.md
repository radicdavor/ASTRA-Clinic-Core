# Program 1 Phase B0 - Clinical Readiness Gate Operating Model

Status: documentation-only operating model

## 1. Svrha

Ovaj dokument definira operating model za Clinical Readiness Gate prije bilo kakve implementacije.

Ovaj dokument je:

- documentation-only
- bez backend koda
- bez frontend koda
- bez API endpointa
- bez database modela
- bez UI ekrana
- bez produkcijskog odobrenja
- bez odobrenja za stvarne podatke pacijenata
- bez certified EMR claim
- bez medical-device claim

Svrha je definirati jezik, granice i upravljanje prije nego sto ASTRA dobije bilo kakvu funkciju koja moze utjecati na odluku moze li se planirani klinicki cin provesti.

## 2. Definition

Clinical Readiness Gate je patient/service/procedure-specific gate koji procjenjuje moze li planirani klinicki cin ici dalje u tom trenutku.

Odgovara na pitanje:

`Can this patient proceed with this planned service/procedure/treatment now?`

Clinical Readiness Gate nije:

- postojeci Operational Readiness
- compliance approval
- medical-device decision system
- autonomous AI decision
- Task engine
- Episode engine
- Workflow engine
- zamjena za lijecnicku prosudbu

Clinical Readiness Gate smije organizirati, upozoriti, prikazati nedostatke i traziti potvrdu. Ne smije samostalno donositi medicinsku odluku.

## 3. Core question

Primarno pitanje:

`Moze li ovaj pacijent sada pristupiti ovoj planiranoj usluzi, postupku ili tretmanu?`

Sekundarna pitanja:

- Sto nedostaje?
- Sto je potencijalno nesigurno?
- Sto treba lijecnicki pregled?
- Sto moze provjeriti medicinska sestra?
- Sto moze provjeriti administracija?
- Sto se moze overrideati?
- Sto mora blokirati klinicki cin?
- Sto mora biti dokumentirano?

## 4. Readiness statuses

| Status | Znacenje | Tko moze rijesiti | Smije li postupak ici dalje | Override | Audit |
| --- | --- | --- | --- | --- | --- |
| `ready` | Nema poznatih prepreka prema konfiguriranim pravilima | Sustav prikazuje, odgovorna osoba potvrduje prema toku | Da | Nije potreban | Opcionalan za prikaz, obvezan ako je potvrda dio workflowa |
| `ready_with_warning` | Postoji upozorenje, ali nije automatski blok | Lijecnik, a za neklinicke stavke sestra/admin | Da, ako je upozorenje pregledano | Da | Da, ako je upozorenje prihvaceno ili overrideano |
| `not_ready` | Nedostaje vazan preduvjet ili postoji prepreka | Ovisno o stavci; najcesce lijecnik/sestra/admin | Ne, dok se stavka ne rijesi | Samo ako konfiguracija dopusta | Da |
| `needs_physician_review` | Potrebna je lijecnicka prosudba | Lijecnik | Ne kao automatski clear; moze ici tek nakon odluke | Da, samo lijecnik | Da |
| `needs_nurse_action` | Potrebna je sestrinska provjera ili radnja | Medicinska sestra | Ovisi o stavci | Moguc ako konfigurirano | Da |
| `needs_missing_document` | Nedostaje dokument ili izvor | Admin moze prikupiti, lijecnik odlucuje je li prihvatljivo bez njega | Ovisi o klinickom znacaju | Da, obicno lijecnik | Da |
| `needs_consent` | Nedostaje suglasnost ili potvrda prisutnosti suglasnosti | Admin/sestra moze provjeriti prisutnost; lijecnik pojasnjava klinicki dio | Ne za postupke koji zahtijevaju consent | Ne, osim ako zakonito i lokalno definirano | Da |
| `needs_rescheduling` | Termin treba odgoditi ili promijeniti | Admin/sestra/lijecnik ovisno o razlogu | Ne za trenutni termin | Obicno ne | Da |
| `blocked` | Postoji blok koji se ne smije ignorirati bez formalnog procesa | Najcesce lijecnik ili maintainer konfiguracije | Ne | Samo ako je eksplicitno dopusteno i auditirano | Da |

Status nije medicinska odluka sam po sebi. Status je strukturirani prikaz zahtjeva, upozorenja ili blokade.

## 5. Readiness item model

Buduci readiness item konceptualno treba imati:

- item key
- label
- category
- status
- severity
- source
- source document link ako postoji
- responsible role
- suggested action
- blocking flag
- override allowed
- override role
- override reason
- audit requirement

Ovaj model se ne implementira u B0. Ovo je vocabulary i design input za buducu domensku mapu.

## 6. Readiness categories

Canonical categories:

- identity
- appointment/service/resource
- preparation
- medication risk
- allergy risk
- sedation/anesthesia
- consent
- missing source/document
- reviewed clinical knowledge
- open questions
- procedure-specific risk
- aesthetic-treatment-specific risk
- administrative prerequisite
- inventory/material prerequisite

Kategorije moraju ostati razumljive korisnicima. Ako kategorija ne pomaze korisniku da zna sto treba uciniti, ne treba ulaziti u prvi model.

## 7. Relationship to existing systems

### Patient Workspace

Patient Workspace ostaje mjesto gdje korisnik vidi sto se zna o pacijentu i odakle to dolazi.

Clinical Readiness Gate moze citati pregledano source-linked znanje iz Patient Workspace konteksta. Ne smije zamijeniti Patient Workspace.

### Appointment Workspace

Prva buduca implementacija treba vjerojatno biti read-only readiness preview u Appointment Workspaceu.

Appointment Workspace je prirodno mjesto za pitanje: moze li ovaj planirani termin ili postupak ici dalje?

### Reception Workspace

Reception moze prikazati operativne readiness signale: identitet, dolazak, dokumenti zaprimljeni, escort ako je konfiguriran kao admin check.

Reception ne smije donositi klinicku odluku.

### ClinicalDocument

ClinicalDocument je source object.

Clinical Readiness smije koristiti samo reviewed source dokumente kao sluzbenu klinicku podlogu.

### Patient Clinical Knowledge

Patient Clinical Knowledge je temelj za klinicki kontekst.

Clinical Readiness smije citati pregledano source-linked znanje i Open Questions, ali ne smije stvarati nove klinicke cinjenice.

### Open Questions

Open Questions su source-linked upozorenja ili nerazrijesene stavke.

Clinical Readiness moze prikazati da open question zahtijeva review. Ne smije automatski pretvoriti Open Question u Task.

### Clinical Evidence Timeline

Clinical Evidence Timeline je read-only audit view.

Clinical Readiness moze kasnije prikazati audit linkove, ali timeline ne smije postati Outcome Evidence object.

### Operational Readiness

Operational Readiness odgovara na pitanje sto blokira demo ili pilot.

Clinical Readiness odgovara na pitanje moze li pacijent pristupiti planiranom klinickom cinu.

Ta dva modela moraju ostati odvojena u jeziku, API imenima i UI oznakama.

### Episode-Based Care

Clinical Readiness ne smije zahtijevati Clinical Episode.

Episode-Based Care ostaje deferred. Kasnije moze koristiti readiness signale, ali ne smije biti preduvjet za B0.

### Future Task engine

Clinical Readiness ne stvara taskove u B0.

Buduci Task engine moze nastati tek nakon definiranih readiness statusa, override semantike i odgovornosti uloga.

## 8. Governance

Pravila upravljanja:

- AI smije predloziti readiness concerns
- AI ne smije clearati readiness
- AI ne smije overrideati readiness
- lijecnik potvrduje klinicku spremnost gdje je potrebna klinicka prosudba
- medicinska sestra moze potvrditi sestrinske i pripremne stavke samo gdje je to eksplicitno dopusteno
- administracija moze potvrditi administrativne i identifikacijske stavke samo gdje je to eksplicitno dopusteno
- svi overridei zahtijevaju razlog i audit
- unreviewed AI suggestions ne smiju biti sluzbeni source
- Clinical Readiness ne smije prikrivati nesigurnost

