# Program 1 - Phase A7 Regression Notes

## 1. Svrha

Ove biljeske zatvaraju Program 1 Phase A7 - Audit Timeline Clinical Evidence Pass.

Phase A7 je evidence/audit hardening postojeceg ClinicalDocument toka. Ne uvodi novi audit sustav, Outcome Evidence object, Task engine, Clinical Readiness Gate, Episode-Based Care, Workflow Engine, real AI/OCR provider, stvarne pacijentove podatke ili produkcijske/certifikacijske tvrdnje.

## 2. Implementirano

- Dodan je `PROGRAM_1_CLINICAL_EVIDENCE_TIMELINE_CONTRACT.md`.
- Dodan je backend helper za klasifikaciju audit dogadjaja u clinical evidence kategorije.
- Dodan je read-only endpoint `GET /api/clinical-documents/{document_id}/evidence-timeline`.
- Endpoint vraca postojece ClinicalDocument audit dogadjaje s labelama, kategorijom i knowledge impact oznakom.
- ClinicalDocument Detail prikazuje `Klinicki evidence timeline`.
- Timeline jasno prikazuje da AI extraction dogadjaji nemaju sluzbeni knowledge ucinak.
- Lijecnicki pregled je oznacen kao dogadjaj koji moze omoguciti sluzbeno source-linked znanje.
- Frontend smoke provjerava timeline sekciju i najvaznije oznake.

## 3. Namjerno nije implementirano

- Outcome Evidence object
- Task engine
- Clinical Readiness Gate
- Episode-Based Care
- Workflow Engine
- formalni Medical Note output
- formalni Patient Explanation output
- Consent lifecycle
- Procedure/Treatment templates
- patient-wide evidence timeline
- real AI provider
- real OCR provider
- stvarni pacijentovi podaci
- produkcijske ili certifikacijske tvrdnje

## 4. Testovi

Pokrenuto tijekom implementacije:

- `python -m pytest tests/test_clinical_evidence_timeline.py` - 3 passed
- `python -m pytest tests/test_clinical_documents.py` - 47 passed, 84 warnings
- `npm run typecheck` - proslo
- `npm run build` - proslo
- `npm run smoke` - proslo

Zavrsni puni testovi nalaze se u zavrsnom odgovoru za ovaj task.

## 5. Poznata upozorenja

- Backend testovi prijavljuju postojece `DeprecationWarning` upozorenje iz `jose.jwt`.
- Frontend build prijavljuje postojece Tailwind `content` upozorenje i React Router `"use client"` bundle warning.

## 6. Preostali rizici

- Timeline je trenutno document-scoped, ne patient-wide.
- Klasifikacija je compatibility layer nad postojecim audit event nazivima; ne migrira staru povijest.
- Patient summary dogadjaji su klasificirani u helperu, ali nisu jos izlozeni kroz poseban patient summary evidence endpoint.
- Audit timeline je citljiviji, ali nije formalni Outcome Evidence object.

## 7. Go/No-Go

Go za nastavak Phase A hardeninga.

No-Go za uvodjenje Clinical Readiness Gatea, Task enginea, Workflow Enginea, Episode-Based Care ili Outcome Evidence objecta prije dodatnog regresijskog gatea.

## 8. Preporuceni sljedeci zadatak

Program 1 Phase A8 - Patient Knowledge Regression Gate
