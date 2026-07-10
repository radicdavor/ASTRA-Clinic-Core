# Program 1 Synthetic Sandbox Maintenance Track Phase A - Quickstart, Command Audit, and README Cleanup

Status: documentation-only maintenance. Synthetic-only. Non-production. Local terminal-only. No real patient data. No PHI/PII. Not for clinical use.

## Purpose

Phase A opens the Program 1 Synthetic Sandbox Maintenance Track after Synthetic Sandbox Implementation Track Phase J. It is not Phase K, not a UI track, and not a new implementation track.

The purpose is to make the existing local synthetic sandbox easier to run and understand by auditing README instructions, sandbox README instructions, command inventory, quickstart sequence, troubleshooting notes, and roadmap wording.

## Scope

- local sandbox documentation cleanup
- quickstart and command audit
- recommended demo sequence
- troubleshooting notes
- No-UI Hold continuity reminder
- JSON mode clarification
- no-file-modification reminder

## Non-Scope

Phase A does not add a new CLI command, Python runtime code, tests, web UI, browser UI, server, API endpoint, network access, database access, integrations, file persistence, export files, EHR/EMR access, real-data ingestion, PHI/PII handling, patient messaging, appointment mutation, workflow enforcement, Task engine behavior, Outcome Evidence behavior, clinical write workflows, clinical writeback, autonomous diagnosis, autonomous treatment, triage execution, patient instruction delivery, clinician-facing executable recommendations, production-readiness claim, go-live authorization, approval/clearance/override capability, cloud deployment, or deployment automation.

## Quickstart

Run these commands from the repository root:

```powershell
git status -sb
python -m unittest discover tests/sandbox/program1
python -m sandbox.program1.cli walkthrough
python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now."
python -m sandbox.program1.cli compare-scenarios
git status -sb
```

The first and final `git status -sb` checks confirm that running local sandbox commands does not modify files.

## Command Inventory

All commands are local terminal-only, synthetic-only, non-production, not for clinical use, no real patient data, and no PHI/PII.

- `python -m sandbox.program1.cli summary --scenario alpha`
- `python -m sandbox.program1.cli summary --scenario beta`
- `python -m sandbox.program1.cli trial --scenario alpha`
- `python -m sandbox.program1.cli trial --scenario beta`
- `python -m sandbox.program1.cli review-feedback`
- `python -m sandbox.program1.cli walkthrough`
- `python -m sandbox.program1.cli walkthrough --json`
- `python -m sandbox.program1.cli feedback-input --text "The review note is easier to understand now."`
- `python -m sandbox.program1.cli feedback-input --text ""`
- `python -m sandbox.program1.cli feedback-input --text "The review note is easier to understand now." --json`
- `python -m sandbox.program1.cli session-recap --scenario alpha`
- `python -m sandbox.program1.cli session-recap --scenario beta`
- `python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now."`
- `python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now." --json`
- `python -m sandbox.program1.cli compare-scenarios`
- `python -m sandbox.program1.cli compare-scenarios --json`

JSON modes are for structured local inspection only. They are not export, persistence, integration, transmission, or production behavior.

## Troubleshooting Notes

- Run commands from the repository root so Python can find the `sandbox` package.
- If `ModuleNotFoundError: No module named 'sandbox'` appears, change into the repository root and retry.
- Use `python -m unittest discover tests/sandbox/program1` to confirm the local sandbox tests still pass.
- Use `git status -sb` after running commands to confirm no files were modified.

## No-UI Hold Reminder

The sandbox remains in No-UI Hold. No web UI, browser UI, local web app, server/API, hosted preview, deployment, production mode, persistence/export, database access, network access, integration, EHR/EMR access, patient-facing surface, or staff workflow surface is authorized.

## Closure Statement

Maintenance Track Phase A is documentation-only and preserves the post-Phase J No-UI Hold. It does not add runtime behavior, sandbox functionality, UI, persistence/export, real-data handling, PHI/PII handling, or clinical workflow behavior.
