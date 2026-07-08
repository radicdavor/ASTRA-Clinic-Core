# Program 1 Phase D77 - Open Questions From Findings Contract

Status: contract

## Purpose

Define how findings may suggest open questions without implementing runtime open-question creation.

This phase does not add an open-question endpoint, DB model, migration, write service, frontend UI, Task engine, Outcome Evidence or patient messaging.

## What Is an Open Question

An open question is unresolved, source-linked clinical context that may require human interpretation.

It may arise from:

- finding
- ClinicalDocument
- extraction candidate
- source inconsistency
- missing follow-up source

## What an Open Question Is Not

An open question is not:

- Task
- Outcome Evidence
- diagnosis
- recommendation by itself
- physician decision
- patient message
- appointment status change
- workflow enforcement signal
- approval, clearance or override

## Relationship to Finding

A finding may suggest that a clinical question exists.

The suggestion remains source-linked context and does not automatically create an official question.

## Relationship to ClinicalDocument

The source document must remain inspectable. The question must preserve source type, label, reference and limitations.

## Relationship to Extraction Candidate

An extraction candidate may suggest a question in a future design, but extraction does not make the question official or persisted.

## Relationship to Physician Decision and Recommendation

Open question may later require a physician decision or recommendation, but those are separate concepts.

The question itself is not the decision and not the recommendation.

## Why No Runtime Creation

Automatic creation would create pressure toward workflow action, false certainty and soft diagnosis. Runtime creation remains no-go until persistence, review, audit, retention and UI governance are explicitly approved.

## Demo/Pilot Boundary

D77 is demo/pilot contract work only. Production and real patient data remain no-go.

