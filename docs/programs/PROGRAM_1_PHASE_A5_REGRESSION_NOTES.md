# Program 1 Phase A5 - Regression Notes

Status: final regression note for Open Questions and Unresolved Findings UI/Contract

Datum provjere: 2026-07-07

## 1. Svrha

Ovaj dokument biljezi regresijski prolaz nakon Phase A5 implementacije.

Ovo nije production approval, real-data approval, compliance approval niti tvrdnja da je ASTRA certificirani EMR ili medicinski uredjaj.

## 2. Sto Je Implementirano

Phase A5 implementira kontrolirani contract i UI clarity za Open Questions:

- `PROGRAM_1_OPEN_QUESTIONS_CONTRACT.md`
- open question klasifikacijski testovi
- centralizirana unresolved language provjera u `patient_knowledge.py`
- podrška za hrvatske dijakritike u `ceka/čeka` klasifikaciji
- open question display metadata:
  - `display_kind=open_question`
  - `severity=warning`
  - `requires_attention=true`
- Patient Workspace prikaz koji odvaja Otvorena pitanja od:
  - poznatih problema
  - zadnjih preporuka
  - Patient Clinical Summary viewa
  - dokumenata koji cekaju pregled

## 3. Provedene Provjere

### Backend

Command:

```powershell
$env:PYTHONPATH = (Join-Path $env:TEMP 'astra-clinic-core-pydeps')
& "C:\Users\Davor\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest
```

Result:

- 128 passed
- 9 skipped
- 123 warnings
- runtime: 111.85s

Napomena: warning dolazi iz `jose.jwt` upotrebe `datetime.utcnow()` u dependencyju.

### Frontend Typecheck

Command:

```powershell
npm run typecheck
```

Result:

- passed

### Frontend Build

Command:

```powershell
npm run build
```

Result:

- passed

Poznata build upozorenja:

- Tailwind `content` option missing/empty
- react-router development bundle `use client` directive ignored by bundler

### Frontend Smoke

Command:

```powershell
npm run smoke
```

Result:

- Frontend pilot smoke passed

### Whitespace

Command:

```powershell
git diff --check
```

Result:

- passed

### Make

Command:

```powershell
make test
```

Result:

- not run through `make` because `make` is not available in this Windows environment
- equivalent backend/frontend checks were run manually

## 4. Namjerno Izvan Scopea

Nije implementirano:

- Task engine
- Clinical Readiness Gate
- Episode-Based Care
- Outcome Evidence object
- Medical Note formal output
- Patient Explanation formal output
- Consent lifecycle
- Procedure/Treatment templates
- real AI provider
- real OCR provider
- real patient data
- production/certification claims

## 5. Remaining Risks

- Open Questions nemaju formalni lifecycle, owner, due date ili resolution state.
- Unresolved Finding jos nije zaseban model; trenutno je source-linked view/contract.
- Klasifikacija je namjerno jednostavna i deterministicka, nije clinical reasoning engine.
- Patient Workspace sada bolje odvaja otvorena pitanja, ali ClinicalDocument Detail review UX jos moze jasnije voditi korisnika.
- Build upozorenja za Tailwind content i react-router ostaju tehnicki dug.
- PostgreSQL integracijski testovi su preskoceni lokalno jer `TEST_DATABASE_URL` nije postavljen.

## 6. Go/No-Go

Go za nastavak Phase A stabilizacije uz demo/pilot guardrails.

No-Go za:

- stvarne pacijentove podatke
- produkciju
- Clinical Readiness Gate
- Task engine
- Workflow Engine
- real AI/OCR provider

## 7. Preporuceni Sljedeci Zadatak

`Program 1 Phase A6 - ClinicalDocument Detail Review UX Hardening`

Svrha A6 treba biti jasniji review workspace za raw source, AI suggestion, physician review, reject/edit semantics i audit evidence bez dodavanja novih clinical workflow objekata.
