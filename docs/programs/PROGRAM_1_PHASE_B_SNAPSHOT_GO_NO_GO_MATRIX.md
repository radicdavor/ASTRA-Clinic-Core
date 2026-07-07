# Program 1 Phase B - Snapshot Go/No-Go Matrix

Status: formal go/no-go matrix for Clinical Readiness Snapshot subphase

## Decision Summary

High-level decision:

- demo/pilot: allowed with guardrails
- real patient data: no-go
- production: no-go
- clinical approval/enforcement: no-go

## Matrix

| Area | Status | Allowed for demo/pilot | Allowed for real patient data | Allowed for production | Blockers | Next action |
|---|---|---:|---:|---:|---|---|
| Live preview | Implemented read-only | Yes | No | No | no production governance, no clinical enforcement policy | keep read-only until enforcement design |
| Template metadata | Implemented demo/static | Yes | No | No | demo templates only, no specialty governance | define production template governance |
| Snapshot persistence | Implemented | Yes | No | No | no DB-level immutable trigger, backup/restore policy missing | production risk hardening |
| Capture service | Implemented | Yes | No | No | no production governance | harden audit and immutability rules |
| Capture endpoint | Implemented | Yes | No | No | permission UX and governance incomplete | review permissions and rate limits |
| History API | Implemented read-only | Yes | No | No | production audit review missing | keep read-only |
| Detail API | Implemented read-only | Yes | No | No | production audit review missing | keep read-only |
| Capture UI | Implemented reason-required | Yes | No | No | usability review and permission UX incomplete | usability review |
| Supersession service | Implemented internal | Yes | No | No | DB immutability policy incomplete | harden additive-only policy |
| Supersession endpoint | Implemented | Yes | No | No | permission UX and legal wording incomplete | production risk review |
| Supersession UI | Implemented reason-required | Yes | No | No | usability review needed | review with pilot users |
| Audit events | Implemented for capture/supersession | Yes | No | No | audit review workflow incomplete | define audit review runbook |
| Idempotency | Implemented for capture | Yes | No | No | idempotency scope/governance needs review | production hardening |
| Permission model | Implemented basic RBAC | Yes | No | No | API key write/supersede denied, UX basic | role UX hardening |
| Frontend safety labels | Implemented | Yes | No | No | real-world wording review needed | usability and legal review |
| Regression coverage | Implemented | Yes | No | No | CI hardening incomplete | CI enforcement |
| Real data readiness | Not approved | No | No | No | privacy, legal, security, governance incomplete | real-data readiness program |
| Production readiness | Not approved | No | No | No | CI, backup, security, compliance incomplete | production risk hardening |
| Clinical approval readiness | Not implemented | No | No | No | no approval/clearance model by design | clinical enforcement readiness design |
| Outcome Evidence readiness | Not implemented | No | No | No | no Outcome Evidence object by design | do not implement until approved |
| Task engine readiness | Not implemented | No | No | No | no Task engine by design | defer until workflow program |

## No-Go Triggers

No-Go if any of the following appear before explicit maintainer approval:

- snapshot wording implies patient is ready
- snapshot wording implies procedure is approved
- supersession wording implies old snapshot was deleted or corrected
- capture or supersession changes appointment status
- capture or supersession creates Task
- capture or supersession creates Outcome Evidence
- AI/API key can write runtime capture or supersession by default
- real patient data is entered
- production/certification claims appear

## Closure Recommendation

Proceed only to production risk hardening or enforcement readiness design.

Recommended next task:

`Program 1 Phase B29 - Snapshot Production Risk Hardening`
