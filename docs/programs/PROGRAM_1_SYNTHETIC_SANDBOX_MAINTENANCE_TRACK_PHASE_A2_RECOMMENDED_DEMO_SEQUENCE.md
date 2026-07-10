# Program 1 Synthetic Sandbox Maintenance Track Phase A2 - Recommended Demo Sequence

Status: documentation-only demo sequence. Synthetic-only. Non-production. Local terminal-only. Not for clinical use.

Recommended quickstart sequence:

```powershell
git status -sb
python -m unittest discover tests/sandbox/program1
python -m sandbox.program1.cli walkthrough
python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now."
python -m sandbox.program1.cli compare-scenarios
git status -sb
```

Review interpretation:

- Start with `git status -sb` to confirm the working tree is clean.
- Run the sandbox tests to confirm existing local behavior.
- Use `walkthrough` for a full clinician-readable terminal overview.
- Use `session-recap` with synthetic feedback to inspect the local recap and feedback boundary.
- Use `compare-scenarios` to compare alpha and beta synthetic scenarios without real patient comparison.
- End with `git status -sb` to confirm no files were modified.

This sequence does not authorize UI, deployment, persistence, export, network/database behavior, integration, real-data handling, PHI/PII handling, clinical workflow behavior, patient messaging, appointment mutation, clinical writeback, approval/override capability, production-readiness, or go-live.
