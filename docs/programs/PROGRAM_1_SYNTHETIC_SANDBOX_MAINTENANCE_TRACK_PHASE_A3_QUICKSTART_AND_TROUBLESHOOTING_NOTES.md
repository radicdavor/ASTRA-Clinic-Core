# Program 1 Synthetic Sandbox Maintenance Track Phase A3 - Quickstart and Troubleshooting Notes

Status: documentation-only troubleshooting notes. Synthetic-only. Non-production. Local terminal-only. Not for clinical use.

## Quickstart

From the repository root:

```powershell
python -m unittest discover tests/sandbox/program1
python -m sandbox.program1.cli walkthrough
```

## Troubleshooting

If Python cannot find the sandbox package:

```powershell
cd "C:\Users\Davor\Documents\ASTRA Academy\ASTRA Clinic Core"
python -m sandbox.program1.cli walkthrough
```

If you want to confirm that commands did not write files:

```powershell
git status -sb
```

If you want structured local inspection:

```powershell
python -m sandbox.program1.cli walkthrough --json
python -m sandbox.program1.cli compare-scenarios --json
```

JSON output is not persistence, export, transmission, integration, production behavior, or clinical content. It is structured local inspection only.

Do not enter real patient data, PHI/PII, real identifiers, clinical notes, appointment details, messages, or production information into sandbox commands.
