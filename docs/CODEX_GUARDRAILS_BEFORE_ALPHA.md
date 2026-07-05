# Codex Guardrails Before Alpha

Future Codex sessions must follow these guardrails until the project passes alpha readiness.

## Before Writing Code

- Inspect `docs/pilot_sessions/` for the latest human pilot report.
- Inspect `docs/V0_1_GO_NO_GO_MATRIX.md`.
- Inspect `docs/V11_BACKLOG_FROM_PILOT.md`.
- Check whether any P0/P1 issue is open or listed as unresolved.

## Scope Rules

- Do not add features if P0/P1 pilot blockers are open.
- Prefer issue-linked changes over speculative work.
- Keep changes tied to pilot evidence.
- Cite evidence files in commit messages when practical.
- Do not expand clinical modules before pilot findings are reviewed.
- Do not add new AI mutation capability before pilot safety is reviewed.

## Safety Rules

- Keep the real-data block intact.
- Keep `REAL_DATA_ALLOWED=false` as the default.
- Keep noop/stub fiscalization warning intact.
- Do not remove the demo banner without a formal readiness decision.
- Do not imply the system is a certified EMR or medical device.
- Do not imply Croatian fiscalization is real until implemented and legally reviewed.

## Release Rules

- Do not tag `v0.1-pilot` if any P0/P1 remains open.
- Do not move to alpha planning until `docs/ALPHA_READINESS_CRITERIA.md` is satisfied.
- If human pilot is waived, update ADR 0001 and release notes with the risk.
