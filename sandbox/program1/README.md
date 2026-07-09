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

Run the local synthetic summary:

```powershell
python -m sandbox.program1.cli
```

Run the alternate synthetic scenario:

```powershell
python -m sandbox.program1.cli --scenario beta
```

Print JSON for local inspection:

```powershell
python -m sandbox.program1.cli summary --scenario beta --json
```

Run a local synthetic clinician trial packet:

```powershell
python -m sandbox.program1.cli trial --scenario alpha
```

Print the local synthetic clinician trial packet as JSON:

```powershell
python -m sandbox.program1.cli trial --scenario beta --json
```

Review safe synthetic feedback examples and a local sandbox iteration queue:

```powershell
python -m sandbox.program1.cli review-feedback
```

Print the local feedback review as JSON:

```powershell
python -m sandbox.program1.cli review-feedback --json
```

Run the complete local clinician walkthrough pack:

```powershell
python -m sandbox.program1.cli walkthrough
```

Print the walkthrough pack as JSON:

```powershell
python -m sandbox.program1.cli walkthrough --json
```

Example:

```python
from sandbox.program1 import build_sample_workflow, build_workflow_summary

patient, encounter, findings, review = build_sample_workflow()
summary = build_workflow_summary(review)
```

## Synthetic Feedback Template

Phase C adds a local feedback template for synthetic usability notes. It validates:

- `scenario_id`
- `reviewer_role`
- `workflow_clarity_score`
- `missing_information`
- `confusing_output`
- `usefulness_notes`
- `safety_concerns`
- `next_iteration_suggestions`
- `synthetic_only_confirmation`

The template is local-only and is not persisted by the sandbox command. Do not enter real patient data, PHI/PII, real identifiers, clinical notes, appointment data, messages, or production information.

## Local Feedback Review

Phase D adds safe synthetic feedback examples and an iteration queue preview. The queue is local-only and does not imply implementation approval beyond the synthetic sandbox, production readiness, clinical deployment, real-data readiness, or cloud readiness.

## Local Clinician Walkthrough

Phase E adds a combined local walkthrough. It lists available synthetic scenarios, command sequence, clinician checklist items, and explicit non-clinical/non-production boundaries. It does not run cloud services, databases, networks, integrations, patient messaging, appointment mutation, clinical writeback, approval/override behavior, or go-live behavior.

Phase F improves the default terminal output so the walkthrough is easier for a clinician to read. The default `summary`, `trial`, `review-feedback`, and `walkthrough` commands now use plain-language scenario labels, non-clinical review note wording, readable feedback framing, and design iteration queue wording. JSON output remains available for structured local inspection.

Phase F remains local-only, terminal-only, synthetic-only, non-production, and not for clinical use. It does not add web UI, server/API behavior, network/database behavior, external integrations, EHR/EMR access, real patient data, PHI/PII, patient messaging, appointment mutation, clinical writeback, approval/override capability, production-readiness, or go-live authorization.
