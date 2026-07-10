# Program 1 Synthetic Sandbox Implementation Track Phase G1 - Feedback Input Model

Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use.

## Input Model

Phase G supports:

- `python -m sandbox.program1.cli feedback-input --text "The review note is easier to understand now."`
- `python -m sandbox.program1.cli feedback-input --interactive`
- `python -m sandbox.program1.cli feedback-input --text "..." --json`

Interactive mode calls `input()` only when `--interactive` is explicitly provided. No default command waits for input.

## Preview Model

The preview includes:

- feedback type: local synthetic design feedback
- entered feedback text
- warning against real patient data, PHI, PII, clinical instructions and identifying information
- interpretation as local preview only
- safety confirmations showing no persistence, transmission, clinical task, patient message, appointment mutation, workflow enforcement, writeback, approval/override or go-live behavior

## JSON Model

JSON output includes safety flags for synthetic-only status, non-production status, clinical use, real patient data, PHI/PII, persistence, external sending, clinical task creation, patient messaging, appointment mutation, workflow enforcement, clinical writeback, approval/override and go-live authorization.
