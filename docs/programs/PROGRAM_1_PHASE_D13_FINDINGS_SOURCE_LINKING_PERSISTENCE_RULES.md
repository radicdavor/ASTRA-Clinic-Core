# Program 1 Phase D13 - Findings Source-Linking Persistence Rules

Status: source-linking persistence rules

## Core Rule

Every persisted finding must have a source reference.

A finding without a source reference is draft/invalid and must not become official patient knowledge.

## Source Forms

Supported future source forms:

- local `ClinicalDocument`
- external source reference
- physician-entered source context
- future reviewed extraction output

## Required Source Metadata

- source type
- source label
- source reference
- source date if known
- institution/author if known
- extraction method if applicable
- reviewed/unreviewed boundary
- limitations

## Immutability Expectations

Source reference fields should be treated as historical context.

If a source is corrected or superseded, future design should add a new finding version or update lifecycle metadata with audit. It must not rewrite historical clinical content silently.

## AI Boundary

AI may suggest structure, but cannot create official clinical truth.

AI-created candidate findings must remain awaiting review until human review policy permits a status transition.

## Runtime Boundary

D13 does not implement source-link persistence.

