# Program 1 Phase B1 - Clinical Readiness Status Taxonomy

Status: documentation-only taxonomy

## 1. Svrha

Ovaj dokument definira kanonske Clinical Readiness statuse, severities, kategorije i konceptualnu strukturu itema.

Ne implementira model, API, UI ili migraciju.

## 2. Gate statuses

| Status | Meaning | Can proceed? | Who can resolve? | Override allowed? | Audit required? | Example |
| --- | --- | --- | --- | --- | --- | --- |
| `ready` | Nema nerijesenih itema prema konfiguriranom kontekstu. | Da | Nije potrebno, ili odgovorna osoba potvrduje workflow. | Nije potrebno | Optional/yes if confirmed | Svi dokumenti pregledani, consent prisutan, nema warninga. |
| `ready_with_warning` | Postoje upozorenja, ali nisu automatski blok. | Da, nakon pregleda warninga | Lijecnik ili dopustena uloga prema itemu | Da | Da | Antikoagulans zabiljezen, lijecnik prihvaca nastavak. |
| `not_ready` | Postoji nerijesen preduvjet ili prepreka. | Ne dok se ne rijesi | Ovisno o itemu | Samo ako dozvoljeno | Da | Pacijent nije pripremljen za kolonoskopiju. |
| `needs_physician_review` | Potrebna je lijecnicka prosudba. | Ne kao automatic clear | Lijecnik | Da, samo lijecnik ako dozvoljeno | Da | Otvoreno pitanje o PHD nalazu prije postupka. |
| `needs_nurse_action` | Potrebna je sestrinska provjera ili radnja. | Ovisi o itemu | Medicinska sestra | Moguce ako konfigurirano | Da | Fasting declaration nije evidentirana. |
| `needs_missing_document` | Nedostaje potreban source/document. | Ovisi o klinickoj vaznosti | Admin prikuplja, lijecnik odlucuje | Da, obicno lijecnik | Da | Nedostaje vanjski PHD nalaz. |
| `needs_consent` | Nedostaje pristanak ili dokaz pristanka. | Ne za postupak koji ga zahtijeva | Admin/sestra provjerava, lijecnik pojasnjava | U pravilu ne | Da | Nema pristanka za sedaciju/polipektomiju. |
| `needs_rescheduling` | Trenutni termin treba odgoditi/promijeniti. | Ne za trenutni cin | Admin/sestra/lijecnik prema razlogu | Obicno ne | Da | Nema pratnje nakon sedacije. |
| `blocked` | Postoji blok koji se ne smije ignorirati bez formalnog procesa. | Ne | Najcesce lijecnik ili governance-defined role | Samo eksplicitno | Da | Aktivna infekcija prije estetskog tretmana. |

## 3. Item severities

| Severity | Meaning | UI tone | Action required? | Example |
| --- | --- | --- | --- | --- |
| `info` | Informativna stavka bez rizika. | Neutralno | Ne, osim ako workflow trazi potvrdu | Pacijent ima pregledan vanjski nalaz. |
| `warning` | Potrebna paznja ili review, ali nije automatski blok. | Zuto/upozorenje | Da, pregled ili potvrda | Antikoagulans naveden u dokumentu. |
| `blocking` | Stavka sprjecava nastavak dok nije rijesena ili overrideana. | Crveno/blok | Da | Nedostaje obvezni consent. |
| `critical` | Visokorizicna stavka koja zahtijeva formalni ljudski review i najstrozi audit. | Kriticno | Da, physician/governance | Moguca kontraindikacija za planirani postupak. |

## 4. Item categories

Canonical categories:

- `identity`
- `appointment`
- `service`
- `room/resource`
- `preparation`
- `medication`
- `allergy`
- `sedation/anesthesia`
- `consent`
- `missing document`
- `reviewed evidence`
- `open question`
- `procedure-specific risk`
- `aesthetic-treatment-specific risk`
- `inventory/material`
- `administrative`

Kategorija opisuje zasto item postoji. Ne smije se koristiti kao zamjena za responsible role ili severity.

## 5. Conceptual item shape

Buduci `Clinical Readiness Item` konceptualno ima:

- `key`
- `label`
- `category`
- `status`
- `severity`
- `source_type`
- `source_ref`
- `responsible_role`
- `suggested_action`
- `blocking`
- `override_allowed`
- `override_role`
- `override_reason_required`
- `audit_required`

Ovo nije schema i ne smije se implementirati bez B2 API/UI contracta.

## 6. Aggregation rules

Konceptualna agregacija:

- any critical/blocking item without override -> `blocked`
- missing required consent -> `needs_consent`
- missing required document -> `needs_missing_document`
- physician-only unresolved issue -> `needs_physician_review`
- nurse checklist issue -> `needs_nurse_action`
- warnings only -> `ready_with_warning`
- no unresolved items -> `ready`

Ova pravila su konceptualna. Prije implementacije treba definirati:

- redoslijed prioriteta ako postoji vise statusa
- tko smije potvrditi svaki status
- kako se prikazuje override
- kako se auditira promjena
- kako se source badge vezuje uz item

