# Program 1 Phase B5 - Regression Notes

Status: implementation/design regression notes

## Implemented

Phase B5 uvodi dizajn i minimalnu runtime transparentnost za buduce vezanje Clinical Readiness templatea na katalog usluga.

Implementirano:

- template binding design document
- template governance document
- preview response exposes template selection metadata
- UI displays binding transparency
- regression coverage for template metadata

Nova preview response metadata polja:

- `template_key`
- `template_label`
- `template_binding_status`
- `template_binding_warning`

Runtime statusi u B5:

- `keyword_fallback`
- `generic_fallback`

Dokumentirani buduci statusi:

- `explicit`
- `module_default`
- `unbound`

## Not implemented

B5 nije implementirao:

- DB binding field
- template editor
- explicit service binding persistence
- module default binding
- production template governance
- enforcement
- override
- Task engine
- Workflow Engine
- Episode-Based Care
- real AI/OCR
- real patient data
- database migrations

## Behavioral changes

`GET /api/appointments/{appointment_id}/clinical-readiness-preview` i dalje koristi istu putanju i ostaje read-only.

Response sada jasnije prikazuje kako je template odabran:

- keyword-matched service dobiva `template_binding_status="keyword_fallback"`
- generic fallback dobiva `template_binding_status="generic_fallback"`
- oba slucaja dobivaju warning koji naglasava demo/pilot prirodu bindinga

Appointment Workspace prikazuje:

- template label
- binding status
- binding warning

UI ne dodaje kontrole za binding ili editing.

## Safety properties

B5 cuva:

- read-only endpoint
- appointment-scoped preview
- non-blocking preview
- odvojenost od `/api/readiness`
- bez appointment status promjene
- bez task creationa
- bez episode creationa
- bez ClinicalPlan creationa
- bez Outcome Evidence creationa
- bez template editor UI-ja
- bez DB binding fielda
- bez migracija
- bez real AI/OCR
- bez real patient data

Template metadata je transparency layer, ne workflow state.

## Tests/checks

B5 targeted checks:

- `docker compose build backend` - proslo
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_preview.py` - proslo, 15 passed
- `npm run smoke` - proslo

Zavrsni full regression pass biljezi se u finalnom odgovoru ovog taska.

## Remaining risks

- binding remains keyword/generic fallback only
- no DB service-template binding
- no template versioning
- no governance workflow
- no formal production approval
- template labels remain demo/pilot prompts
- UI prikazuje binding status tekstualno, bez posebnog governance componenta

## Go / No-Go

Go za nastavak demo/pilot read-only Clinical Readiness preview razvoja.

No-Go za produkcijski binding, enforcement, override, template editor, real AI/OCR i stvarne podatke.

## Recommended next task

`Program 1 Phase B6 - Clinical Readiness Explicit Service Binding Prototype`

Uvjet:

Prvi prototype treba ostati demo/pilot-only i koristiti sigurni non-migrating configuration pristup.

Ako se razmatra DB field, to mora biti zaseban carefully-scoped migration task.
