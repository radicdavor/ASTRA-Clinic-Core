# Program 1 - Phase A6 Regression Notes

## 1. Svrha

Ove biljeske zatvaraju Program 1 Phase A6 - ClinicalDocument Detail Review UX Hardening.

Phase A6 je UX i regresijski hardening postojeceg ClinicalDocument toka. Nije nova klinicka funkcionalnost, nije produkcijsko odobrenje, nije real-data odobrenje i nije tvrdnja da je ASTRA certificirani EMR ili medicinski uredaj.

## 2. Implementirano

- Dodan je `PROGRAM_1_CLINICAL_DOCUMENT_DETAIL_UX_CONTRACT.md`.
- Dodani su backend testovi za ClinicalDocument detail lifecycle stanja.
- ClinicalDocument Detail jasnije odvaja:
  - izvorni dokument
  - AI prijedlog ekstrakcije
  - lijecnicki pregled
  - doprinos sluzbenom source-linked znanju pacijenta
- UI sada jasno kaze da odbijanje AI prijedloga ne odbija izvorni dokument.
- Frontend smoke provjerava nove oznake i akcije na ClinicalDocument Detail ekranu.
- Program 1 dokumentacija je uskladjena s A6 hardening statusom.

## 3. Namjerno nije implementirano

- Task engine
- Clinical Readiness Gate
- Episode-Based Care
- Workflow Engine
- Outcome Evidence object
- formalni Medical Note output
- formalni Patient Explanation output
- Consent lifecycle
- Procedure/Treatment templates
- pravi AI provider
- pravi OCR provider
- stvarni pacijentovi podaci
- produkcijske ili certifikacijske tvrdnje

## 4. Testovi

Pokrenuto:

- `git diff --check` - proslo
- `python -m pytest` u backendu - 130 passed, 9 skipped, 133 warnings
- `npm run typecheck` u frontendu - proslo
- `npm run build` u frontendu - proslo
- `npm run smoke` u frontendu - proslo

Poznata upozorenja:

- Backend testovi prijavljuju `DeprecationWarning` iz `jose.jwt` dependencyja.
- Frontend build prijavljuje postojece Vite/Tailwind upozorenje za praznu Tailwind `content` konfiguraciju i React Router `"use client"` bundle warning.

Nije pokrenuto:

- `make test`, jer `make` nije dostupan u ovom Windows okruzenju.

## 5. Preostali rizici

- `ClinicalDocumentDetail` je jasniji, ali source rejection i supersede workflow jos nisu formalizirani kao zasebne akcije.
- `Finding` jos nije zaseban domain object; `key_findings` ostaju strukturirani output na ClinicalDocumentu.
- Audit timeline prikazuje tehnicke dogadjaje, ali jos nije dodatno oblikovan kao klinicki evidence timeline.
- Pravi OCR/file storage i pravi AI provider nisu implementirani.

## 6. Go/No-Go

Go za nastavak Program 1 Phase A hardeninga.

No-Go za uvodjenje Clinical Readiness Gatea, Task enginea, Workflow Enginea ili Episode-Based Care prije dodatnog stabiliziranja document/audit sloja.

## 7. Preporuceni sljedeci zadatak

Program 1 Phase A7 - Audit Timeline Clinical Evidence Pass
