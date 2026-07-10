# Program 1 Synthetic Sandbox Implementation Track Phase J2 - Local Terminal Capability Inventory

Status: documentation-only inventory. Synthetic-only. Non-production. Local terminal-only. Not for clinical use.

The current local terminal-only synthetic demo commands are:

- `python -m sandbox.program1.cli summary --scenario alpha`
- `python -m sandbox.program1.cli summary --scenario beta`
- `python -m sandbox.program1.cli trial --scenario alpha`
- `python -m sandbox.program1.cli trial --scenario beta`
- `python -m sandbox.program1.cli review-feedback`
- `python -m sandbox.program1.cli walkthrough`
- `python -m sandbox.program1.cli walkthrough --json`
- `python -m sandbox.program1.cli feedback-input --text "..."`
- `python -m sandbox.program1.cli feedback-input --text ""`
- `python -m sandbox.program1.cli feedback-input --text "..." --json`
- `python -m sandbox.program1.cli session-recap --scenario alpha`
- `python -m sandbox.program1.cli session-recap --scenario beta`
- `python -m sandbox.program1.cli session-recap --scenario alpha --feedback "..."`
- `python -m sandbox.program1.cli session-recap --scenario alpha --feedback "..." --json`
- `python -m sandbox.program1.cli compare-scenarios`
- `python -m sandbox.program1.cli compare-scenarios --json`

Inventory interpretation: these are local terminal-only synthetic demo commands. They do not authorize UI work, deployment, persistence, export, database access, network access, integration, EHR/EMR access, real patient data, PHI/PII, clinical decision execution, patient messaging, appointment mutation, workflow enforcement, clinical writeback, approval/override capability, production-readiness, or go-live.
