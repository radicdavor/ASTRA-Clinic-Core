# Program 1 Local Production Readiness Track Phase G - Local Evaluation Preflight and Evidence Plan

Status: documentation-only. Synthetic-only. Local-only. No execution authorization. No deployment. No production use. No clinical use. No go-live authorization.

## 1. Purpose

Phase G defines a preflight and evidence plan for a possible future controlled local evaluation of the `Local Clinician-Facing Synthetic Review Demo`.

Phase G does not execute the candidate, package it, install it, configure a machine, validate runtime behavior, open a UI track, open a real-data track, or authorize deployment.

## 2. Explicit Authorization Boundary

Allowed:

- documentation of preflight checks
- documentation of required evidence
- documentation of pass, fail, and not-tested states
- documentation of evaluator and custodian responsibilities
- documentation of stop conditions
- documentation of synthetic-only evaluation scenarios
- continuation of the No-UI Hold
- continuation of the no-real-data, no-persistence, no-export, and no-go-live boundaries

Prohibited:

- Python runtime code
- new CLI commands
- local execution
- software installation or packaging
- operating-system configuration
- UI, server, API, network, database, or integration implementation
- persistence, export, synchronization, telemetry, or backup implementation
- real-data ingestion, viewing, processing, storage, transmission, or logging
- PHI or PII handling
- clinical workflow behavior
- patient messaging
- appointment mutation
- clinical writeback
- clinical task creation
- autonomous diagnosis, treatment, triage, recommendation, or instruction
- approval, override, clearance, or workflow-enforcement capability
- production deployment
- go-live authorization

## 3. Preflight Objective

The future preflight must determine whether a separately authorized local synthetic evaluation could be performed within the already defined boundaries.

The preflight is not a production-readiness test. It is a boundary-conformance review for a synthetic, clinician-facing, local-only candidate.

## 4. Required Roles

A future authorized preflight must identify:

- one accountable Program 1 owner
- one local machine custodian
- one evaluator
- one independent reviewer of evidence
- one person authorized to stop the evaluation

One person may hold more than one role only if the decision record explicitly states the conflict-of-interest implications.

## 5. Required Candidate Identity

Before any future execution, the evidence record must identify:

- repository: `radicdavor/ASTRA-Clinic-Core`
- exact commit SHA
- exact approved files and launch path already present in the repository
- candidate name
- candidate purpose
- synthetic scenario set
- expected outputs
- prohibited inputs
- expected processes
- expected files read
- expected files written, which must remain none unless separately authorized
- expected ports, which must remain none
- expected network calls, which must remain none

Version labels such as `latest`, `current`, or `main` are insufficient evidence for execution. A fixed commit SHA is required.

## 6. Machine Preflight Evidence

A future preflight must record, without adding implementation in this phase:

| Control | Required evidence | Acceptable state |
| --- | --- | --- |
| Machine identity | Device name and accountable custodian | Identified |
| Operating system | Supported version record | Supported |
| Security updates | Patch status record | Current |
| Disk protection | Full-disk encryption status | Enabled |
| Authentication | Named authenticated account | Enabled |
| Privilege model | Daily account privilege record | Least privilege |
| Screen lock | Automatic lock policy record | Enabled |
| Physical access | Location and access description | Controlled |
| Shared access | Generic/shared account review | None |
| Local copy custody | Commit, path, owner, and removal record | Complete |
| Decommission path | Removal and verification steps | Defined |

No machine is approved by this document.

## 7. No-Network Preflight Evidence

A future separately authorized review must define how it will establish that the candidate:

- has no internet dependency
- has no local-area-network dependency
- starts without connectivity
- creates no listening server or port
- attempts no outbound connection
- performs no update check
- emits no telemetry or analytics
- invokes no external API
- accesses no database
- accesses no EHR or EMR
- accesses no appointment system
- accesses no patient messaging system
- starts no persistent background service

Evidence methods may be proposed later, but Phase G does not authorize their execution or the addition of instrumentation.

## 8. Synthetic-Only Input Preflight

The future evaluation plan must use only repository-controlled synthetic scenarios.

The evaluator instructions must explicitly prohibit:

- patient names
- dates of birth
- addresses
- telephone numbers
- email addresses
- national or institutional identifiers
- appointment information
- copied clinical histories
- clinical documents
- screenshots from clinical systems
- exported patient records
- free-text information derived from a real patient
- any PHI or PII

The evaluation must stop immediately if real data is entered, pasted, displayed, generated, or suspected.

## 9. No-Persistence and No-Export Preflight

A future review must identify whether execution is expected to create:

- files
- caches
- logs
- histories
- temporary artifacts
- clipboard content
- screenshots
- print output
- exported reports
- browser storage
- database records
- telemetry records

The acceptable planned state remains:

- no persistence
- no export
- no patient-derived clipboard content
- no screenshots containing real data
- no print output
- no synchronization
- no hidden history retention

Phase G does not authorize runtime verification or remediation.

## 10. Safety Label Preflight

Before any future authorized evaluation, all visible evaluation instructions and outputs must be reviewed for explicit statements that the candidate is:

- synthetic-only
- local evaluation only
- not for clinical use
- not a diagnostic system
- not a treatment recommendation system
- not a triage system
- not connected to patient records
- not connected to appointment systems
- not connected to patient messaging
- not approved for production
- not go-live ready

No UI labeling is created or authorized by Phase G. No-UI Hold remains active.

## 11. Evaluation Scenario Plan

A future local evaluation may only consider already authorized synthetic scenarios and must not introduce clinical workflow behavior.

The scenario plan must define:

- scenario identifier
- synthetic source confirmation
- intended reviewer question
- expected non-clinical output shape
- prohibited interpretation
- stop condition
- evidence to retain outside the runtime, if separately authorized

The plan must not define scoring, ranking, treatment selection, urgency prioritization, protocol enforcement, patient communication, appointment action, or clinical writeback.

## 12. Evidence State Model

Every preflight item must use exactly one state:

- `PASS` — evidence exists and satisfies the documented criterion
- `FAIL` — evidence exists and does not satisfy the criterion
- `NOT TESTED` — no authorized verification has occurred
- `NOT APPLICABLE` — criterion is demonstrably outside the candidate boundary, with rationale
- `BLOCKED` — verification cannot proceed because a prerequisite or authorization is absent

Silence, assumption, inferred compliance, and planned future work do not count as `PASS`.

Current Phase G state for all runtime, machine, network, persistence, and execution checks: `NOT TESTED` or `BLOCKED`.

## 13. Mandatory Stop Conditions

A future evaluation must stop if any of the following occurs:

- real data, PHI, or PII is entered or displayed
- a network connection is required or attempted
- a listening port or server is created
- a database or external integration is accessed
- a file, log, cache, history, or export is created contrary to the approved plan
- the candidate exposes patient-facing functionality
- the candidate permits messaging, appointment mutation, clinical writeback, task creation, approval, or override
- the candidate produces autonomous clinical recommendations or instructions
- the fixed candidate version cannot be established
- evidence custody is incomplete
- an evaluator cannot explain an observed behavior
- any hold boundary is ambiguous

Stopping an evaluation does not authorize troubleshooting changes. Any remediation requires a separately scoped track.

## 14. Evidence Record Template

A future evidence record must include:

- record identifier
- date and time
- exact commit SHA
- machine identity
- custodian
- evaluator
- reviewer
- authorization reference
- synthetic scenario identifiers
- preflight item
- evidence description
- evidence location
- state
- rationale
- observed deviation
- stop decision
- follow-up decision

The template is defined only. No evidence repository, database, export, or persistence mechanism is created.

## 15. Entry Criteria for a Future Execution Review

A future local execution review may be proposed only after:

- an explicit execution-review authorization is recorded
- exact files and change types are named
- the fixed candidate commit is identified
- roles are assigned
- machine evidence is available
- custody rules are accepted
- synthetic-only instructions are approved
- no-network verification method is approved
- no-persistence and no-export verification method is approved
- stop conditions are accepted
- evidence handling is approved
- No-UI Hold is reaffirmed
- no-real-data and no-go-live boundaries are reaffirmed

Phase G does not satisfy these criteria by itself.

## 16. Phase G Decision

Phase G completes the documentation of the local evaluation preflight and evidence plan.

It does not authorize:

- candidate execution
- machine configuration
- packaging
- deployment
- UI
- real data
- PHI or PII
- clinical workflow
- persistence or export
- network operation
- integration
- production use
- go-live

## 17. Hold Record

Hold name: Program 1 Local Evaluation Preflight Hold after Phase G.

Hold state:

- documentation-only work complete
- preflight execution not started
- runtime verification not started
- local evaluation not started
- deployment not started
- UI track not started
- real-data track not started
- clinical workflow track not started
- No-UI Hold active
- synthetic-only boundary active
- no-network boundary active
- no-persistence and no-export boundary active
- no-go-live state active

Recommended next decision:

`Stop and hold after Local Production Readiness Track Phase G unless a narrowly scoped documentation-only Phase H is explicitly authorized.`

A possible Phase H may define a Local Synthetic Evaluation Authorization Packet without authorizing or performing execution.

## 18. Closure Confirmations

Confirmed:

- documentation-only
- no Python runtime code
- no new CLI command
- no execution
- no UI
- no server or API
- no network or database capability
- no integration
- no persistence or export
- no real-data, PHI, or PII
- no clinical workflow
- no patient messaging
- no appointment mutation
- no clinical writeback
- no clinical task creation
- no autonomous clinical behavior
- no approval or override capability
- no production deployment
- no go-live authorization
- No-UI Hold remains active
- no UI track was started
- no real-data track was started

Program 1 Local Production Readiness Track Phase G is closed as documentation-only governance work.
