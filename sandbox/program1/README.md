# Program 1 Synthetic Sandbox Implementation Track Phase A

Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use.

This local sandbox lets a user experience a minimal Program 1 workflow with synthetic placeholders only:

1. load a synthetic patient
2. load a synthetic encounter
3. attach synthetic findings
4. produce a synthetic clinician review placeholder
5. see explicit sandbox-only and non-clinical status

## Boundaries

- No real patient data.
- No PHI/PII.
- No network calls.
- No database connection.
- No external API connection.
- No EHR/EMR connection.
- No file import of clinical data.
- No environment secrets.
- No deployment configuration.
- No patient messaging.
- No appointment mutation.
- No autonomous diagnosis or treatment.
- No clinical writeback.
- No approval, clearance, or override capability.
- No go-live claim.

## Local Use

This module is intentionally isolated from backend and frontend runtime paths. It can be imported in local tests or interactive Python sessions only.

Example:

```python
from sandbox.program1 import build_sample_workflow, build_workflow_summary

patient, encounter, findings, review = build_sample_workflow()
summary = build_workflow_summary(review)
```
