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

## Local Synthetic Feedback Input

Phase G adds a local terminal-only feedback preview. It echoes synthetic design feedback back to the terminal and does not store, export, transmit, or convert feedback into any clinical task.

Run a local synthetic feedback preview:

```powershell
python -m sandbox.program1.cli feedback-input --text "The review note is easier to understand now."
```

Print the same local preview as JSON:

```powershell
python -m sandbox.program1.cli feedback-input --text "The review note is easier to understand now." --json
```

Optional interactive input is available only when explicitly requested:

```powershell
python -m sandbox.program1.cli feedback-input --interactive
```

Do not enter real patient data, PHI, PII, clinical instructions, patient-identifying information, appointment details, messages, or production information. Phase G does not add file persistence, exports, network/database behavior, integrations, patient messaging, appointment mutation, clinical writeback, workflow enforcement, clinical task creation, approval/override capability, production-readiness, or go-live authorization.

## Local Synthetic Session Recap

Phase H adds a local terminal-only session recap. It combines a synthetic scenario, patient, encounter, findings, non-clinical review note, optional synthetic feedback preview, design iteration note, and safety confirmations in one readable terminal view.

Run a local synthetic session recap:

```powershell
python -m sandbox.program1.cli session-recap --scenario alpha
```

Include local synthetic feedback preview:

```powershell
python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now."
```

Print the recap as JSON:

```powershell
python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now." --json
```

The recap is not persisted, exported, transmitted, stored, converted into a clinical task, sent to patients, used for workflow enforcement, or treated as clinical content. Phase H does not add web UI, server/API behavior, network/database behavior, integrations, EHR/EMR access, real patient data, PHI/PII, patient messaging, appointment mutation, clinical writeback, approval/override capability, production-readiness, or go-live authorization.

## Local Synthetic Scenario Comparison

Phase I adds a local terminal-only scenario comparison view for the alpha and beta synthetic scenarios. It helps reviewers compare sandbox design differences without comparing real patients or supporting clinical decision-making.

Run the comparison:

```powershell
python -m sandbox.program1.cli compare-scenarios
```

Print the comparison as JSON:

```powershell
python -m sandbox.program1.cli compare-scenarios --json
```

The comparison is not persisted, exported, transmitted, stored, written to a database, or integrated with external systems. Phase I does not add web UI, server/API behavior, network/database behavior, EHR/EMR access, real patient data, PHI/PII, patient messaging, appointment mutation, clinical writeback, workflow enforcement, clinical task creation, approval/override capability, production-readiness, or go-live authorization.

## Local Synthetic Demo Closure and No-UI Hold

Phase J closes the current local terminal-only synthetic sandbox demo after Phases A through I. The sandbox is complete enough to pause and is placed into No-UI Hold.

Current local terminal-only synthetic demo commands:

```powershell
python -m sandbox.program1.cli summary --scenario alpha
python -m sandbox.program1.cli summary --scenario beta
python -m sandbox.program1.cli trial --scenario alpha
python -m sandbox.program1.cli trial --scenario beta
python -m sandbox.program1.cli review-feedback
python -m sandbox.program1.cli walkthrough
python -m sandbox.program1.cli walkthrough --json
python -m sandbox.program1.cli feedback-input --text "..."
python -m sandbox.program1.cli feedback-input --text ""
python -m sandbox.program1.cli feedback-input --text "..." --json
python -m sandbox.program1.cli session-recap --scenario alpha
python -m sandbox.program1.cli session-recap --scenario beta
python -m sandbox.program1.cli session-recap --scenario alpha --feedback "..."
python -m sandbox.program1.cli session-recap --scenario alpha --feedback "..." --json
python -m sandbox.program1.cli compare-scenarios
python -m sandbox.program1.cli compare-scenarios --json
```

No-UI Hold means no web UI, browser UI, server/API, local web app, hosted preview, deployment, production mode, EHR/EMR integration, database persistence, export behavior, patient-facing surface, or staff workflow surface is authorized.

The sandbox remains synthetic-only, non-production, local terminal-only, no real patient data, no PHI/PII, and not for clinical use. Phase J does not add a new CLI command or runtime behavior.

## Maintenance Quickstart

Maintenance Track Phase A adds documentation-only quickstart and command audit notes after Phase J. It is not Phase K, not a UI track, and not a new implementation track.

Recommended local quickstart from the repository root:

```powershell
git status -sb
python -m unittest discover tests/sandbox/program1
python -m sandbox.program1.cli walkthrough
python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now."
python -m sandbox.program1.cli compare-scenarios
git status -sb
```

All sandbox commands remain local terminal-only, synthetic-only, non-production, no real patient data, no PHI/PII, and not for clinical use. JSON modes are for structured local inspection only; they are not export, persistence, transmission, integration, production behavior, or clinical content.

If Python reports `ModuleNotFoundError: No module named 'sandbox'`, run the command from the repository root:

```powershell
cd "C:\Users\Davor\Documents\ASTRA Academy\ASTRA Clinic Core"
```

Running sandbox commands should not modify files. Use `git status -sb` before and after a demo sequence to confirm the working tree remains clean.

## Maintenance Demo Review Checklist

Maintenance Track Phase B adds documentation-only evaluation guidance after Maintenance Track Phase A. It is not Phase K, not a UI track, not a new implementation track, and not production-readiness.

Recommended review sequence:

```powershell
git status -sb
python -m unittest discover tests/sandbox/program1
python -m sandbox.program1.cli walkthrough
python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now."
python -m sandbox.program1.cli compare-scenarios
git status -sb
```

Reviewer focus:

- Is the walkthrough understandable?
- Is the output too long, confusing, or missing key context?
- Are alpha and beta easy to distinguish?
- Does the session recap make the synthetic workflow clearer?
- Does the comparison help evaluate sandbox usefulness?
- Would future UI discussion be useful, without authorizing UI work now?
- Are additional synthetic scenarios worth considering, without adding scenarios now?

Evaluation notes are guidance only. The sandbox does not store, transmit, export, persist, convert, or use them as clinical content. No-UI Hold remains active.

## Additional Local Synthetic Review Scenarios

Scenario Expansion Track Phase A adds three local terminal-only synthetic scenarios. This is not Phase K, not Maintenance Track Phase C, not a UI track, and not a production-readiness step.

Available scenarios:

- `alpha` - Synthetic patient A, example review visit
- `beta` - Synthetic patient B, boundary review visit
- `gamma` - Synthetic patient C, incomplete documentation review visit
- `delta` - Synthetic patient D, conflicting information review visit
- `epsilon` - Synthetic patient E, safety-boundary stress review visit

Examples:

```powershell
python -m sandbox.program1.cli summary --scenario gamma
python -m sandbox.program1.cli trial --scenario delta
python -m sandbox.program1.cli session-recap --scenario epsilon
python -m sandbox.program1.cli compare-scenarios
```

All scenarios remain local-only, terminal-only, synthetic-only, non-production, no real patient data, no PHI/PII, and not for clinical use. The expansion does not add UI, server/API/network/database/integration behavior, persistence/export, diagnosis, treatment, triage, patient instruction, patient messaging, appointment mutation, clinical writeback, workflow enforcement, clinical task creation, approval/override capability, production-readiness, or go-live authorization.

## Scenario Comparison Ordering

Scenario Expansion Track Phase B applies a small readability polish to `compare-scenarios`. The comparison now displays scenarios in this order:

```text
Alpha, Beta, Gamma, Delta, Epsilon
```

This is ordering only. It does not add scenarios, does not add a CLI command, does not add UI, and does not create ranking, scoring, sequencing, recommendation, protocol, clinical workflow, persistence, export, or production behavior.

## Local-Only Production Boundary

Local Production Readiness Track Phase A is documentation-only. It defines a local-only production-readiness boundary and the first future candidate, `Local Clinician-Facing Synthetic Review Demo`. It does not deploy anything and does not authorize local UI, real data, PHI/PII, clinical use, integrations, persistence/export, or go-live.

The first candidate remains synthetic-only, local-machine-only, clinician-facing, and terminal-first unless a separate future UI track is explicitly authorized. It has no network/database dependency, external integration, patient messaging, appointment mutation, clinical writeback, workflow enforcement, clinical task creation, autonomous diagnosis/treatment, or go-live claim.

No-UI Hold remains active.

## Local Synthetic Evaluation Authorization Packet

Local Production Readiness Track Phase H is complete as documentation-only authorization-packet work. It defines the packet structure, candidate identity requirements, roles, machine and custody declaration, synthetic-only declaration, no-network/no-persistence/no-export declarations, safety labels, stop conditions, deviation handling, expiration, revocation, and decision record requirements.

Phase H does not authorize execution, local evaluation, runtime verification, machine approval, UI, real-data access, deployment, clinical use, or go-live. Phase I is not started. No-UI Hold and the no-real-data boundary remain active.
