# Pilot Issue Board Protocol

## Label Policy

Use labels from `docs/ISSUE_LABELS.md`.

Required labels for pilot findings:

- one severity label: `pilot:P0`, `pilot:P1`, `pilot:P2` or `pilot:P3`
- at least one area label: for example `area:frontend`, `area:backend`, `area:inventory`, `area:billing`, `area:appointments`, `area:audit`, `area:security` or `area:docs`
- add `real-data-blocker` for anything blocking real patient data readiness

## Severity Policy

- P0: data corruption, security issue or demo cannot proceed.
- P1: core workflow blocked.
- P2: confusing but workaround exists.
- P3: cosmetic or minor wording issue.

## When to Create an Issue

Create an issue when:

- a participant cannot complete a task
- a label, warning or status causes confusion
- stock, invoice, payment or audit result is unexpected
- a real-data or fiscalization warning is unclear
- a facilitator workaround is needed

## Who Can Close P0/P1

P0/P1 issues require maintainer review before closure. Closure must include:

- reproduction notes
- fix summary or reason not reproducible
- verification evidence
- affected release/tag decision

## Definition of Done for P0/P1

- Root cause understood or explicitly documented as non-reproducible.
- Fix merged or operational mitigation accepted.
- Backend/frontend checks relevant to the issue pass.
- Release notes/checklist updated if the issue affects `v0.1-pilot`.

## Deferring P2/P3

P2/P3 may remain open for `v0.1-pilot` only if:

- they are documented in release notes or triage
- they do not block the core demo flow
- no real-data or fiscalization confusion remains unresolved

## Updating Release Notes From Issues

Before tagging:

1. Review open pilot issues.
2. Copy unresolved P2/P3 limitations into release notes.
3. Confirm no open P0/P1 remains.
4. Link final triage file from release notes if needed.
