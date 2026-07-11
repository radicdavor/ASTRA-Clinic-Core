# Program 1 Phase C - Evidence and Decision Packet

Status: ready; operational fields blank.

## Required Evidence

- exact commit SHA and clean-worktree confirmation
- machine and local-route identity
- participant eligibility and consent record
- moderator and observer identities
- preflight checklist
- completed task records
- closing-question responses
- issue classifications
- stop/deviation records or explicit `none`
- reviewer readback
- decision owner and date

Missing evidence produces `INCOMPLETE`, never a pass.

## Decision States

- `NOT RUN`: no external session occurred
- `INCOMPLETE`: session or evidence is incomplete
- `STOPPED`: a stop condition occurred
- `REMEDIATE`: one or more S1-S3 issues require a separate fix authorization
- `REPEAT SYNTHETIC EVALUATION`: fixes require another synthetic session
- `ACCEPT WITH DOCUMENTED MINOR ISSUES`: only S4 issues remain
- `PHASE C SYNTHETIC EVALUATION COMPLETE`: required evidence is complete and no S0-S2 issue remains

None of these states authorizes real data, clinical use, production, deployment, or go-live.

## Decision Rules

- any S0: stop; no pass decision
- any S1: remediate; no pass decision
- any S2: remediate or repeat; no pass decision
- S3: decision owner documents remediation or explicit acceptance rationale
- S4 only: may accept with documented minor issues
- no evidence: not run or incomplete
- unanimous comfort without evidence: incomplete

## Final Decision Record

- Packet ID:
- Session ID(s):
- Exact commit SHA:
- Evidence reviewer:
- Safety reviewer:
- Decision owner:
- Decision state:
- Open issues:
- Required next action:
- Explicit prohibited authorizations:
- Decision date/expiry:
- Signature/acknowledgment:

