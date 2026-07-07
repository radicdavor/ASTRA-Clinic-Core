# Program 1 Phase B4 - Regression Notes

Status: implementation regression notes

## Implemented

Phase B4 uvodi sigurne demo/pilot staticne template definicije za read-only Clinical Readiness Preview.

Implementirano:

- template design document
- demo/pilot static template definitions
- service-name template matching
- preview uses template-generated items
- regression coverage

Template families:

- `generic`
- `gastroscopy`
- `colonoscopy`
- `hpylori`
- `aesthetic_injectable`
- `aesthetic_skinbooster_pn`
- `aesthetic_energy_device`

## Behavior

`GET /api/appointments/{appointment_id}/clinical-readiness-preview` sada dodaje template-generated preview iteme prema nazivu usluge.

Ako se prepozna specifican template, response ukljucuje limitation:

`Koristi se demo/pilot template: <template name>.`

Ako nema specificnog matcha, koristi se generic template i response ukljucuje limitation:

`Nema specificnog clinical readiness templatea za ovu uslugu; koristi se genericki preview.`

Svi template-generated itemi ostaju:

- preview-only
- non-blocking u runtime previewu
- bez audit writea na read
- bez task creationa
- bez appointment status promjene
- bez episode/ClinicalPlan/Outcome Evidence creationa

Samo missing patient i missing service ostaju strukturni blockeri u prototipu.

## Not implemented

B4 nije implementirao:

- DB template model
- template editor
- service catalog template binding
- template versioning
- enforcement
- blocking workflow
- override
- Task engine
- Workflow Engine
- Outcome Evidence object
- real AI/OCR
- production readiness
- real patient data
- production/certification claims

## Safety properties

B4 cuva B3 granice:

- endpoint ostaje read-only
- preview ostaje appointment-scoped
- preview ostaje odvojen od `/api/readiness`
- preview ne zahtijeva Clinical Episode
- preview ne koristi unreviewed AI kao source
- preview ne koristi Patient Clinical Summary kao source of truth
- Open Questions ostaju warning/physician-review itemi, ne taskovi
- template itemi ne clearaju readiness i ne odobravaju postupak

## Tests/checks

B4 regression gate:

- `docker compose build backend` - proslo
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_preview.py` - proslo, 14 passed
- `npm run smoke` - proslo

Zavrsni full regression pass biljezi se u finalnom odgovoru ovog taska.

## Remaining risks

- keyword matching je primitivan
- nema service catalog template bindinga
- nema formalnog template versioninga
- nema governance UI-ja
- nema override modela
- nema produkcijskih pravila
- template item labels nisu klinicke smjernice

## Go / No-Go

Go za nastavak demo/pilot read-only preview razvoja.

No-Go za enforcement, override, taskove, Workflow Engine, real AI/OCR, real patient data i produkcijske tvrdnje.

## Recommended next task

`Program 1 Phase B5 - Clinical Readiness Template Binding Design`

Razlog:

Staticni templatei rade i regression coverage postoji. Prije dodavanja vise UI-ja ili bilo kakvog enforcementa ASTRA treba siguran model kako se templatei vezu na katalog usluga bez pretvaranja u produkcijska pravila.
