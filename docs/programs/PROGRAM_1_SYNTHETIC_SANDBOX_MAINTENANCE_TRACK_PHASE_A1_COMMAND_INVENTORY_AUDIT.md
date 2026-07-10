# Program 1 Synthetic Sandbox Maintenance Track Phase A1 - Command Inventory Audit

Status: documentation-only command audit. Synthetic-only. Non-production. Local terminal-only. Not for clinical use.

The audited local terminal-only commands are:

| Command | Purpose | Boundary |
| --- | --- | --- |
| `python -m sandbox.program1.cli summary --scenario alpha` | Show alpha summary | Synthetic terminal output only |
| `python -m sandbox.program1.cli summary --scenario beta` | Show beta summary | Synthetic terminal output only |
| `python -m sandbox.program1.cli trial --scenario alpha` | Show alpha trial packet | Synthetic terminal output only |
| `python -m sandbox.program1.cli trial --scenario beta` | Show beta trial packet | Synthetic terminal output only |
| `python -m sandbox.program1.cli review-feedback` | Review synthetic feedback examples | Local design feedback only |
| `python -m sandbox.program1.cli walkthrough` | Show complete walkthrough | Local terminal walkthrough only |
| `python -m sandbox.program1.cli walkthrough --json` | Show structured walkthrough payload | Structured local inspection only |
| `python -m sandbox.program1.cli feedback-input --text "The review note is easier to understand now."` | Preview synthetic feedback text | Not stored or transmitted |
| `python -m sandbox.program1.cli feedback-input --text ""` | Preview empty feedback handling | Not stored or transmitted |
| `python -m sandbox.program1.cli feedback-input --text "The review note is easier to understand now." --json` | Structured feedback preview | Structured local inspection only |
| `python -m sandbox.program1.cli session-recap --scenario alpha` | Show alpha recap | Local terminal recap only |
| `python -m sandbox.program1.cli session-recap --scenario beta` | Show beta recap | Local terminal recap only |
| `python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now."` | Show alpha recap with synthetic feedback preview | Not stored or transmitted |
| `python -m sandbox.program1.cli session-recap --scenario alpha --feedback "The review note is easier to understand now." --json` | Structured alpha recap | Structured local inspection only |
| `python -m sandbox.program1.cli compare-scenarios` | Compare alpha and beta synthetic scenarios | No real patient comparison |
| `python -m sandbox.program1.cli compare-scenarios --json` | Structured synthetic comparison | Structured local inspection only |

Audit decision: all listed commands remain local terminal-only, synthetic-only, non-production, not for clinical use, no real patient data, and no PHI/PII.

No new command is added by Maintenance Track Phase A.
