# Program 1 Phase D74 - Extraction CI Gate

Status: CI gate documented

## Gate

D66-D76 extraction contract safety is covered by:

- `tests/test_clinical_finding_extraction_contract.py`
- `tests/test_clinical_findings_lifecycle.py`
- `tests/test_clinical_findings_persistence.py`
- `tests/test_clinical_findings_read_api.py`
- full backend pytest suite
- frontend typecheck
- frontend build
- frontend smoke

## Coverage

The extraction contract test covers:

- passive schema serialization
- forbidden field absence
- required source reference
- required human review
- no auto persistence
- no runtime extraction flag
- no finding extraction route
- no finding extraction service

Frontend smoke covers absence of findings extraction client/UI labels.

## CI Decision

No new dependency or dedicated workflow step is required because the full backend suite and frontend smoke already cover the new tests.

