# Program 1 Phase A - Regression Notes

Status: final regression note for critical hardening pass

Datum provjere: 2026-07-07

## 1. Svrha

Ovaj dokument biljezi regresijski prolaz nakon Program 1 Phase A hardening pass-a.

Ovo nije production approval, real-data approval, compliance approval niti tvrdnja da je ASTRA certificirani EMR ili medicinski uredjaj.

## 2. Provedene Provjere

### Backend

Command:

```powershell
$env:PYTHONPATH = (Join-Path $env:TEMP 'astra-clinic-core-pydeps')
& "C:\Users\Davor\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest
```

Result:

- 123 passed
- 9 skipped
- 118 warnings
- runtime: 103.63s

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

## 3. Sto Je Namjerno Izvan Opsega

Nije implementirano:

- real AI provider
- real OCR provider
- Episode-Based Care
- Clinical Readiness Gate
- Task engine
- Outcome Evidence object
- Medical Note formal output
- Patient Explanation formal output
- Consent lifecycle
- Procedure/Treatment templates
- Workflow Engine
- production deployment
- real-data readiness
- certified EMR or medical-device behavior

## 4. Preostali Rizici

- `core.py` je smanjen, ali i dalje sadrzi vise domena i treba ga dalje disciplinirano razdvajati.
- Audit event stringovi su dokumentirani, ali nisu svi postojece kodne vrijednosti normalizirane radi ocuvanja kompatibilnosti.
- Patient Clinical Summary je jasnije oznacen kao view, ali buduci Finding/Open Question model jos nije formaliziran.
- Build upozorenja za Tailwind content i react-router ostaju tehnicki dug.
- Integracijski PostgreSQL testovi su preskoceni lokalno jer ovise o `TEST_DATABASE_URL`.

## 5. Go/No-Go

Go za nastavak Phase A stabilizacije uz zadrzavanje demo/pilot guardraila.

No-Go za:

- stvarne pacijentove podatke
- produkciju
- Clinical Readiness Gate
- Workflow Engine
- real AI/OCR provider

## 6. Preporuceni Sljedeci Zadatak

`Program 1 Phase A5 - Open Questions and Unresolved Findings UI/Contract`

Svrha sljedeceg zadatka treba biti razjasniti nerijesene stavke i otvorena pitanja kao source-linked, reviewane tvrdnje, bez uvodjenja Task enginea ili Clinical Readiness Gatea.
