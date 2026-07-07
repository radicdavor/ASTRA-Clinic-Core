# Program 1 Phase B - Snapshot Next-Step Decision Brief

Status: next-step decision after Clinical Readiness Snapshot closure

## Decision

Do not proceed directly to Clinical Readiness enforcement.

Clinical Readiness Snapshot is now useful for demo/pilot preview history, but it is not a clinical approval layer.

ASTRA should not convert snapshot status into enforcement until production-risk issues are explicitly reviewed.

## Option A

`Program 1 Phase C0 - Clinical Readiness Enforcement Readiness Design`

Purpose:

- define whether ASTRA should ever block or gate clinical actions
- define human responsibility model
- define override semantics
- define audit and legal boundaries

Risk:

- too early if production risk hardening is incomplete
- may imply workflow power before governance is ready

## Option B

`Program 1 Phase B29 - Snapshot Production Risk Hardening`

Purpose:

- harden CI
- harden real-data guardrails
- review immutable snapshot policy
- improve permission UX
- review audit evidence
- review backup/restore implications
- review legal/compliance disclaimers

Risk:

- slower path to visible feature expansion
- mostly governance and quality work

## Recommendation

Recommended next task:

`Program 1 Phase B29 - Snapshot Production Risk Hardening`

Reason:

Before enforcement, ASTRA must harden:

- CI reliability
- real-data readiness guardrails
- immutable snapshot policy
- permission UX
- audit review workflow
- backup/restore implications
- legal/compliance disclaimers

## Explicit No-Go

Do not implement yet:

- clinical approval
- readiness clearance
- override workflow
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production/certification claims
- real AI/OCR
- real patient data approval

## Maintainer Decision Needed Later

Before any Phase C enforcement work, maintainers must decide:

- whether ASTRA may ever block clinical workflow
- who can override warnings
- what audit payload is required
- whether an Outcome Evidence object is needed
- whether Task engine is required
- whether legal/compliance review is mandatory before use
