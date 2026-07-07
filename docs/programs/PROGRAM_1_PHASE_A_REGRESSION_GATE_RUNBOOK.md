# Program 1 - Phase A Regression Gate Runbook

## 1. Svrha

Ovaj runbook opisuje kako pokrenuti Phase A Patient Knowledge Regression Gate.

Runbook ne uvodi novu funkcionalnost, produkcijsko odobrenje, real-data odobrenje, compliance odobrenje ili certifikacijsku tvrdnju.

## 2. Whitespace check

Iz root direktorija repozitorija:

```powershell
git diff --check
```

## 3. Backend full gate

Iz `backend` direktorija:

```powershell
pytest
```

Na ovom Windows okruzenju, ako se koristi bundled Python runtime:

```powershell
$env:PYTHONPATH = (Join-Path $env:TEMP 'astra-clinic-core-pydeps')
& "C:\Users\Davor\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest
```

## 4. Backend targeted gate

Iz `backend` direktorija:

```powershell
pytest tests/test_patient_knowledge_regression_gate.py
pytest tests/test_clinical_documents.py
pytest tests/test_clinical_evidence_timeline.py
```

Bundled Python varijanta:

```powershell
$env:PYTHONPATH = (Join-Path $env:TEMP 'astra-clinic-core-pydeps')
& "C:\Users\Davor\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest tests/test_patient_knowledge_regression_gate.py
& "C:\Users\Davor\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest tests/test_clinical_documents.py
& "C:\Users\Davor\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest tests/test_clinical_evidence_timeline.py
```

## 5. Frontend gate

Iz `frontend` direktorija:

```powershell
npm run typecheck
npm run build
npm run smoke
```

## 6. Make gate

Ako je `make` dostupan:

```powershell
make test
```

Na Windows okruzenju `make` moze biti nedostupan. U tom slucaju potrebno je rucno pokrenuti ekvivalentne provjere:

- `git diff --check`
- backend `pytest`
- frontend `npm run typecheck`
- frontend `npm run build`
- frontend `npm run smoke`

## 7. No-Go

Gate ne prolazi ako bilo koja od provjera padne ili ako testovi pokazu:

- unreviewed AI output kao official knowledge
- summary view kao source of truth
- open questions bez reviewed sourcea
- evidence timeline koji stvara odluke, taskove ili outcomes
- readiness kao Clinical Readiness Gate
- Episode-Based Care kao primarni workflow
- real AI/OCR provider
- real patient data
- produkcijske ili certifikacijske tvrdnje
