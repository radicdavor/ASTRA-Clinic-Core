# Program 2 — Phase F: Timeline and AI Summary Layer

## Status

Phase F implements a journey timeline projection and a deterministic, source-linked local summary stub. No live AI provider was added.

## Timeline

`GET /api/patient-journeys/{id}/timeline` projects existing source-of-truth entities rather than copying them into a new timeline table. It currently includes appointment, journey workflow events, source documents, communication attempts, laboratory orders and invoices. Every item contains date, type, title, optional summary, source URL, provenance, review state and journey ID.

Document timeline items link directly to the original source endpoint and include the stored checksum in provenance. The timeline is a read projection; source entities retain ownership of their data.

## Source-linked summary

`JourneyAISummary` stores provider/model metadata, generation time, explicit review status, structured sections, source references and limitations. `JourneyAISummaryFact` makes each proposed statement independently reviewable and links it to a source document where one exists.

The local provider `local-deterministic-source-index` does not infer diagnoses, treatment or readiness. It indexes available documents, carries forward only a physician-reviewed document summary when one exists, and identifies unresolved mandatory document requests. If no source exists, it explicitly records missing information; absence is never presented as a normal finding.

All generated summaries are labeled as AI-generated and start in `pending_review`. Individual facts require an authorized user to accept or reject them. The summary becomes `reviewed` only when no fact remains pending. Acceptance does not overwrite the source document or directly create a formal clinical note.

## Safety boundary

- source documents remain the source of truth
- every document-derived fact contains a source link
- fact and missing-information types are distinct
- limitations explain that blank sections are not normal findings
- no diagnosis, treatment, clearance, prioritization or autonomous workflow transition occurs
- generation and every fact review are audited

## Deferred

- live external AI provider
- richer structured extraction from OCR text
- cross-journey longitudinal clinical synthesis
- Phase I UI for side-by-side source review and selective fact use
