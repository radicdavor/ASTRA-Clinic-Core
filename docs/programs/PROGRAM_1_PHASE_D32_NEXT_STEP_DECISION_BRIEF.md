# Program 1 Phase D32 - Next-Step Decision Brief

Status: decision brief

## Decision

Do not add a runtime findings endpoint yet.

The DB foundation is now present, but the read boundary, response shape, permission model and safety wording must be defined before exposing findings through API or UI.

## Option A

`Program 1 Phase D33 - Findings Read-Only API Contract`

Documentation-only. Defines future read routes and response shape without adding endpoint runtime.

## Option B

`Program 1 Phase D33 - Findings Source Document Binding Contract`

Documentation-only. Focuses on source document binding before API design.

## Option C

`Program 1 Phase D33 - ClinicalDocument Finding Extraction Contract`

Documentation-only. Defines extraction contract without AI/OCR runtime.

## Recommendation

Choose `Program 1 Phase D33 - Findings Read-Only API Contract`.

Reason: persistence now exists, so the safest next step is to define read-only API boundaries before any runtime endpoint, service or UI is introduced.

