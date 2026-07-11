# Program 1 Synthetic Sandbox Maintenance Track Phase B1 - Demo Review Checklist

Status: documentation-only demo review checklist. Synthetic-only. Non-production. Local terminal-only. Not for clinical use.

## Command Sequence

```powershell
git status -sb
python -m unittest discover tests/sandbox/program1
python -m sandbox.program1.cli walkthrough
python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now."
python -m sandbox.program1.cli compare-scenarios
git status -sb
```

## Review Checklist

- Confirm the working tree is clean before the demo.
- Confirm the sandbox test suite passes.
- Confirm the walkthrough is understandable without reading source code.
- Confirm the session recap explains the scenario, synthetic feedback preview, and safety boundary.
- Confirm scenario comparison explains alpha and beta without implying real patient comparison.
- Confirm all output says synthetic-only, non-production, no real patient data, no PHI/PII, and not for clinical use.
- Confirm no output implies diagnosis, treatment, triage, patient instruction, clinical recommendation, appointment action, workflow action, or writeback.
- Confirm the final working tree remains clean.

This checklist does not authorize UI work, production work, integration work, persistence, export, real-data handling, PHI/PII handling, or clinical workflow behavior.
