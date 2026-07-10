# Program 1 Synthetic Sandbox Implementation Track Phase I - Local Synthetic Scenario Comparison View

Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use.

## Status

Phase I adds a local terminal-only synthetic scenario comparison view.

It remains local-only, synthetic-only, terminal-only, non-production and not for clinical use.

## Purpose

Phase I displays the alpha and beta synthetic scenarios in one clinician-readable comparison view. It helps a reviewer understand differences between demo scenarios without comparing real patients or supporting clinical decision-making.

## Command

```powershell
python -m sandbox.program1.cli compare-scenarios
python -m sandbox.program1.cli compare-scenarios --json
```

## Non-Approval

Phase I does not authorize real patient data, PHI/PII, clinical recommendations, autonomous diagnosis, autonomous treatment, patient messaging, appointment mutation, clinical writeback, workflow enforcement, clinical task creation, approval/clearance/override capability, production readiness or go-live.

## Closure Statement

Phase I adds only a local terminal comparison. It does not persist, export, transmit, store, message patients, mutate appointments, enforce workflows, write clinical records or imply production/clinical readiness. Phase J or later was not started.
