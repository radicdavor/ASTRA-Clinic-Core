# Program 1 Phase B6 - Regression Notes

Status: demo/pilot explicit binding prototype

## Implemented

Phase B6 uvodi prvi non-migrating explicit service binding prototype za Clinical Readiness Preview.

Implementirano:

- explicit service binding prototype document
- static demo explicit service binding config
- explicit binding selection prije keyword fallbacka
- preview metadata prikazuje `template_binding_status="explicit"` kada demo binding postoji
- regression coverage za explicit binding, precedence i safety granice

Runtime precedence:

1. demo explicit service binding
2. keyword fallback
3. generic fallback

## Behavioral changes

`GET /api/appointments/{appointment_id}/clinical-readiness-preview` ostaje ista read-only putanja.

Ako `Service.code` ili tocno normalizirano ime usluge postoji u demo binding konfiguraciji, preview koristi taj template prije keyword fallbacka.

Primjer:

- service code `COLONOSCOPY`
- service name `Gastroskopija posebni demo naziv`
- rezultat: `template_key="colonoscopy"` i `template_binding_status="explicit"`

Ovo dokazuje da explicit binding ima prednost pred keywordom.

## Not implemented

B6 nije implementirao:

- DB binding field
- Alembic migraciju
- template editor
- persistent explicit service binding
- module default binding
- template versioning storage
- production governance workflow
- enforcement
- override
- Task engine
- Workflow Engine
- Episode-Based Care
- real AI/OCR
- real patient data

## Safety properties

B6 cuva:

- endpoint je read-only
- preview je appointment-scoped
- preview je non-blocking
- preview je odvojen od `/api/readiness`
- explicit binding je demo/pilot konfiguracija, nije produkcijsko pravilo
- nema appointment status promjene
- nema task creationa
- nema episode creationa
- nema ClinicalPlan creationa
- nema Outcome Evidence creationa
- nema audit writea za obican read

## Tests/checks

B6 targeted checks:

- `docker compose build backend` - proslo
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_preview.py` - proslo, 18 passed
- `npm run smoke` - proslo

Zavrsni full regression pass biljezi se u finalnom odgovoru ovog taska.

## Remaining risks

- explicit binding je staticni code config
- nema admin UI-ja
- nema DB service-template bindinga
- nema template versioning persistencea
- nema formalnog production approval workflowa
- demo binding po tocno normaliziranom nazivu i dalje nije produkcijski stabilan kao DB-backed binding

## Go / No-Go

Go za nastavak demo/pilot transparentnog preview razvoja.

No-Go za enforcement, override, production binding, template editor, real AI/OCR i stvarne podatke.

## Recommended next task

`Program 1 Phase B7 - Clinical Readiness Template Versioning Design`

Razlog:

Prije DB bindinga ili editora treba definirati kako se template content i binding verzioniraju, kako se povijesni previewi ne mijenjaju tiho i kako se promjene auditiraju.
