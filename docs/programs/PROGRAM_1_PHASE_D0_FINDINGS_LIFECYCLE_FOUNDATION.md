# Program 1 Phase D0 - Findings Lifecycle Foundation

Status: foundation/design

## Why Phase D Exists

Phase D opens the Findings Lifecycle foundation after Phase C closed the acknowledgment write endpoint as No-Go.

The core gap is that ASTRA can show source-linked knowledge and advisory signals, but it does not yet have a governed lifecycle for findings that may need review, follow-up, decision or temporary closure.

## What Is A Finding

A finding is a source-linked clinical knowledge unit that may require human review, status tracking and lifecycle governance.

Examples:

- document-derived abnormality
- source-linked clinical statement
- unresolved question from pathology, lab, endoscopy, radiology or external report
- readiness-relevant warning derived from reviewed source context

## What A Finding Is Not

A finding is not:

- automatic diagnosis
- automatic treatment plan
- Task
- Outcome Evidence
- patient message
- appointment status
- readiness clearance
- override
- final physician decision unless separately confirmed

## Relationship To Patient Clinical Knowledge Layer

Findings belong under the Patient Clinical Knowledge direction.

They are a way to represent source-linked clinical knowledge and unresolved items. They do not replace the source documents or make the Patient Clinical Summary a source of truth.

## Relationship To ClinicalDocument

`ClinicalDocument` remains the source object.

A finding may reference one or more source documents, but the source document itself is not a finding.

## Relationship To Clinical Summary

Patient Clinical Summary is a view over reviewed knowledge.

It may display findings later, but it must not become the authority for creating official findings without source context.

## Relationship To Open Questions

A finding may open an open question.

An open question is not a task, diagnosis, treatment plan or patient instruction.

## Relationship To Physician Decision

A physician decision is separate from a finding.

Reviewing or displaying a finding does not automatically create a diagnosis, treatment plan, clearance or patient-facing instruction.

## Relationship To Acknowledgment And Readiness

The acknowledgment/readiness stack remains advisory and read-only where already implemented.

Findings may later provide the lifecycle context that makes review actions safer. D0 does not add such actions.

## Why D0 Does Not Add Runtime Engine

D0 is documentation-first because unsafe runtime behavior would be easy to overinterpret.

Before adding endpoints or persistence, ASTRA must define:

- finding boundaries
- safe status taxonomy
- source evidence rules
- human responsibility
- open question relationship
- recommendation/decision boundary

## Demo/Pilot Assumption

D0 remains demo/pilot only.

## No-Go

D0 does not approve:

- runtime findings endpoint
- findings DB model or migration
- Task engine
- Outcome Evidence
- patient messaging
- automatic diagnosis
- automatic treatment plan
- appointment status mutation
- workflow enforcement
- production use
- real patient data

