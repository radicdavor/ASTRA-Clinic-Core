# Program 1 Phase B7 - Regression Notes

Status: demo/pilot template versioning transparency

## Implemented

Phase B7 uvodi template versioning design i minimalni demo runtime metadata sloj.

Implementirano:

- template versioning design document
- staticni demo template version metadata
- preview response exposes template version metadata
- Appointment Workspace displays template version
- regression coverage for template version metadata

Nova preview response metadata polja:

- `template_version`
- `template_version_warning`

Trenutna demo vrijednost:

- `template_version="demo-v1"`

## Behavioral changes

`GET /api/appointments/{appointment_id}/clinical-readiness-preview` ostaje ista read-only putanja.

Response sada prikazuje demo verziju templatea.

Appointment Workspace prikazuje:

- Template
- Verzija
- Binding

Template verzija je transparency metadata, ne workflow state.

## Not implemented

B7 nije implementirao:

- DB template version table
- DB binding version table
- Alembic migraciju
- template editor
- persistent versioning
- audit za promjenu templatea
- enforcement
- override
- Task engine
- Workflow Engine
- real AI/OCR
- real patient data

## Safety properties

B7 cuva:

- endpoint je read-only
- preview je appointment-scoped
- preview je non-blocking
- verzija je demo/pilot oznaka iz staticne konfiguracije
- verzija nije produkcijsko verzioniranje
- nema appointment status promjene
- nema task creationa
- nema episode creationa
- nema ClinicalPlan creationa
- nema Outcome Evidence creationa
- nema audit writea za obican read

## Tests/checks

B7 targeted checks:

- `docker compose build backend` - proslo
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_preview.py` - proslo, 19 passed
- `npm run smoke` - proslo

Zavrsni full regression pass biljezi se u finalnom odgovoru ovog taska.

## Remaining risks

- template version je staticni code metadata
- nema persistent version history
- nema audit eventa za template promjene
- nema formalnog production approval workflowa
- nema veza povijesnog previewa s immutable template snapshotom

## Go / No-Go

Go za nastavak demo/pilot transparentnog preview razvoja.

No-Go za produkcijski versioning, editor, enforcement, override, real AI/OCR i stvarne podatke.

## Recommended next task

`Program 1 Phase B8 - Clinical Readiness Snapshot Design`

Razlog:

Nakon template key, binding i version transparencyja treba definirati kako bi buduci read-only snapshot mogao zabiljeziti sto je preview prikazao u odredenom trenutku, bez stvaranja Outcome Evidence objekta ili enforcementa.
