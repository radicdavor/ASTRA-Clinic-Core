# Program 1 Phase B4 - Clinical Readiness Template Design

Status: demo/pilot-only template design

## 1. Svrha

Ovaj dokument definira demo/pilot-only template model za read-only Clinical Readiness Preview.

Templatei generiraju preview stavke koje korisniku pomazu vidjeti sto bi moglo biti potrebno pregledati prije planirane usluge, postupka ili tretmana.

Ovaj dokument nije:

- produkcijsko odobrenje
- real-data odobrenje
- compliance odobrenje
- certified EMR claim
- medical-device claim
- klinicka smjernica
- workflow engine
- task engine

Templatei:

- generiraju preview iteme
- ne donose odluke
- ne blokiraju workflow
- ne clearaju readiness
- ne stvaraju taskove
- ne zamjenjuju lijecnicku prosudbu
- nisu produkcijska pravila

ASTRA smije organizirati, upozoriti i prikazati ogranicenja.

Lijecnik odlucuje.

## 2. Template concept

Clinical Readiness Template je staticna, service/procedure-oriented lista mogucih readiness itema.

Template smije reci:

- ova usluga obicno treba provjeru nataste
- ova usluga obicno treba provjeru pristanka
- ova usluga obicno treba pregled lijekova koji nose rizik
- ova usluga obicno treba provjeru pratnje nakon sedacije

Template ne smije reci:

- pacijent je odobren
- postupak je dopusten
- AI je clear-ao pacijenta
- klinicki rizik je odsutan
- nastavi automatski

Template item je podsjetnik i signal za review, ne odluka.

## 3. Template matching

Prvo sigurno matching pravilo je deterministicno i jednostavno:

- prema keywordima u nazivu usluge
- opcionalno prema service category/module kada takav podatak postane stabilan
- fallback na generic template

Primjeri keyworda:

- naziv usluge sadrzi `gastroskop`
- naziv usluge sadrzi `kolonoskop`
- naziv usluge sadrzi `H. pylori` ili `Helicobacter`
- naziv usluge sadrzi `filler`, `botox`, `skinbooster`, `polinukleotid` ili `PN`
- naziv usluge sadrzi `laser`, `RF`, `Exion` ili `energy`

B4 ne uvodi database template editor.

B4 ne uvodi service catalog template binding model.

## 4. Template item structure

Konceptualna struktura template itema:

- `key`
- `label`
- `category`
- `default_status`
- `severity`
- `responsible_role`
- `source_type`
- `suggested_action`
- `blocking`
- `override_allowed`
- `override_role`
- `override_reason_required`
- `audit_required`

Ova struktura mapira B1/B2 vocabulary i API contract, ali u B4 ostaje staticna demo/pilot definicija u kodu.

## 5. Initial template families

Pocetne template family definicije:

- `generic`
- `gastroscopy`
- `colonoscopy`
- `hpylori`
- `aesthetic_injectable`
- `aesthetic_skinbooster_pn`
- `aesthetic_energy_device`

### Generic

Generic template se koristi kada nema specificnog matcha.

Primjeri itema:

- potvrditi planiranu uslugu
- provjeriti treba li pristanak

### Gastroscopy

Primjeri itema:

- provjera nataste
- pregled antikoagulansa/antiagregansa
- pregled alergija
- pratnja nakon sedacije ako je sedacija planirana
- provjera pristanka
- pregled prethodnih relevantnih nalaza

### Colonoscopy

Primjeri itema:

- deklaracija pripreme crijeva
- pregled antikoagulansa/antiagregansa
- pregled terapije za dijabetes ako je relevantno
- pratnja nakon sedacije
- pristanak za kolonoskopiju/sedaciju/polipektomiju
- pregled prethodne kolonoskopije/PHD nalaza
- obiteljska anamneza/high-risk pregled
- material readiness za polipektomijski pribor

### H. pylori

Primjeri itema:

- poznata prethodna eradikacijska terapija
- pregled alergije na penicilin
- timing PPI/antibiotik/bizmut terapije
- timing test-of-cure
- pregled prethodnog neuspjeha ili rezistencije

### Aesthetic injectable

Primjeri itema:

- trudnoca/dojenje deklaracija
- aktivna infekcija/herpes
- pregled antikoagulansa
- pregled alergija
- prethodni filler/material history
- prethodne komplikacije
- pristanak
- baseline foto dokumentacija
- dostupnost proizvoda/serije

### Aesthetic skinbooster / PN

Primjeri itema:

- aktivna infekcija
- inflammatory/autoimmune concern gdje je relevantno
- prethodna reakcija
- interval tretmana
- pristanak
- foto dokumentacija
- dostupnost proizvoda/serije

### Aesthetic energy device

Primjeri itema:

- kontraindicirani uredaj/implantat/pacemaker gdje je relevantno
- stanje koze u tretiranom podrucju
- nedavni postupci
- pristanak
- dokumentacija tretiranog podrucja

## 6. Governance

Pravila za B4:

- svi template-generated itemi su preview-only
- blocking itemi u previewu ne smiju blokirati workflow
- template-generated blockers su samo potencijalni buduci blockeri
- samo missing patient i missing service smiju biti strukturni blockeri u prototipu
- lijecnik odlucuje o klinickom znacenju
- medicinska sestra i administracija smiju provjeravati samo role-appropriate iteme
- nema audit write na preview read
- nema DB template modela
- nema template editora
- nema real AI/OCR providera
- nema produkcijskih pravila

Ako template item zvuci kao klinicki blok, u B4 se prikazuje kao upozorenje za pregled, ne kao enforcement.
