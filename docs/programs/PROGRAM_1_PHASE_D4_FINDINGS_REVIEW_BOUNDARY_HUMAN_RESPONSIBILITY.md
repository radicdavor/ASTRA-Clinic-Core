# Program 1 Phase D4 - Findings Review Boundary and Human Responsibility

Status: review boundary

## Purpose

This document defines who may review findings and what review means.

## Who Can Review

Future policy should distinguish:

- physician review for clinical interpretation and decisions
- authorized human review for administrative/source-quality checks only where explicitly allowed
- nurse review only for preparation or context support, not final clinical decision unless later policy explicitly permits a narrow case
- reception review limited to identity, document availability and administrative context

## AI/API Key Limits

AI agents and API keys may not be final reviewers.

They may propose structure or retrieve source context in future phases, but they must not create official clinical truth, diagnosis, clearance, override, patient instruction or treatment plan.

## What Review Means

Review means a human looked at the finding and its source context.

Review does not automatically mean:

- diagnosis
- patient notification
- task creation
- outcome evidence
- treatment plan
- readiness clearance
- approval
- override

## Source Context Requirement

Finding review requires source context.

The reviewer must be able to inspect the source document/reference, extraction limitations and whether the source was reviewed.

## Future Audit Needs

Future review events should capture:

- actor
- role
- timestamp
- finding key/id
- source references
- review note/reason
- whether a separate physician decision was created

Audit must not imply clinical outcome evidence.

## Runtime Boundary

D4 does not implement review endpoint, review service, permission seed, UI action or audit event.

