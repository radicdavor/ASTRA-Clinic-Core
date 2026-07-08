# Program 1 Phase D11 - Findings Persistence Design

Status: persistence design

## Purpose

Define future persistence for findings without adding runtime persistence, endpoint, service, migration or UI.

## Proposed Entity

- entity name: `ClinicalFinding`
- proposed table name: `clinical_findings`

## Relationships

- belongs to one patient
- may reference one `ClinicalDocument`
- must carry a source reference even when the source is external or not modeled as a local document
- may later relate to open questions or physician decisions, but those are separate concepts

## Persistence Responsibilities

Future persistence should store:

- stable finding key
- patient relation
- source document/source reference
- lifecycle status
- category and display label
- review metadata
- source limitations
- schema version

## Boundaries

ClinicalFinding persistence must not include:

- Task link
- Outcome Evidence link
- patient message link
- automatic diagnosis/treatment fields
- appointment status mutation
- approval, clearance or override fields

## Physician Decision Boundary

A finding may support a later physician decision, but the finding row must not be the decision itself.

## No-Go

D11 does not approve:

- migration
- endpoint
- write service
- frontend UI
- production
- real patient data

